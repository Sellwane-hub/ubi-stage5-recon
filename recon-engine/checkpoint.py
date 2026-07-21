"""Checkpoint state: lets an interrupted run resume without repeating completed
stages. After each stage the engine saves its completed stages and the records
found so far. On startup it loads any existing checkpoint and skips done stages.

Because normalization sorts records by identity before hashing, a resumed run
that reassembles records in a different order still produces the same result
hash as an uninterrupted run.
"""

import json
from pathlib import Path

STAGES = ["ports", "signal", "http"]


def load(path):
    """Load checkpoint state, or return a fresh empty state if none exists."""
    p = Path(path)
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return {
                "completed": data.get("completed", []),
                "records": data.get("records", []),
                "vhost": data.get("vhost"),
                "signal_port": data.get("signal_port"),
            }
        except (json.JSONDecodeError, OSError):
            pass
    return {"completed": [], "records": [], "vhost": None, "signal_port": None}


def save(path, state):
    """Persist checkpoint state atomically (write temp, then replace)."""
    p = Path(path)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, sort_keys=True, indent=2), encoding="utf-8")
    tmp.replace(p)  # atomic on the same filesystem


def is_done(state, stage):
    """Has this stage already been completed in a prior run?"""
    return stage in state["completed"]


def mark_done(state, stage):
    """Mark a stage complete (idempotent)."""
    if stage not in state["completed"]:
        state["completed"].append(stage)
