"""Freeze caller-supplied Edge graph-release configuration in a session."""

from __future__ import annotations

import json
from pathlib import Path

from abel_invest.narrative_core.contracts.constants import GRAPH_RELEASE_FILENAME


def load_graph_release(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("graph release must be a JSON mapping")
    if payload.get("contract") != "abel-edge.graph-release/v1":
        raise ValueError("graph release must use abel-edge.graph-release/v1")
    graph_ref = payload.get("graph_ref")
    if not isinstance(graph_ref, dict) or not str(graph_ref.get("graph_version") or ""):
        raise ValueError("graph release must declare graph_ref.graph_version")
    return payload


def freeze_graph_release(session: Path, payload: dict) -> Path:
    path = session / GRAPH_RELEASE_FILENAME
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
