"""
episode_dedup.py
──────────────────
Collapses a single patient's repeat visits for the same diagnosis into one
"episode" before they get counted, so a patient who visits 3 times for the
same complaint isn't counted as 3 independent cases. The kept row is always
the episode's most recent visit ("last diagnosis is the final verdict").

Two modes, both used somewhere in analytics_service.py / spatial_service.py /
disease_forecaster.py:

  gap_days=None — the patient's entire history of this diagnosis collapses to
    one episode (their single latest visit). For all-time aggregate panels
    (hotspots, clusters) where the question is "how many distinct people are
    affected", not "how many visits occurred".

  gap_days=N — visits more than N days apart start a new episode. For
    time-series signal detection (monthly/weekly alerts, forecasting) where a
    patient's genuinely separate recurrence weeks/months later is still a
    real, distinct incidence — only tight-together repeat/follow-up visits
    should collapse.
"""
from __future__ import annotations

from datetime import timedelta


def dedupe_repeat_diagnoses(
    rows: list[tuple],
    patient_idx: int,
    diagnosis_idx: int,
    date_idx: int,
    gap_days: int | None = None,
) -> list[tuple]:
    """Return a filtered copy of `rows`, one row per episode."""
    groups: dict[tuple, list[tuple]] = {}
    for row in rows:
        key = (row[patient_idx], row[diagnosis_idx])
        groups.setdefault(key, []).append(row)

    kept: list[tuple] = []
    for items in groups.values():
        items.sort(key=lambda r: r[date_idx])

        if gap_days is None:
            kept.append(items[-1])  # whole history is one episode
            continue

        episode = [items[0]]
        for row in items[1:]:
            if (row[date_idx] - episode[-1][date_idx]) > timedelta(days=gap_days):
                kept.append(episode[-1])
                episode = [row]
            else:
                episode.append(row)
        kept.append(episode[-1])

    return kept
