#!/usr/bin/env python3
"""
Visualizes what's inside the patient-clustering K-Means model and the RL
Q-table, and what a retrain operation actually changes.

Safety model:
  - The real .pkl files under data/models/ are only ever opened for reading.
  - All "retrain" operations run against temp copies (deleted on exit).
  - retrain_from_feedback() normally calls db.commit() on treatment_feedbacks
    rows (flips is_retrained=True). That step is reimplemented here as a
    read-only simulation -- no ORM writes, no commit -- so this script never
    changes production DB state either.
  - Both claims are verified at the end of the run (file mtime/size and
    is_retrained counts are compared before vs after).

Usage:
  python3 backend/scripts/model_report.py [--output PATH] [--open]
"""
import argparse
import copy
import json
import os
import shutil
import sys
import tempfile
import webbrowser
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import func

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from models import SessionLocal, Patient, MedicalRecord, TreatmentFeedback, ClinicalOutcomeScore  # noqa: E402
import services.patient_clustering_service as pcs_module  # noqa: E402
import services.rl_service as rl_module  # noqa: E402

REAL_CLUSTER_PATH = os.path.join(BACKEND_DIR, "data", "models", "patient_cluster_model.pkl")
REAL_QTABLE_PATH = os.path.join(BACKEND_DIR, "data", "models", "rl_q_table.pkl")

EXAMPLE_PATIENT = {
    "age": 45, "gender": "Female", "prakriti": "Pitta", "vikriti": "Pitta",
    "disease": "Abdominal distension disorder (TM2)", "severity": 5,
}
LEARNING_RATE = rl_module.RLRecommendationService().learning_rate  # 0.1, read from the real service


# ---------------------------------------------------------------------------
# Read-only DB access
# ---------------------------------------------------------------------------

def fetch_training_frame(db) -> pd.DataFrame:
    """Same shape retrain_clusters() builds internally -- duplicated here
    (read-only query) so we can inject synthetic rows before fitting."""
    records = db.query(MedicalRecord, Patient).join(Patient, MedicalRecord.patient_id == Patient.id).all()
    rows = []
    for r, p in records:
        try:
            severity_val = int(r.severity) if r.severity else 5
        except ValueError:
            severity_val = 5
        try:
            age_val = int(p.age) if p.age else 30
        except ValueError:
            age_val = 30
        rows.append({
            "age": age_val, "gender": p.gender or "Unknown",
            "prakriti": r.prakriti or "Unknown", "vikriti": r.vikriti or "Unknown",
            "disease": r.diagnosis or "Unknown", "severity_numeric": severity_val,
        })
    return pd.DataFrame(rows)


def db_snapshot(db) -> dict:
    counts = {
        "patients": db.query(Patient).count(),
        "medical_records": db.query(MedicalRecord).count(),
        "treatment_feedbacks": db.query(TreatmentFeedback).count(),
        "clinical_outcome_scores": db.query(ClinicalOutcomeScore).count(),
    }
    rating_rows = (
        db.query(TreatmentFeedback.doctor_rating, func.count(TreatmentFeedback.id))
        .group_by(TreatmentFeedback.doctor_rating).all()
    )
    counts["ratings"] = {(r or "none"): n for r, n in rating_rows}
    counts["is_retrained_true"] = db.query(TreatmentFeedback).filter(TreatmentFeedback.is_retrained == True).count()  # noqa: E712
    return counts


def feedback_cluster_id_gap(db) -> dict:
    """How many feedback rows can actually reach the Q-table. Read-only."""
    rows = db.query(TreatmentFeedback.ml_context).all()
    total = len(rows)
    with_cluster_id = 0
    for (ctx_str,) in rows:
        try:
            ctx = json.loads(ctx_str) if ctx_str else {}
        except (json.JSONDecodeError, TypeError):
            ctx = {}
        if ctx.get("cluster_id") is not None:
            with_cluster_id += 1
    return {"total": total, "with_cluster_id": with_cluster_id, "without_cluster_id": total - with_cluster_id}


# ---------------------------------------------------------------------------
# Current-model snapshot (raw read, no service instantiation needed)
# ---------------------------------------------------------------------------

def characterize_clusters(pipeline, df: pd.DataFrame) -> list:
    labels = pipeline.predict(df)
    out = []
    for c in sorted(set(labels)):
        sub = df[labels == c]

        def mode(col):
            vc = sub[col].value_counts()
            return vc.index[0] if len(vc) else "-"

        out.append({
            "cluster": int(c), "count": int(len(sub)), "pct": round(100 * len(sub) / len(df), 1),
            "dominant_disease": mode("disease"), "dominant_prakriti": mode("prakriti"),
            "dominant_vikriti": mode("vikriti"), "dominant_gender": mode("gender"),
            "avg_age": round(sub["age"].mean(), 1), "avg_severity": round(sub["severity_numeric"].mean(), 1),
        })
    return out


