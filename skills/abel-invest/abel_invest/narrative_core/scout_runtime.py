"""Bounded, resumable helper for disposable Abel Invest scout scripts."""

from __future__ import annotations

import json
import signal
import time
from collections.abc import Callable, Iterable, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from threading import current_thread, main_thread
from typing import Any


DEFAULT_MAX_SECONDS = 120.0
DEFAULT_ROUND_BUDGET_SECONDS = 120.0
DEFAULT_PROGRESS_INTERVAL_SECONDS = 30.0
DEFAULT_RANK_KEYS = ("selection_score", "sharpe", "total_return")
DEFAULT_TIMEOUT_BEHAVIOR = "stop"


class ScoutCandidateTimeout(TimeoutError):
    """Raised when runtime enforcement stops one slow scout candidate."""


@dataclass(frozen=True)
class ScoutFamilyBudget:
    """Free-form budget declaration for one planned scout candidate group.

    The agent-authored seconds are not trusted timing facts. They are a compact
    declaration of intended search width so the runtime can gate obvious budget
    violations before execution and record how the declaration compared with
    actual streamed results afterward.

    The label and traits are deliberately not enums. They describe computation
    shape for budget accounting without constraining strategy direction.
    """

    label: str
    candidate_count: int
    budget_seconds: float
    max_candidate_seconds: float | None = None
    cost_traits: Sequence[str] = field(default_factory=tuple)
    reduction_axes: Sequence[str] = field(default_factory=tuple)
    stage: str = ""

    def __init__(
        self,
        *,
        label: str,
        candidate_count: int,
        budget_seconds: float | None = None,
        estimated_seconds: float | None = None,
        max_candidate_seconds: float | None = None,
        cost_traits: Sequence[str] = (),
        reduction_axes: Sequence[str] = (),
        stage: str = "",
    ) -> None:
        if budget_seconds is None:
            budget_seconds = 0.0 if estimated_seconds is None else estimated_seconds
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "candidate_count", candidate_count)
        object.__setattr__(self, "budget_seconds", budget_seconds)
        object.__setattr__(self, "max_candidate_seconds", max_candidate_seconds)
        object.__setattr__(self, "cost_traits", tuple(cost_traits))
        object.__setattr__(self, "reduction_axes", tuple(reduction_axes))
        object.__setattr__(self, "stage", stage)

    def to_dict(self) -> dict[str, Any]:
        budget_seconds = round(float(self.budget_seconds), 3)
        return {
            "label": str(self.label),
            "candidate_count": int(self.candidate_count),
            "budget_seconds": budget_seconds,
            "estimated_seconds": budget_seconds,
            "max_candidate_seconds": (
                None
                if self.max_candidate_seconds is None
                else round(float(self.max_candidate_seconds), 3)
            ),
            "cost_traits": [str(item) for item in self.cost_traits],
            "reduction_axes": [str(item) for item in self.reduction_axes],
            "stage": str(self.stage),
        }


ScoutFamilyEstimate = ScoutFamilyBudget


