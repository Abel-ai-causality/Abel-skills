"""Bounded, resumable helper for disposable Abel Invest scout scripts."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_MAX_SECONDS = 300.0
DEFAULT_PROGRESS_INTERVAL_SECONDS = 30.0
DEFAULT_RANK_KEYS = ("selection_score", "sharpe", "total_return")


@dataclass(frozen=True)
class ScoutEstimate:
    """Dry-run estimate for a bounded scout run."""

    name: str
    target: str
    candidate_count: int
    row_count: int | None = None
    feed_symbols: Sequence[str] = field(default_factory=tuple)
    planned_families: Sequence[str] = field(default_factory=tuple)
    estimated_seconds: float = 0.0
    max_seconds: float = DEFAULT_MAX_SECONDS
    reduction_hint: str = ""

    @property
    def within_budget(self) -> bool:
        return self.estimated_seconds <= self.max_seconds

    def to_dict(self) -> dict[str, Any]:
        hint = self.reduction_hint
        if not hint and not self.within_budget:
            hint = default_reduction_hint()
        return {
            "name": self.name,
            "target": self.target,
            "candidate_count": self.candidate_count,
            "row_count": self.row_count,
            "feed_count": len(self.feed_symbols),
            "feed_symbols": list(self.feed_symbols),
            "planned_families": list(self.planned_families),
            "estimated_seconds": round(float(self.estimated_seconds), 3),
            "max_seconds": round(float(self.max_seconds), 3),
            "within_budget": self.within_budget,
            "reduction_hint": hint,
        }


class ScoutRun:
    """Small execution contract for agent-authored first-look scouts.

    The helper intentionally does not prescribe alpha families or scoring logic.
    It only standardizes dry-run estimates, streaming result persistence,
    resumability, and compact stdout.
    """

    def __init__(
        self,
        *,
        name: str,
        output_dir: str | Path,
        max_seconds: float = DEFAULT_MAX_SECONDS,
        progress_interval_seconds: float = DEFAULT_PROGRESS_INTERVAL_SECONDS,
        rank_keys: Sequence[str] = DEFAULT_RANK_KEYS,
        top_k: int = 5,
    ) -> None:
        self.name = name
        self.output_dir = Path(output_dir)
        self.max_seconds = float(max_seconds)
        self.progress_interval_seconds = float(progress_interval_seconds)
        self.rank_keys = tuple(rank_keys)
        self.top_k = int(top_k)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def dry_run_path(self) -> Path:
        return self.output_dir / f"{self.name}.dry_run.json"

    @property
    def results_path(self) -> Path:
        return self.output_dir / f"{self.name}.results.jsonl"

    @property
    def state_path(self) -> Path:
        return self.output_dir / f"{self.name}.state.json"

    @property
    def summary_path(self) -> Path:
        return self.output_dir / f"{self.name}.summary.json"

    def write_dry_run(self, estimate: ScoutEstimate) -> dict[str, Any]:
        payload = estimate.to_dict()
        payload["artifacts"] = self._artifact_paths()
        self._write_json(self.dry_run_path, payload)
        print(
            "scout_dry_run "
            f"name={estimate.name} target={estimate.target} "
            f"candidate_count={estimate.candidate_count} "
            f"estimated_seconds={payload['estimated_seconds']} "
            f"max_seconds={payload['max_seconds']} "
            f"within_budget={str(payload['within_budget']).lower()}"
        )
        if payload["reduction_hint"]:
            print(f"reduction_hint={payload['reduction_hint']}")
        print(f"artifacts dry_run={self.dry_run_path}")
        return payload

    def run(
        self,
        candidates: Iterable[Any],
        scorer: Callable[[Any], dict[str, Any]],
        *,
        resume: bool = False,
        max_seconds: float | None = None,
    ) -> dict[str, Any]:
        budget = self.max_seconds if max_seconds is None else float(max_seconds)
        completed_indices = self._completed_indices() if resume else set()
        start_time = time.monotonic()
        last_progress = start_time
        completed_this_run = 0
        skipped = 0
        status = "completed"

        for index, candidate in enumerate(candidates):
            if index in completed_indices:
                skipped += 1
                continue
            elapsed = time.monotonic() - start_time
            if elapsed >= budget:
                status = "timeout"
                break
            result = scorer(candidate)
            if not isinstance(result, dict):
                raise TypeError("Scout scorer must return a dict.")
            row = {
                "candidate_index": index,
                "candidate": _json_safe(candidate),
                "result": _json_safe(result),
                "elapsed_seconds": round(time.monotonic() - start_time, 3),
                "completed_at": _now_epoch(),
            }
            self._append_jsonl(self.results_path, row)
            completed_indices.add(index)
            completed_this_run += 1

            now = time.monotonic()
            if now - last_progress >= self.progress_interval_seconds:
                last_progress = now
                self._write_state(
                    status="running",
                    next_candidate_index=index + 1,
                    completed_count=len(completed_indices),
                    skipped_count=skipped,
                    elapsed_seconds=now - start_time,
                    max_seconds=budget,
                )
                self.write_summary(status="running")
                print(
                    "scout_progress "
                    f"name={self.name} completed={len(completed_indices)} "
                    f"elapsed_seconds={round(now - start_time, 3)} "
                    f"results={self.results_path}"
                )

        elapsed = time.monotonic() - start_time
        if status == "completed":
            next_index = len(completed_indices)
        else:
            next_index = max(completed_indices) + 1 if completed_indices else 0
        state = self._write_state(
            status=status,
            next_candidate_index=next_index,
            completed_count=len(completed_indices),
            skipped_count=skipped,
            elapsed_seconds=elapsed,
            max_seconds=budget,
        )
        summary = self.write_summary(status=status)
        print(
            "scout_complete "
            f"name={self.name} status={status} "
            f"completed={completed_this_run} total_completed={len(completed_indices)} "
            f"elapsed_seconds={round(elapsed, 3)}"
        )
        for rank, row in enumerate(summary.get("top", [])[: self.top_k], start=1):
            result = row.get("result") or {}
            print(
                "scout_top "
                f"rank={rank} name={result.get('name', row.get('candidate_index'))} "
                f"family={result.get('family', '')} "
                f"score={_rank_value(result, self.rank_keys)}"
            )
        print(
            "artifacts "
            f"results={self.results_path} state={self.state_path} "
            f"summary={self.summary_path}"
        )
        return {"state": state, "summary": summary}

    def write_summary(self, *, status: str) -> dict[str, Any]:
        rows = self._read_results()
        ranked = sorted(
            rows,
            key=lambda row: _rank_value(row.get("result") or {}, self.rank_keys),
            reverse=True,
        )
        family_best: dict[str, dict[str, Any]] = {}
        for row in ranked:
            result = row.get("result") or {}
            family = str(result.get("family") or "unknown")
            if family not in family_best:
                family_best[family] = row
        payload = {
            "name": self.name,
            "status": status,
            "completed_count": len(rows),
            "top": ranked[: self.top_k],
            "family_best": family_best,
            "artifacts": self._artifact_paths(),
        }
        self._write_json(self.summary_path, payload)
        return payload

    def _artifact_paths(self) -> dict[str, str]:
        return {
            "dry_run": str(self.dry_run_path),
            "results": str(self.results_path),
            "state": str(self.state_path),
            "summary": str(self.summary_path),
        }

    def _completed_indices(self) -> set[int]:
        indices: set[int] = set()
        for row in self._read_results():
            try:
                indices.add(int(row.get("candidate_index")))
            except (TypeError, ValueError):
                continue
        return indices

    def _read_results(self) -> list[dict[str, Any]]:
        if not self.results_path.exists():
            return []
        rows = []
        for line in self.results_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rows.append(json.loads(line))
        return rows

    def _write_state(
        self,
        *,
        status: str,
        next_candidate_index: int,
        completed_count: int,
        skipped_count: int,
        elapsed_seconds: float,
        max_seconds: float,
    ) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "status": status,
            "next_candidate_index": int(next_candidate_index),
            "completed_count": int(completed_count),
            "skipped_count": int(skipped_count),
            "elapsed_seconds": round(float(elapsed_seconds), 3),
            "max_seconds": round(float(max_seconds), 3),
            "artifacts": self._artifact_paths(),
            "updated_at": _now_epoch(),
        }
        self._write_json(self.state_path, payload)
        return payload

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def estimate_seconds(
    candidate_count: int,
    *,
    seconds_per_candidate: float,
    fixed_seconds: float = 0.0,
) -> float:
    return float(fixed_seconds) + int(candidate_count) * float(seconds_per_candidate)


def default_reduction_hint() -> str:
    return "reduce candidate families, then lag/window grid, graph feed count, model families, and ensemble variants"


def _rank_value(result: dict[str, Any], rank_keys: Sequence[str]) -> float:
    for key in rank_keys:
        value = result.get(key)
        if isinstance(value, (int, float)):
            return float(value)
        try:
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            continue
    return float("-inf")


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        if hasattr(value, "to_dict"):
            return value.to_dict()
        return repr(value)


def _now_epoch() -> float:
    return round(time.time(), 3)