def qtable_stats(q_table: dict) -> dict:
    pairs = [(s, a, v) for s, actions in q_table.items() for a, v in actions.items()]
    nonzero = [p for p in pairs if p[2] != 0]
    top = sorted(pairs, key=lambda p: -abs(p[2]))[:15]
    return {
        "n_states": len(q_table), "n_pairs": len(pairs), "n_nonzero": len(nonzero),
        "n_empty_states": sum(1 for a in q_table.values() if not a), "top_pairs": top,
    }


# ---------------------------------------------------------------------------
# Sandboxed "operation" demos
# ---------------------------------------------------------------------------

def _recompute_inertia(pipeline, df: pd.DataFrame) -> float:
    """sklearn's .inertia_ is fixed at fit time, so it only reflects whatever
    data the model was fit on *then* -- not necessarily today's data. This
    recomputes actual sum-of-squared-distances for a given model against a
    given dataframe, so before/after are compared on the identical rows."""
    pre = pipeline.named_steps["preprocessor"]
    X = pre.transform(df)
    if hasattr(X, "toarray"):
        X = X.toarray()
    km = pipeline.named_steps["classifier"]
    labels = km.predict(X)
    return float(((X - km.cluster_centers_[labels]) ** 2).sum())


def clustering_retrain_demo(df_real: pd.DataFrame, real_pipeline, sandbox_dir: str) -> dict:
    """'Before' = the real fitted model (already loaded), evaluated against
    ALL of today's real data. 'After' = refit on real data + injected
    synthetic patients, using the identical pipeline shape, saved only to a
    sandbox path, also evaluated on the same real rows for a fair diff."""
    before_labels = real_pipeline.predict(df_real)
    before_sizes = pd.Series(before_labels).value_counts().sort_index().to_dict()
    before_inertia = _recompute_inertia(real_pipeline, df_real)
    before_example = int(real_pipeline.predict(pd.DataFrame([{
        "age": EXAMPLE_PATIENT["age"], "gender": EXAMPLE_PATIENT["gender"],
        "prakriti": EXAMPLE_PATIENT["prakriti"], "vikriti": EXAMPLE_PATIENT["vikriti"],
        "disease": EXAMPLE_PATIENT["disease"], "severity_numeric": EXAMPLE_PATIENT["severity"],
    }]))[0])

    real_disease_categories = set(
        real_pipeline.named_steps["preprocessor"].transformers_[1][1].named_steps["onehot"].categories_[3]
    )
    n_unseen_disease_rows = int((~df_real["disease"].isin(real_disease_categories)).sum())

    synthetic = [{
        "age": 25 + (i * 3) % 50, "gender": "Female" if i % 2 == 0 else "Male",
        "prakriti": "Pitta", "vikriti": "Pitta",
        "disease": "Abdominal distension disorder (TM2)", "severity_numeric": 3 + (i % 6),
    } for i in range(150)]
    df_augmented = pd.concat([df_real, pd.DataFrame(synthetic)], ignore_index=True)

    sandbox_path = os.path.join(sandbox_dir, "after_cluster_model.pkl")
    pcs_module.MODEL_PATH = sandbox_path  # redirect _load_model/_save_model; file doesn't exist yet
    after_service = pcs_module.PatientClusteringService()  # fresh, unfit pipeline (identical shape)
    after_service.pipeline.fit(df_augmented)
    after_service.is_fitted = True
    after_service._save_model()  # writes only to sandbox_path

    after_labels_on_real = after_service.pipeline.predict(df_real)
    after_sizes = pd.Series(after_labels_on_real).value_counts().sort_index().to_dict()
    after_inertia = _recompute_inertia(after_service.pipeline, df_real)  # same rows as before_inertia
    after_example = after_service.get_cluster({
        "age": EXAMPLE_PATIENT["age"], "gender": EXAMPLE_PATIENT["gender"],
        "prakriti": EXAMPLE_PATIENT["prakriti"], "vikriti": EXAMPLE_PATIENT["vikriti"],
        "disease": EXAMPLE_PATIENT["disease"], "severity": EXAMPLE_PATIENT["severity"],
    })

    return {
        "before_sizes": before_sizes, "after_sizes": after_sizes,
        "before_inertia": before_inertia, "after_inertia": after_inertia,
        "n_unseen_disease_rows": n_unseen_disease_rows, "n_disease_categories_before": len(real_disease_categories),
        "n_synthetic": len(synthetic), "before_example_cluster": before_example,
        "after_example_cluster": after_example,
    }