@dataclass(frozen=True)
class ScoutEstimate:
    """Dry-run budget declaration for a bounded scout run."""

    name: str
    target: str
    candidate_count: int
    row_count: int | None = None
    feed_symbols: Sequence[str] = field(default_factory=tuple)
    planned_families: Sequence[str] = field(default_factory=tuple)
    family_breakdown: Sequence[ScoutFamilyBudget | dict[str, Any]] = field(default_factory=tuple)
    budget_seconds: float | None = None
    estimated_seconds: float = 0.0
    max_seconds: float = DEFAULT_MAX_SECONDS
    max_family_seconds: float | None = None
    max_candidate_seconds: float | None = None
    reduction_hint: str = ""

    @property
    def declared_budget_seconds(self) -> float:
        if self.budget_seconds is not None:
            return float(self.budget_seconds)
        return float(self.estimated_seconds)

    @property
    def within_budget(self) -> bool:
        return (
            self.declared_budget_seconds <= self.max_seconds
            and not self.over_budget_families
            and not self.slow_candidate_families
        )

    @property
    def normalized_family_breakdown(self) -> list[dict[str, Any]]:
        return [_normalize_family_budget(item) for item in self.family_breakdown]

    @property
    def slowest_family(self) -> dict[str, Any] | None:
        families = self.normalized_family_breakdown
        if not families:
            return None
        return max(families, key=lambda item: float(item.get("budget_seconds") or 0.0))

    @property
    def over_budget_families(self) -> list[dict[str, Any]]:
        if self.max_family_seconds is None:
            return []
        budget = float(self.max_family_seconds)
        return [
            item
            for item in self.normalized_family_breakdown
            if float(item.get("budget_seconds") or 0.0) > budget
        ]

    @property
    def slow_candidate_families(self) -> list[dict[str, Any]]:
        if self.max_candidate_seconds is None:
            return []
        budget = float(self.max_candidate_seconds)
        return [
            item
            for item in self.normalized_family_breakdown
            if item.get("max_candidate_seconds") is not None
            and float(item.get("max_candidate_seconds") or 0.0) > budget
        ]

    def to_dict(self) -> dict[str, Any]:
        hint = self.reduction_hint
        if not hint and not self.within_budget:
            hint = default_reduction_hint()
        family_breakdown = self.normalized_family_breakdown
        slowest = self.slowest_family
        return {
            "name": self.name,
            "target": self.target,
            "candidate_count": self.candidate_count,
            "row_count": self.row_count,
            "feed_count": len(self.feed_symbols),
            "feed_symbols": list(self.feed_symbols),
            "planned_families": list(self.planned_families),
            "family_breakdown": family_breakdown,
            "slowest_family": slowest,
            "over_budget_families": self.over_budget_families,
            "slow_candidate_families": self.slow_candidate_families,
            "budget_seconds": round(self.declared_budget_seconds, 3),
            "estimated_seconds": round(self.declared_budget_seconds, 3),
            "max_seconds": round(float(self.max_seconds), 3),
            "max_family_seconds": (
                None
                if self.max_family_seconds is None
                else round(float(self.max_family_seconds), 3)
            ),
            "max_candidate_seconds": (
                None
                if self.max_candidate_seconds is None
                else round(float(self.max_candidate_seconds), 3)
            ),
            "within_budget": self.within_budget,
            "reduction_hint": hint,
        }


