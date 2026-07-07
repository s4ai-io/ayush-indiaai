"""
utils/run_logger.py

Per-run structured JSON logger for the full voice pipeline:
  voice input → transcription (ASR) → translation → vllm phi-4 extraction

Each pipeline invocation produces ONE JSON file:
  backend/logs/runs/<YYYY-MM-DD_HH-MM-SS.mmm>_<run_id>.json

Schema:
{
  "run_id":           "abc123def456",
  "datetime":         "2026-02-28T10:15:30.123",
  "voice_input_file": "/absolute/path/to/audio.webm",  # or null
  "transcriptor": { "input": {...}, "output": {...}|null, "error": "..."|null },
  "translator":   { ... } | null,   # null when input is English
  "vllm_phi4":    { ... } | null    # appended by llm_logger after LLM call
}

Usage in a request handler:
    rl = RunLogger()
    rl.set_voice_file("/path/to/audio.webm")
    rl.update_step("transcriptor", input={...}, output={...})
    rl.update_step("translator",   input={...}, output={...})
    rl.finalize()   # writes JSON to disk

Usage from llm_logger (cross-request, different process context):
    rl = RunLogger.load_existing(run_id)
    if rl:
        rl.update_step("vllm_phi4", input={...}, output={...})
        rl.finalize()
"""

import json
import os
import uuid
import datetime
from typing import Any, Dict, Optional

# ── Directory setup ─────────────────────────────────────────────────────────────
# backend/utils/run_logger.py  →  backend/logs/runs/
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS_DIR = os.path.join(_BACKEND_DIR, "logs", "runs")
VOICE_DIR = os.path.join(_BACKEND_DIR, "logs", "voice_inputs")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="milliseconds")


def _ts_for_filename(iso: str) -> str:
    """YYYY-MM-DDTHH:MM:SS.mmm → YYYY-MM-DD_HH-MM-SS.mmm  (filesystem-safe)"""
    date_part, time_part = iso.split("T")
    time_clean = time_part.split("+")[0].split("Z")[0]   # strip tz
    ms = time_clean.split(".")[-1][:3] if "." in time_clean else "000"
    hms = time_clean.split(".")[0].replace(":", "-")
    return f"{date_part}_{hms}.{ms}"


# ── RunLogger ───────────────────────────────────────────────────────────────────

class RunLogger:
    """
    Context object for one voice-pipeline run.

    Normal usage (new run):
        rl = RunLogger()               # creates fresh run_id
        ...
        rl.finalize()                  # flushes to backend/logs/runs/

    Cross-request usage (attach vllm step to existing run):
        rl = RunLogger.load_existing(run_id)
        if rl:
            rl.update_step("vllm_phi4", ...)
            rl.finalize()
    """

    # ── Construction ────────────────────────────────────────────────────────────

    def __init__(self, run_id: Optional[str] = None):
        self.run_id: str = run_id or uuid.uuid4().hex[:12]
        self._created_at: str = _now_iso()
        self._record: Dict[str, Any] = {
            "run_id": self.run_id,
            "datetime": self._created_at,
            "voice_input_file": None,
            "transcriptor": None,
            "translator": None,
            "vllm_phi4": None,
            "gemma4_turn": None,
        }
        self._override_path: Optional[str] = None   # set by load_existing()
        _ensure_dir(RUNS_DIR)
        _ensure_dir(VOICE_DIR)

    @classmethod
    def load_existing(cls, run_id: str) -> "Optional[RunLogger]":
        """
        Scan RUNS_DIR for a file whose name contains run_id.
        Loads the JSON and returns a RunLogger bound to that file.
        Returns None if not found or on error.
        """
        _ensure_dir(RUNS_DIR)
        for fname in sorted(os.listdir(RUNS_DIR), reverse=True):  # newest first
            if run_id in fname and fname.endswith(".json"):
                fpath = os.path.join(RUNS_DIR, fname)
                try:
                    with open(fpath, encoding="utf-8") as f:
                        data = json.load(f)
                    inst = cls.__new__(cls)
                    inst.run_id = data["run_id"]
                    inst._created_at = data.get("datetime", _now_iso())
                    inst._record = data
                    inst._override_path = fpath
                    _ensure_dir(RUNS_DIR)
                    _ensure_dir(VOICE_DIR)
                    return inst
                except Exception as exc:
                    print(f"[run_logger] load_existing({run_id}): {exc}")
                    return None
        print(f"[run_logger] load_existing: no file found for run_id={run_id}")
        return None

    # ── Setters ─────────────────────────────────────────────────────────────────

    def set_voice_file(self, file_path: str) -> None:
        """Store the absolute path of the saved voice recording."""
        self._record["voice_input_file"] = file_path

    def update_step(
        self,
        step: str,          # "transcriptor" | "translator" | "vllm_phi4" | "gemma4_turn"
        *,
        input: Optional[Dict[str, Any]] = None,
        output: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> None:
        """Attach input / output / error for a pipeline step."""
        if step not in ("transcriptor", "translator", "vllm_phi4", "gemma4_turn"):
            raise ValueError(f"Unknown step: {step!r}")
        self._record[step] = {"input": input, "output": output, "error": error}

    # ── File path ────────────────────────────────────────────────────────────────

    @property
    def file_path(self) -> str:
        """Absolute path of the run JSON file."""
        if self._override_path:
            return self._override_path
        ts = _ts_for_filename(self._created_at)
        return os.path.join(RUNS_DIR, f"{ts}_{self.run_id}.json")

    # ── Persistence ──────────────────────────────────────────────────────────────

    def flush(self) -> None:
        """Write/overwrite the run file. Safe to call multiple times."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._record, f, indent=2, ensure_ascii=False, default=str)
        except Exception as exc:
            print(f"[run_logger] flush failed: {exc}")

    def finalize(self) -> str:
        """Final flush. Returns the path of the written file."""
        self.flush()
        print(f"[run_logger] ✓ Run {self.run_id} → {self.file_path}")
        return self.file_path