def rl_real_data_gap_demo(db, q_table_copy: dict) -> dict:
    """Read-only replay of retrain_from_feedback()'s decision logic against
    the real feedback rows -- no ORM mutation, no commit."""
    feedbacks = db.query(TreatmentFeedback).filter(TreatmentFeedback.is_retrained == False).all()  # noqa: E712
    skipped_no_context, applied, zero_reward = 0, 0, 0
    q_before = copy.deepcopy(q_table_copy)
    for fb in feedbacks:
        try:
            ctx = json.loads(fb.ml_context) if fb.ml_context else {}
        except (json.JSONDecodeError, TypeError):
            ctx = {}
        cluster_id, disease = ctx.get("cluster_id"), ctx.get("disease")
        if cluster_id is None or not disease:
            skipped_no_context += 1
            continue
        rating = fb.doctor_rating
        reward = 1.0 if rating == "positive" else (-1.0 if rating == "negative" else 0.0)
        if reward == 0.0:
            zero_reward += 1
            continue
        state = rl_module.rl_service._get_state_key(cluster_id, disease)
        try:
            ai_plan = json.loads(fb.ai_plan) if fb.ai_plan else {}
        except (json.JSONDecodeError, TypeError):
            ai_plan = {}
        q_table_copy.setdefault(state, {})
        for h in ai_plan.get("herbs", []):
            name = (h.get("name", "") if isinstance(h, dict) else str(h)).strip().lower()
            if not name:
                continue
            old_q = q_table_copy[state].get(name, 0.0)
            q_table_copy[state][name] = old_q + LEARNING_RATE * (reward - old_q)
            applied += 1
    return {
        "total_unprocessed": len(feedbacks), "skipped_no_context": skipped_no_context,
        "zero_reward": zero_reward, "applied": applied,
        "q_table_unchanged": q_before == q_table_copy,
    }


def rl_synthetic_walkthrough() -> dict:
    """Fabricated events -- not real patient data -- to show the update rule
    Q(s,a) += lr * (reward - Q(s,a)) mechanics step by step."""
    events = [
        ("8_abdominal distension disorder (tm2)", "ashwagandha", 1.0),
        ("8_abdominal distension disorder (tm2)", "ashwagandha", 1.0),
        ("8_abdominal distension disorder (tm2)", "ashwagandha", -1.0),
        ("8_abdominal distension disorder (tm2)", "ashwagandha", 1.0),
        ("8_abdominal distension disorder (tm2)", "ashwagandha", 1.0),
        ("8_abdominal distension disorder (tm2)", "yoga:pawanmuktasana", 1.0),
        ("8_abdominal distension disorder (tm2)", "yoga:pawanmuktasana", 1.0),
        ("3_acidity (amlapitta)", "triphala", -1.0),
        ("3_acidity (amlapitta)", "triphala", -1.0),
        ("3_acidity (amlapitta)", "triphala", -1.0),
        ("3_acidity (amlapitta)", "triphala", 1.0),
    ]
    q = {}
    ledger, trajectories = [], {}
    for i, (state, action, reward) in enumerate(events, start=1):
        q.setdefault(state, {})
        old_q = q[state].get(action, 0.0)
        new_q = old_q + LEARNING_RATE * (reward - old_q)
        q[state][action] = new_q
        ledger.append({"step": i, "state": state, "action": action, "reward": reward, "old_q": old_q, "new_q": new_q})
        key = f"{state} · {action}"
        trajectories.setdefault(key, []).append((len(trajectories.get(key, [])) + 1, new_q))
    return {"ledger": ledger, "trajectories": trajectories, "final_q": q}


# ---------------------------------------------------------------------------
# Tiny inline-SVG chart builders (dataviz palette, hover tooltip via data-tip)
# ---------------------------------------------------------------------------

def _fmt(v):
    return f"{v:.3f}" if isinstance(v, float) else str(v)