class ScoutRun:
    """Small execution contract for agent-authored first-look scouts.

    The helper intentionally does not prescribe alpha families or scoring logic.
    It only standardizes dry-run budget declarations, streaming result persistence,
    resumability, and compact stdout.
    """

    def __init__(
        self,
        *,
        name: str,
        output_dir: str | Path,
        max_seconds: float = DEFAULT_MAX_SECONDS,
        max_candidate_seconds: float | None = None,
        timeout_behavior: str = DEFAULT_TIMEOUT_BEHAVIOR,
        continue_on_candidate_error: bool = True,
        progress_interval_seconds: float = DEFAULT_PROGRESS_INTERVAL_SECONDS,
        round_budget_seconds: float | None = DEFAULT_ROUND_BUDGET_SECONDS,
        rank_keys: Sequence[str] = DEFAULT_RANK_KEYS,
        top_k: int = 5,
    ) -> None:
        self.name = name
        self.output_dir = Path(output_dir)
        self.max_seconds = float(max_seconds)
        self.max_candidate_seconds = (
            None if max_candidate_seconds is None else float(max_candidate_seconds)
        )
        self.timeout_behavior = timeout_behavior
        self.continue_on_candidate_error = bool(continue_on_candidate_error)
        self.progress_interval_seconds = float(progress_interval_seconds)
        self.round_budget_seconds = (
            None if round_budget_seconds is None else float(round_budget_seconds)
        )
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

    @property
    def round_budget_path(self) -> Path:
        return self.output_dir / "scout_budget_state.json"

    def write_dry_run(self, estimate: ScoutEstimate) -> dict[str, Any]:
        payload = estimate.to_dict()
        payload["artifacts"] = self._artifact_paths()
        payload["round_budget"] = self._round_budget_snapshot()
        self._write_json(self.dry_run_path, payload)
        round_budget = payload["round_budget"]
        print(
            "scout_dry_run "
            f"name={estimate.name} target={estimate.target} "
            f"candidate_count={estimate.candidate_count} "
            f"budget_seconds={payload['budget_seconds']} "
            f"max_seconds={payload['max_seconds']} "
            f"round_budget_remaining={round_budget['remaining_seconds']} "
            f"within_budget={str(payload['within_budget']).lower()}"
        )
        if payload["reduction_hint"]:
            print(f"reduction_hint={payload['reduction_hint']}")
        for family in payload["family_breakdown"]:
            print(
                "scout_family "
                f"label={family.get('label')} "
                f"candidates={family.get('candidate_count')} "
                f"budget_seconds={family.get('budget_seconds')} "
                f"max_candidate_seconds={family.get('max_candidate_seconds')}"
            )
        print(f"artifacts dry_run={self.dry_run_path}")
        return payload

    def run(
        self,
        candidates: Iterable[Any],
        scorer: Callable[[Any], dict[str, Any]],
        *,
        resume: bool = False,
        max_seconds: float | None = None,
        max_candidate_seconds: float | None = None,
    ) -> dict[str, Any]:
        requested_budget = self.max_seconds if max_seconds is None else float(max_seconds)
        round_budget = self._round_budget_snapshot()
        round_remaining = round_budget["remaining_seconds"]
        budget = requested_budget
        budget_limited_by_round = False
        if round_remaining is not None:
            budget = min(requested_budget, float(round_remaining))
            budget_limited_by_round = budget < requested_budget
        candidate_budget = (
            self.max_candidate_seconds
            if max_candidate_seconds is None
            else float(max_candidate_seconds)
        )
        enforcement_mode = _timeout_enforcement_mode(candidate_budget)
        completed_indices = self._completed_indices() if resume else set()
        start_time = time.monotonic()
        last_progress = start_time
        completed_this_run = 0
        skipped = 0
        status = "completed"
        timeout_scope = ""

        if budget <= 0:
            next_index = max(completed_indices) + 1 if completed_indices else 0
            state = self._write_state(
                status="budget_exhausted",
                next_candidate_index=next_index,
                completed_count=len(completed_indices),
                skipped_count=0,
                elapsed_seconds=0.0,
                max_seconds=0.0,
                max_candidate_seconds=candidate_budget,
                timeout_scope="round_budget",
                timeout_enforcement=enforcement_mode,
                round_budget=round_budget,
            )
            summary = self.write_summary(status="budget_exhausted", round_budget=round_budget)
            print(
                "scout_complete "
                f"name={self.name} status=budget_exhausted "
                f"completed=0 total_completed={len(completed_indices)} "
                "elapsed_seconds=0.0"
            )
            print(
                "round_budget_exhausted "
                f"round_key={round_budget['round_key']} "
                f"used_seconds={round_budget['used_seconds']} "
                f"budget_seconds={round_budget['budget_seconds']}"
            )
            print(
                "artifacts "
                f"results={self.results_path} state={self.state_path} "
                f"summary={self.summary_path} round_budget={self.round_budget_path}"
            )
            return {"state": state, "summary": summary}

        for index, candidate in enumerate(candidates):
            if index in completed_indices:
                skipped += 1
                continue
            elapsed = time.monotonic() - start_time
            if elapsed >= budget:
                status = "budget_exhausted" if budget_limited_by_round else "timeout"
                timeout_scope = "round_budget" if budget_limited_by_round else "run"
                break
            try:
                with _candidate_timeout(candidate_budget):
                    result = scorer(candidate)
            except ScoutCandidateTimeout:
                status = "timeout"
                timeout_scope = "candidate"
                result = {
                    "name": _candidate_name(candidate, index),
                    "family": _candidate_family(candidate),
                    "status": "timeout",
                    "error": "candidate_timeout",
                    "timeout_seconds": candidate_budget,
                }
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
                if self.timeout_behavior == "continue":
                    continue
                break
            except Exception as exc:
                if not self.continue_on_candidate_error:
                    raise
                result = {
                    "name": _candidate_name(candidate, index),
                    "family": _candidate_family(candidate),
                    "status": "error",
                    "error": "candidate_error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
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
                continue
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
                    max_candidate_seconds=candidate_budget,
                    timeout_scope="",
                    timeout_enforcement=enforcement_mode,
                    round_budget=round_budget,
                )
                self.write_summary(status="running", round_budget=round_budget)
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
        final_round_budget = self._record_round_budget(
            elapsed_seconds=elapsed,
            status=status,
            requested_max_seconds=requested_budget,
            effective_max_seconds=budget,
        )
        state = self._write_state(
            status=status,
            next_candidate_index=next_index,
            completed_count=len(completed_indices),
            skipped_count=skipped,
            elapsed_seconds=elapsed,
            max_seconds=budget,
            max_candidate_seconds=candidate_budget,
            timeout_scope=timeout_scope,
            timeout_enforcement=enforcement_mode,
            round_budget=final_round_budget,
        )
        summary = self.write_summary(status=status, round_budget=final_round_budget)
        print(
            "scout_complete "
            f"name={self.name} status={status} "
            f"completed={completed_this_run} total_completed={len(completed_indices)} "
            f"elapsed_seconds={round(elapsed, 3)}"
        )
        print(
            "round_budget "
            f"round_key={final_round_budget['round_key']} "
            f"used_seconds={final_round_budget['used_seconds']} "
            f"remaining_seconds={final_round_budget['remaining_seconds']}"
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
            f"summary={self.summary_path} round_budget={self.round_budget_path}"
        )
        return {"state": state, "summary": summary}

    def write_summary(
        self,
        *,
        status: str,
        round_budget: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        rows = self._read_results()
        ranked = sorted(
            rows,
            key=lambda row: _rank_value(row.get("result") or {}, self.rank_keys),
            reverse=True,
        )
        family_best: dict[str, dict[str, Any]] = {}
        family_stats: dict[str, dict[str, Any]] = {}
        for row in ranked:
            result = row.get("result") or {}
            family = str(result.get("family") or "unknown")
            stats = family_stats.setdefault(
                family,
                {"completed_count": 0, "timeout_count": 0, "error_count": 0},
            )
            stats["completed_count"] += 1
            if result.get("status") == "timeout":
                stats["timeout_count"] += 1
            if result.get("error"):
                stats["error_count"] += 1
            if family not in family_best:
                family_best[family] = row
        payload = {
            "name": self.name,
            "status": status,
            "completed_count": len(rows),
            "top": ranked[: self.top_k],
            "family_best": family_best,
            "family_stats": family_stats,
            "artifacts": self._artifact_paths(),
            "round_budget": round_budget or self._round_budget_snapshot(),
        }
        self._write_json(self.summary_path, payload)
        return payload

    def _artifact_paths(self) -> dict[str, str]:
        return {
            "dry_run": str(self.dry_run_path),
            "results": str(self.results_path),
            "state": str(self.state_path),
            "summary": str(self.summary_path),
            "round_budget": str(self.round_budget_path),
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
        max_candidate_seconds: float | None,
        timeout_scope: str,
        timeout_enforcement: str,
        round_budget: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "status": status,
            "next_candidate_index": int(next_candidate_index),
            "completed_count": int(completed_count),
            "skipped_count": int(skipped_count),
            "elapsed_seconds": round(float(elapsed_seconds), 3),
            "max_seconds": round(float(max_seconds), 3),
            "max_candidate_seconds": (
                None
                if max_candidate_seconds is None
                else round(float(max_candidate_seconds), 3)
            ),
            "timeout_scope": timeout_scope,
            "timeout_enforcement": timeout_enforcement,
            "round_budget": round_budget,
            "artifacts": self._artifact_paths(),
            "updated_at": _now_epoch(),
        }
        self._write_json(self.state_path, payload)
        return payload

    def _round_budget_snapshot(self) -> dict[str, Any]:
        recorded_rounds = self._recorded_round_count()
        key = f"recorded_rounds:{recorded_rounds}"
        budget_seconds = self.round_budget_seconds
        state = self._read_round_budget_state()
        round_state = (state.get("rounds") or {}).get(key) or {}
        used = round(float(round_state.get("used_seconds") or 0.0), 3)
        remaining = (
            None
            if budget_seconds is None
            else max(round(float(budget_seconds) - used, 3), 0.0)
        )
        return {
            "round_key": key,
            "recorded_rounds": recorded_rounds,
            "budget_seconds": None if budget_seconds is None else round(float(budget_seconds), 3),
            "used_seconds": used,
            "remaining_seconds": remaining,
            "state_path": str(self.round_budget_path),
        }

    def _record_round_budget(
        self,
        *,
        elapsed_seconds: float,
        status: str,
        requested_max_seconds: float,
        effective_max_seconds: float,
    ) -> dict[str, Any]:
        snapshot = self._round_budget_snapshot()
        if self.round_budget_seconds is None:
            return snapshot
        state = self._read_round_budget_state()
        rounds = state.setdefault("rounds", {})
        round_state = rounds.setdefault(
            snapshot["round_key"],
            {
                "recorded_rounds": snapshot["recorded_rounds"],
                "budget_seconds": snapshot["budget_seconds"],
                "used_seconds": 0.0,
                "runs": [],
            },
        )
        elapsed = max(float(elapsed_seconds), 0.0)
        used = round(float(round_state.get("used_seconds") or 0.0) + elapsed, 3)
        budget = float(self.round_budget_seconds)
        round_state["used_seconds"] = used
        round_state["remaining_seconds"] = max(round(budget - used, 3), 0.0)
        round_state["runs"] = list(round_state.get("runs") or [])
        round_state["runs"].append(
            {
                "name": self.name,
                "status": status,
                "elapsed_seconds": round(elapsed, 3),
                "requested_max_seconds": round(float(requested_max_seconds), 3),
                "effective_max_seconds": round(float(effective_max_seconds), 3),
                "results": str(self.results_path),
                "state": str(self.state_path),
                "summary": str(self.summary_path),
                "updated_at": _now_epoch(),
            }
        )
        state["round_budget_seconds"] = round(budget, 3)
        state["updated_at"] = _now_epoch()
        self._write_json(self.round_budget_path, state)
        return self._round_budget_snapshot()

    def _read_round_budget_state(self) -> dict[str, Any]:
        if not self.round_budget_path.exists():
            return {"rounds": {}}
        try:
            payload = json.loads(self.round_budget_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"rounds": {}}
        if not isinstance(payload, dict):
            return {"rounds": {}}
        payload.setdefault("rounds", {})
        return payload

    def _recorded_round_count(self) -> int:
        session_dir = self._infer_session_dir()
        if session_dir is None:
            return 0
        count = 0
        for results_path in sorted((session_dir / "branches").glob("*/results.tsv")):
            try:
                lines = results_path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            count += sum(1 for line in lines[1:] if line.strip())
        return count

    def _infer_session_dir(self) -> Path | None:
        if self.output_dir.name == "scratch" and (self.output_dir.parent / "branches").exists():
            return self.output_dir.parent
        if (self.output_dir / "branches").exists():
            return self.output_dir
        return None

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
    return "drop over-budget slow families first, then reduce lag/window grid, feed count, model settings, and ensemble variants"


def _normalize_family_budget(item: ScoutFamilyBudget | dict[str, Any]) -> dict[str, Any]:
    if isinstance(item, ScoutFamilyBudget):
        return item.to_dict()
    if not isinstance(item, dict):
        raise TypeError("family_breakdown items must be ScoutFamilyBudget or dict.")
    label = str(item.get("label") or item.get("name") or "unknown")
    max_candidate = item.get("max_candidate_seconds")
    budget_seconds = round(
        float(item.get("budget_seconds", item.get("estimated_seconds")) or 0.0),
        3,
    )
    return {
        "label": label,
        "candidate_count": int(item.get("candidate_count") or 0),
        "budget_seconds": budget_seconds,
        "estimated_seconds": budget_seconds,
        "max_candidate_seconds": (
            None if max_candidate is None else round(float(max_candidate), 3)
        ),
        "cost_traits": [str(value) for value in item.get("cost_traits") or ()],
        "reduction_axes": [str(value) for value in item.get("reduction_axes") or ()],
        "stage": str(item.get("stage") or ""),
    }


def _candidate_family(candidate: Any) -> str:
    if isinstance(candidate, dict):
        return str(candidate.get("family") or candidate.get("label") or "unknown")
    return str(getattr(candidate, "family", "") or getattr(candidate, "label", "") or "unknown")


def _candidate_name(candidate: Any, index: int) -> str:
    if isinstance(candidate, dict):
        return str(candidate.get("name") or candidate.get("label") or index)
    return str(getattr(candidate, "name", "") or getattr(candidate, "label", "") or index)


def _timeout_enforcement_mode(max_candidate_seconds: float | None) -> str:
    if max_candidate_seconds is None:
        return "none"
    if _signal_timeout_available():
        return "signal"
    return "cooperative"


def _signal_timeout_available() -> bool:
    return (
        current_thread() is main_thread()
        and hasattr(signal, "SIGALRM")
        and hasattr(signal, "setitimer")
    )


@contextmanager
def _candidate_timeout(seconds: float | None):
    if seconds is None or seconds <= 0 or not _signal_timeout_available():
        yield
        return

    previous_handler = signal.getsignal(signal.SIGALRM)
    try:
        previous_timer = signal.setitimer(signal.ITIMER_REAL, 0)
    except (AttributeError, ValueError):
        yield
        return

    def _raise_timeout(signum, frame):  # noqa: ARG001
        raise ScoutCandidateTimeout(f"candidate exceeded {seconds} seconds")

    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, float(seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        delay, interval = previous_timer
        if delay > 0:
            signal.setitimer(signal.ITIMER_REAL, delay, interval)


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