def bar_chart_svg(categories, series, colors, width=700, height=280, value_fmt=lambda v: f"{v:,}"):
    """series: list of (label, [values aligned to categories])."""
    pad_l, pad_r, pad_t, pad_b = 44, 16, 16, 46
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b
    n = len(categories)
    max_v = max((max(vals) for _, vals in series), default=1) or 1
    group_w = plot_w / n
    n_series = len(series)
    bar_w = (group_w * 0.62) / n_series
    gap = group_w * 0.38

    def y(v):
        return pad_t + plot_h - (v / max_v) * plot_h

    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart-svg" role="img">']
    for gl in np.linspace(0, max_v, 4):
        yy = y(gl)
        parts.append(f'<line x1="{pad_l}" y1="{yy:.1f}" x2="{width-pad_r}" y2="{yy:.1f}" class="gridline" />')
        parts.append(f'<text x="{pad_l-8}" y="{yy+4:.1f}" class="axis-label" text-anchor="end">{value_fmt(gl)}</text>')
    for i, cat in enumerate(categories):
        gx = pad_l + i * group_w
        for si, (label, vals) in enumerate(series):
            v = vals[i]
            bx = gx + gap / 2 + si * bar_w
            bh = plot_h - (y(v) - pad_t)
            parts.append(
                f'<rect x="{bx:.1f}" y="{y(v):.1f}" width="{bar_w-3:.1f}" height="{max(bh,0):.1f}" '
                f'rx="3" fill="{colors[si % len(colors)]}" class="bar" '
                f'data-tip="{label}: {cat}&#10;{value_fmt(v)}" />'
            )
        parts.append(f'<text x="{gx+group_w/2:.1f}" y="{height-pad_b+18}" class="axis-label" text-anchor="middle">{cat}</text>')
    parts.append(f'<line x1="{pad_l}" y1="{pad_t+plot_h}" x2="{width-pad_r}" y2="{pad_t+plot_h}" class="baseline" />')
    parts.append("</svg>")
    return "".join(parts)


def line_chart_svg(trajectories: dict, colors, width=700, height=280):
    pad_l, pad_r, pad_t, pad_b = 44, 16, 16, 34
    plot_w, plot_h = width - pad_l - pad_r, height - pad_t - pad_b
    max_step = max((len(pts) for pts in trajectories.values()), default=1)
    lo, hi = -1.05, 1.05

    def x(i):
        return pad_l + (i - 1) / max(max_step - 1, 1) * plot_w

    def y(v):
        return pad_t + plot_h - (v - lo) / (hi - lo) * plot_h

    parts = [f'<svg viewBox="0 0 {width} {height}" class="chart-svg" role="img">']
    for gl in [-1, -0.5, 0, 0.5, 1]:
        yy = y(gl)
        parts.append(f'<line x1="{pad_l}" y1="{yy:.1f}" x2="{width-pad_r}" y2="{yy:.1f}" class="gridline" />')
        parts.append(f'<text x="{pad_l-8}" y="{yy+4:.1f}" class="axis-label" text-anchor="end">{gl:+.1f}</text>')
    parts.append(f'<line x1="{pad_l}" y1="{y(0):.1f}" x2="{width-pad_r}" y2="{y(0):.1f}" class="baseline" />')
    for si, (label, pts) in enumerate(trajectories.items()):
        color = colors[si % len(colors)]
        path = " ".join(f'{"M" if i==0 else "L"}{x(p[0]):.1f},{y(p[1]):.1f}' for i, p in enumerate(pts))
        parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" />')
        for i, p in enumerate(pts):
            parts.append(
                f'<circle cx="{x(p[0]):.1f}" cy="{y(p[1]):.1f}" r="4" fill="{color}" '
                f'data-tip="{label}&#10;update {p[0]}: Q={p[1]:+.3f}" />'
            )
    parts.append("</svg>")
    return "".join(parts)


# ---------------------------------------------------------------------------
# HTML assembly
# ---------------------------------------------------------------------------

CSS = """
:root {
  --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e; --ink-muted:#898781;
  --line:#e1e0d9; --accent:#2a78d6; --accent-2:#1baf7a; --good:#0ca30c; --warning:#c98500; --critical:#d03b3b;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root { --page:#0d0d0d; --surface:#1a1a19; --ink:#ffffff; --ink-2:#c3c2b7; --ink-muted:#898781;
    --line:#2c2c2a; --accent:#3987e5; --accent-2:#199e70; --good:#0ca30c; --warning:#c98500; --critical:#e66767; }
}
:root[data-theme="dark"] { --page:#0d0d0d; --surface:#1a1a19; --ink:#ffffff; --ink-2:#c3c2b7; --ink-muted:#898781;
  --line:#2c2c2a; --accent:#3987e5; --accent-2:#199e70; --good:#0ca30c; --warning:#c98500; --critical:#e66767; }
:root[data-theme="light"] { --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e; --ink-muted:#898781;
  --line:#e1e0d9; --accent:#2a78d6; --accent-2:#1baf7a; --good:#0ca30c; --warning:#c98500; --critical:#d03b3b; }

* { box-sizing:border-box; }
body { margin:0; background:var(--page); color:var(--ink);
  font-family: system-ui,-apple-system,"Segoe UI",sans-serif; }
.wrap { max-width:920px; margin:0 auto; padding:40px 20px 80px; display:flex; flex-direction:column; gap:40px; }
header.top { display:flex; flex-direction:column; gap:6px; border-bottom:1px solid var(--line); padding-bottom:24px; }
h1 { font-size:26px; font-weight:700; margin:0; text-wrap:balance; letter-spacing:-0.01em; }
.meta { color:var(--ink-muted); font-size:13px; }
.safety-note { font-size:13px; color:var(--ink-2); background:var(--surface); border:1px solid var(--line);
  border-radius:8px; padding:10px 14px; margin-top:8px; }
section { display:flex; flex-direction:column; gap:16px; }
h2 { font-size:19px; font-weight:650; margin:0; }
h2 .eyebrow { display:block; font-size:11px; font-weight:600; letter-spacing:0.07em; text-transform:uppercase;
  color:var(--ink-muted); margin-bottom:4px; }
p.lead { color:var(--ink-2); font-size:14.5px; line-height:1.6; max-width:70ch; margin:0; }
.card { background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:20px 24px; }
.stat-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:1px; background:var(--line);
  border:1px solid var(--line); border-radius:10px; overflow:hidden; }
.stat { background:var(--surface); padding:16px 18px; display:flex; flex-direction:column; gap:4px; }
.stat .label { font-size:11px; text-transform:uppercase; letter-spacing:0.06em; color:var(--ink-muted); }
.stat .value { font-size:26px; font-weight:700; font-variant-numeric:tabular-nums; }
.stat .sub { font-size:12px; color:var(--ink-2); }
.callout { border-radius:10px; padding:14px 18px; display:flex; gap:12px; align-items:flex-start; border:1px solid; }
.callout.critical { border-color:color-mix(in srgb, var(--critical) 40%, transparent); background:color-mix(in srgb, var(--critical) 8%, var(--surface)); }
.callout.good { border-color:color-mix(in srgb, var(--good) 40%, transparent); background:color-mix(in srgb, var(--good) 8%, var(--surface)); }
.callout .icon { font-weight:700; font-size:15px; flex:none; width:20px; text-align:center; }
.callout.critical .icon { color:var(--critical); }
.callout.good .icon { color:var(--good); }
.callout .body { font-size:14px; line-height:1.55; color:var(--ink-2); }
.callout .body b { color:var(--ink); }
table { border-collapse:collapse; width:100%; font-size:13px; }
table.data-table { min-width:640px; }
.table-scroll { overflow-x:auto; border:1px solid var(--line); border-radius:8px; }
th, td { text-align:left; padding:8px 12px; border-bottom:1px solid var(--line); white-space:nowrap; }
th { color:var(--ink-muted); font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:0.04em; }
td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
tr:last-child td { border-bottom:none; }
.mono { font-family:var(--mono); font-size:12.5px; }
.chart-card { padding:18px 20px 12px; }
.chart-title { font-size:13px; font-weight:600; color:var(--ink-2); margin-bottom:6px; }
.legend { display:flex; gap:16px; font-size:12px; color:var(--ink-2); margin-bottom:8px; flex-wrap:wrap; }
.legend .dot { display:inline-block; width:9px; height:9px; border-radius:2px; margin-right:6px; vertical-align:middle; }
svg.chart-svg { width:100%; height:auto; overflow:visible; }
.gridline { stroke:var(--line); stroke-width:1; }
.baseline { stroke:var(--ink-muted); stroke-width:1; }
.axis-label { fill:var(--ink-muted); font-size:10.5px; font-family:system-ui,sans-serif; }
.bar { cursor:pointer; transition:opacity .12s; }
.bar:hover { opacity:0.75; }
circle { cursor:pointer; }
circle:hover { r:6; }
#tooltip { position:fixed; pointer-events:none; background:var(--ink); color:var(--page); font-size:12px;
  padding:6px 10px; border-radius:6px; white-space:pre-line; line-height:1.4; opacity:0; transform:translate(-50%,-115%);
  transition:opacity .08s; z-index:50; max-width:240px; }
#tooltip.show { opacity:0.96; }
footer.foot { border-top:1px solid var(--line); padding-top:20px; font-size:12.5px; color:var(--ink-muted); }
"""

JS = """
const tip = document.getElementById('tooltip');
document.querySelectorAll('[data-tip]').forEach(el => {
  el.addEventListener('mousemove', e => {
    tip.textContent = el.getAttribute('data-tip');
    tip.style.left = e.clientX + 'px';
    tip.style.top = e.clientY + 'px';
    tip.classList.add('show');
  });
  el.addEventListener('mouseleave', () => tip.classList.remove('show'));
});
"""


def stat_tile(label, value, sub=""):
    return f'<div class="stat"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>'


def callout(tone, icon, html_body):
    return f'<div class="callout {tone}"><div class="icon">{icon}</div><div class="body">{html_body}</div></div>'


def data_table(headers, rows, numeric_cols=()):
    th = "".join(f'<th class="{"num" if h in numeric_cols else ""}">{h}</th>' for h in headers)
    body = ""
    for row in rows:
        tds = "".join(f'<td class="{"num" if h in numeric_cols else ""}">{row[h]}</td>' for h in headers)
        body += f"<tr>{tds}</tr>"
    return f'<div class="table-scroll"><table class="data-table"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def render_html(ctx) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    db_s = ctx["db_snapshot"]
    gap = ctx["gap"]
    cstats = ctx["cluster_stats"]
    qstats = ctx["qtable_stats"]
    cdemo = ctx["cluster_demo"]
    rlgap = ctx["rl_gap_demo"]
    walk = ctx["rl_walkthrough"]

    cluster_table = data_table(
        ["Cluster", "Patients", "% of total", "Dominant disease", "Prakriti", "Vikriti", "Gender", "Avg age", "Avg severity"],
        [{"Cluster": c["cluster"], "Patients": f'{c["count"]:,}', "% of total": f'{c["pct"]}%',
          "Dominant disease": c["dominant_disease"], "Prakriti": c["dominant_prakriti"], "Vikriti": c["dominant_vikriti"],
          "Gender": c["dominant_gender"], "Avg age": c["avg_age"], "Avg severity": c["avg_severity"]} for c in cstats],
        numeric_cols={"Patients", "% of total", "Avg age", "Avg severity"},
    )

    cluster_bar = bar_chart_svg(
        [str(c["cluster"]) for c in cstats], [("Patients", [c["count"] for c in cstats])],
        colors=["var(--accent)"],
    )

    top_q_table = data_table(
        ["State (cluster_disease)", "Action", "Q-value"],
        [{"State (cluster_disease)": f'<span class="mono">{s}</span>', "Action": f'<span class="mono">{a}</span>', "Q-value": f"{v:+.3f}"}
         for s, a, v in qstats["top_pairs"]] or [{"State (cluster_disease)": "-", "Action": "no non-zero entries yet", "Q-value": "-"}],
        numeric_cols={"Q-value"},
    )

    before_after_cats = sorted(set(cdemo["before_sizes"]) | set(cdemo["after_sizes"]))
    before_after_bar = bar_chart_svg(
        [str(c) for c in before_after_cats],
        [("Before", [cdemo["before_sizes"].get(c, 0) for c in before_after_cats]),
         ("After (+150 synthetic)", [cdemo["after_sizes"].get(c, 0) for c in before_after_cats])],
        colors=["var(--accent)", "var(--accent-2)"],
    )

    ledger_table = data_table(
        ["Step", "State", "Action", "Reward", "Old Q", "New Q"],
        [{"Step": r["step"], "State": f'<span class="mono">{r["state"]}</span>', "Action": f'<span class="mono">{r["action"]}</span>',
          "Reward": f'{r["reward"]:+.1f}', "Old Q": f'{r["old_q"]:+.3f}', "New Q": f'{r["new_q"]:+.3f}'} for r in walk["ledger"]],
        numeric_cols={"Reward", "Old Q", "New Q"},
    )
    traj_colors = ["var(--accent)", "var(--accent-2)", "#eda100", "#e34948"]
    traj_legend = "".join(
        f'<span><span class="dot" style="background:{traj_colors[i % len(traj_colors)]}"></span>{label}</span>'
        for i, label in enumerate(walk["trajectories"])
    )
    traj_chart = line_chart_svg(walk["trajectories"], traj_colors)

    cluster_shift_note = (
        f'unchanged (still <b>Cluster {cdemo["before_example_cluster"]}</b>)'
        if cdemo["before_example_cluster"] == cdemo["after_example_cluster"]
        else f'shifted from <b>Cluster {cdemo["before_example_cluster"]}</b> to <b>Cluster {cdemo["after_example_cluster"]}</b>'
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Model Report — Clustering &amp; RL</title>
<style>{CSS}</style>
</head>
<body>
<div id="tooltip"></div>
<div class="wrap">

  <header class="top">
    <h1>What's in the models, and what changes when they retrain</h1>
    <div class="meta">Generated {now} · patient_cluster_model.pkl &amp; rl_q_table.pkl</div>
    <div class="safety-note">Read-only against production: model files are only ever copied before any refit, and the
    one production step that writes to the database (marking feedback rows <span class="mono">is_retrained</span>)
    was replayed here as a simulation with no commit. Verified counts are in the footer.</div>
  </header>

  <section>
    <h2><span class="eyebrow">Section 1</span>Current production state</h2>
    <p class="lead">Everything the two model files and the underlying tables hold right now, before any operation runs.</p>
    <div class="stat-row">
      {stat_tile("Patients", f'{db_s["patients"]:,}')}
      {stat_tile("Visits (medical records)", f'{db_s["medical_records"]:,}', "trains the K-Means clusterer")}
      {stat_tile("Doctor feedback rows", f'{db_s["treatment_feedbacks"]:,}',
                  f'{db_s["ratings"].get("positive",0):,} accurate · {db_s["ratings"].get("negative",0):,} needs changes')}
      {stat_tile("Clinical outcome scores", f'{db_s["clinical_outcome_scores"]:,}', "objective reward source")}
      {stat_tile("K-Means clusters", len(cstats), "n_clusters hyperparameter")}
      {stat_tile("Q-table states seen", f'{qstats["n_states"]:,}', f'{qstats["n_empty_states"]:,} with zero learned actions')}
    </div>
    <div class="card">
      <div class="chart-title">Patients per cluster (current fitted model, predicted on real historical data)</div>
      {cluster_bar}
    </div>
    {cluster_table}
  </section>

  <section>
    <h2><span class="eyebrow">Section 2</span>The RL Q-table, as it stands</h2>
    <p class="lead">Non-zero (state, action) pairs learned so far — the only ones an epsilon-greedy exploit step can return.</p>
    {top_q_table}
    {callout("critical", "!", f'''<b>{gap["without_cluster_id"]:,} of {gap["total"]:,}</b> doctor-feedback rows have no
    <span class="mono">cluster_id</span> in their stored ml_context. <span class="mono">retrain_from_feedback()</span> requires it
    ({os.path.relpath(os.path.join(BACKEND_DIR,"services","rl_service.py"), BACKEND_DIR)}) — every one of those rows gets marked
    processed and skipped without touching a single Q-value. That's why the table above is still almost entirely empty
    despite {db_s["ratings"].get("positive",0)+db_s["ratings"].get("negative",0):,} real doctor ratings on file.''')}
  </section>

  <section>
    <h2><span class="eyebrow">Section 3 · Operation</span>Clustering retrain — before vs after</h2>
    <p class="lead">Simulated in a sandbox: refit the same pipeline (StandardScaler + OneHotEncoder → KMeans, k=10, random_state=42) on the
    real {'{:,}'.format(int(sum(cdemo["before_sizes"].values())))} historical visits plus {cdemo["n_synthetic"]} synthetic new patients
    (same profile as the example we've been tracing: {EXAMPLE_PATIENT["disease"]}, Pitta/Pitta). Nothing here is written to the real model file.
    Both inertia numbers below are recomputed on the identical {'{:,}'.format(int(sum(cdemo["before_sizes"].values())))} real rows, so they're
    a fair before/after — not sklearn's stored <span class="mono">.inertia_</span>, which reflects whatever data the model happened to be fit
    on originally and isn't comparable across fits.</p>
    <div class="stat-row">
      {stat_tile("Inertia before", f'{cdemo["before_inertia"]:,.0f}', "current live model, scored on today's real data")}
      {stat_tile("Inertia after", f'{cdemo["after_inertia"]:,.0f}', "retrained model, scored on the same real data")}
      {stat_tile("Example patient's cluster", "→", cluster_shift_note)}
    </div>
    {callout("critical", "!", f'''The live production model has never seen <b>{cdemo["n_unseen_disease_rows"]:,}</b> of these
    {'{:,}'.format(int(sum(cdemo["before_sizes"].values())))} real patients' diagnoses — it only recognizes
    <b>{cdemo["n_disease_categories_before"]}</b> disease names from whenever it was last trained. For those patients, disease
    contributes nothing to which cluster they land in (silently dropped by <span class="mono">OneHotEncoder(handle_unknown="ignore")</span>)
    — only age/gender/prakriti/vikriti/severity decide it. This is a bigger, pre-existing accuracy gap than the synthetic-patient
    experiment below; it means the live clustering model is due for a retrain against current data independent of anything new
    being added.''')}
    <div class="card">
      <div class="legend">
        <span><span class="dot" style="background:var(--accent)"></span>Before</span>
        <span><span class="dot" style="background:var(--accent-2)"></span>After (+{cdemo["n_synthetic"]} synthetic)</span>
      </div>
      <div class="chart-title">Cluster sizes, same {'{:,}'.format(int(sum(cdemo["before_sizes"].values())))} real patients, re-labeled by each model</div>
      {before_after_bar}
    </div>
    <p class="lead"><b>Caveat that matters:</b> K-Means cluster indices aren't stable across separate fits — "Cluster 8" in the
    before-model and "Cluster 8" in the after-model are not guaranteed to describe the same population. Every retrain can silently
    renumber clusters, which is also why the RL Q-table's <span class="mono">cluster_id</span> keys can go stale the moment
    <span class="mono">retrain_clusters()</span> runs again.</p>
  </section>

  <section>
    <h2><span class="eyebrow">Section 4 · Operation</span>RL retrain — real data vs a synthetic walkthrough</h2>
    <p class="lead">Part A replays <span class="mono">retrain_from_feedback()</span>'s exact decision logic against your real
    {rlgap["total_unprocessed"]:,} unprocessed feedback rows, read-only. Part B fabricates a small event sequence (not real patients) to show
    the update rule itself: <span class="mono">Q(s,a) += {LEARNING_RATE} × (reward − Q(s,a))</span>.</p>

    {callout("good" if rlgap["applied"]==0 else "critical", "i", f'''Part A result: of {rlgap["total_unprocessed"]:,} unprocessed rows,
    <b>{rlgap["skipped_no_context"]:,}</b> were skipped for missing cluster_id/disease, <b>{rlgap["zero_reward"]:,}</b> had no reward, and
    <b>{rlgap["applied"]}</b> Q-values were actually updated. Q-table copy unchanged: <b>{rlgap["q_table_unchanged"]}</b>.''')}

    <div class="card">
      <div class="chart-title">Part B — synthetic event ledger</div>
      {ledger_table}
    </div>
    <div class="card chart-card">
      <div class="legend">{traj_legend}</div>
      <div class="chart-title">Q-value trajectory per (state, action) across its own updates</div>
      {traj_chart}
    </div>
  </section>

  <footer class="foot">
    Safety verification: {ctx["safety_note"]}<br/>
    Re-run: <span class="mono">python3 backend/scripts/model_report.py</span> — every number here is recomputed live from the
    current DB and model files at run time, nothing is cached.
  </footer>

</div>
<script>{JS}</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=os.path.join(BACKEND_DIR, "reports", "model_report.html"))
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    before_mtime_c, before_size_c = os.path.getmtime(REAL_CLUSTER_PATH), os.path.getsize(REAL_CLUSTER_PATH)
    before_mtime_q, before_size_q = os.path.getmtime(REAL_QTABLE_PATH), os.path.getsize(REAL_QTABLE_PATH)

    sandbox_dir = tempfile.mkdtemp(prefix="model_report_sandbox_")
    try:
        with SessionLocal() as db:
            print("Reading DB (read-only)...")
            db_s = db_snapshot(db)
            gap = feedback_cluster_id_gap(db)
            before_is_retrained_true = db_s["is_retrained_true"]

            print("Loading real models (read-only)...")
            real_pipeline = joblib.load(REAL_CLUSTER_PATH)
            real_q_table = joblib.load(REAL_QTABLE_PATH)
            df_real = fetch_training_frame(db)
            cluster_stats = characterize_clusters(real_pipeline, df_real)
            q_stats = qtable_stats(real_q_table)

            print("Simulating clustering retrain in sandbox...")
            cluster_demo = clustering_retrain_demo(df_real, real_pipeline, sandbox_dir)

            print("Simulating RL retrain against real feedback (read-only, no commit)...")
            q_table_sandbox_copy = copy.deepcopy(real_q_table)
            rl_gap_demo = rl_real_data_gap_demo(db, q_table_sandbox_copy)

            after_is_retrained_true = db.query(TreatmentFeedback).filter(TreatmentFeedback.is_retrained == True).count()  # noqa: E712

        print("Running synthetic RL walkthrough...")
        rl_walkthrough = rl_synthetic_walkthrough()

        after_mtime_c, after_size_c = os.path.getmtime(REAL_CLUSTER_PATH), os.path.getsize(REAL_CLUSTER_PATH)
        after_mtime_q, after_size_q = os.path.getmtime(REAL_QTABLE_PATH), os.path.getsize(REAL_QTABLE_PATH)
        cluster_file_untouched = (before_mtime_c, before_size_c) == (after_mtime_c, after_size_c)
        qtable_file_untouched = (before_mtime_q, before_size_q) == (after_mtime_q, after_size_q)
        db_untouched = before_is_retrained_true == after_is_retrained_true

        safety_note = (
            f'cluster model file unchanged: {cluster_file_untouched} · '
            f'Q-table file unchanged: {qtable_file_untouched} · '
            f'is_retrained=True count unchanged ({before_is_retrained_true:,} → {after_is_retrained_true:,}): {db_untouched}'
        )
        assert cluster_file_untouched and qtable_file_untouched and db_untouched, "SAFETY CHECK FAILED: production state changed!"
        print(f"Safety check passed — {safety_note}")

        ctx = {
            "db_snapshot": db_s, "gap": gap, "cluster_stats": cluster_stats, "qtable_stats": q_stats,
            "cluster_demo": cluster_demo, "rl_gap_demo": rl_gap_demo, "rl_walkthrough": rl_walkthrough,
            "safety_note": safety_note,
        }
        html = render_html(ctx)

        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w") as f:
            f.write(html)
        print(f"\nReport written to {args.output}")
        if args.open:
            webbrowser.open(f"file://{os.path.abspath(args.output)}")
    finally:
        shutil.rmtree(sandbox_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
