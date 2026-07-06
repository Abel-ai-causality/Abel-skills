"""Small runtime helper for resumable Abel Invest scratch scouts."""

from __future__ import annotations

import json
import signal
import time
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from pathlib import Path
from typing import Any


DEFAULT_MAX_SECONDS = 120.0
DEFAULT_ROUND_BUDGET_SECONDS = 120.0
DEFAULT_PROGRESS_INTERVAL_SECONDS = 30.0
DEFAULT_TOP_K = 20
MAX_PARAM_VALUE_JSON_BYTES = 4096
SCOUT_IDENTITY_KEYS = ("name", "family", "category", "group", "label")
SCOUT_METRIC_KEYS = (
    "selection_score",
    "score",
    "sharpe",
    "sortino",
    "total_return",
    "ann_return",
    "test_total_return",
    "max_drawdown",
    "turnover",
    "exposure",
    "avg_abs_position",
    "mean_abs_exposure",
    "hit_rate",
    "rows",
    "bars",
    "days",
    "n_days",
    "trading_days",
    "selection_width",
    "width",
    "train_sharpe",
    "test_sharpe",
)
SCOUT_STATUS_KEYS = (
    "status",
    "error",
    "error_type",
    "error_message",
    "timeout_seconds",
)
SUMMARY_ROW_KEYS = (
    "candidate_index",
    "name",
    "family",
    "sort_value",
    "selection_score",
    "score",
    "sharpe",
    "sortino",
    "total_return",
    "ann_return",
    "test_total_return",
    "max_drawdown",
    "turnover",
    "exposure",
    "avg_abs_position",
    "mean_abs_exposure",
    "hit_rate",
    "rows",
    "bars",
    "days",
    "n_days",
    "trading_days",
    "selection_width",
    "width",
    "train_sharpe",
    "test_sharpe",
    "params",
)
FAMILY_BEST_ROW_KEYS = (
    "candidate_index",
    "name",
    "family",
    "sort_value",
    "selection_score",
    "score",
    "sharpe",
    "total_return",
    "test_total_return",
    "max_drawdown",
)

SortKey = str | Callable[[dict[str, Any]], Any]


class _ScoutRuntimeTimeout(TimeoutError):
    """Internal timeout used to return control to ScoutRun."""


class ScoutRun:
    """Runtime contract for agent-authored batch scratch scouts.

    Strategy remains in the caller's candidates, scorer, and required
    ``sort_key``. The helper only owns streaming persistence, automatic resume,
    runtime limits, and compact summaries.
    """

    def __init__(self, name: str, output_dir: str | Path, /) -> None:
        self.name = str(name)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def manifest_path(self) -> Path:
        return self.output_dir / f"{self.name}.manifest.json"

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
        shared_dir = self._infer_shared_scratch_dir()
        if shared_dir is not None:
            return shared_dir / "scout_budget_state.json"
        return self.output_dir / "scout_budget_state.json"

    def run(
        self,
        candidates: Iterable[Any],
        scorer: Callable[[Any], dict[str, Any]],
        *,
        sort_key: SortKey,
    ) -> dict[str, Any]:
        if sort_key is None:
            raise TypeError("ScoutRun.run() requires sort_key.")

        round_budget = self._round_budget_snapshot()
        round_remaining = round_budget["remaining_seconds"]
        budget = DEFAULT_MAX_SECONDS
        budget_limited_by_round = False
        if round_remaining is not None:
            budget = min(DEFAULT_MAX_SECONDS, float(round_remaining))
            budget_limited_by_round = budget < DEFAULT_MAX_SECONDS

        self._write_manifest(candidates, sort_key=sort_key, round_budget=round_budget)
        completed_indices = self._completed_indices()
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
                effective_max_seconds=0.0,
                timeout_scope="round_budget",
                round_budget=round_budget,
            )
            summary = self._write_summary(
                status="budget_exhausted",
                sort_key=sort_key,
            )
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
            self._print_artifacts()
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

            remaining_seconds = max(budget - elapsed, 0.0)
            try:
                with _candidate_deadline(remaining_seconds):
                    row = self._score_candidate(index, candidate, scorer, sort_key)
            except _ScoutRuntimeTimeout:
                status = "budget_exhausted" if budget_limited_by_round else "timeout"
                timeout_scope = "round_budget" if budget_limited_by_round else "run"
                break
            self._append_jsonl(self.results_path, row)
            completed_indices.add(index)
            completed_this_run += 1

            now = time.monotonic()
            if now - last_progress >= DEFAULT_PROGRESS_INTERVAL_SECONDS:
                last_progress = now
                self._write_state(
                    status="running",
                    next_candidate_index=index + 1,
                    completed_count=len(completed_indices),
                    skipped_count=skipped,
                    elapsed_seconds=now - start_time,
                    effective_max_seconds=budget,
                    timeout_scope="",
                    round_budget=round_budget,
                )
                self._write_summary(status="running", sort_key=sort_key)
                print(
                    "scout_progress "
                    f"name={self.name} completed={len(completed_indices)} "
                    f"elapsed_seconds={round(now - start_time, 3)} "
                    f"results={self.results_path}"
                )

        elapsed = time.monotonic() - start_time
        next_index = len(completed_indices) if status == "completed" else (
            max(completed_indices) + 1 if completed_indices else 0
        )
        final_round_budget = self._record_round_budget(
            elapsed_seconds=elapsed,
            status=status,
            effective_max_seconds=budget,
        )
        state = self._write_state(
            status=status,
            next_candidate_index=next_index,
            completed_count=len(completed_indices),
            skipped_count=skipped,
            elapsed_seconds=elapsed,
            effective_max_seconds=budget,
            timeout_scope=timeout_scope,
            round_budget=final_round_budget,
        )
        summary = self._write_summary(
            status=status,
            sort_key=sort_key,
        )
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
        for rank, row in enumerate(summary.get("top", []), start=1):
            print(
                "scout_top "
                f"rank={rank} name={row.get('name', row.get('candidate_index'))} "
                f"family={row.get('family', '')} "
                f"score={row.get('sort_value')}"
            )
        self._print_artifacts()
        return {"state": state, "summary": summary}

    def _write_summary(
        self,
        *,
        status: str,
        sort_key: SortKey,
    ) -> dict[str, Any]:
        rows = self._read_results()
        ranked = _rank_rows(rows, sort_key)
        family_best: dict[str, dict[str, Any]] = {}
        family_stats: dict[str, dict[str, Any]] = {}
        for row in rows:
            family = str(row.get("family") or "unknown")
            stats = family_stats.setdefault(
                family,
                {"completed_count": 0, "sort_error_count": 0, "error_count": 0},
            )
            stats["completed_count"] += 1
            if row.get("status") == "sort_error":
                stats["sort_error_count"] += 1
            if row.get("error"):
                stats["error_count"] += 1
        for row in ranked:
            family = str(row.get("family") or "unknown")
            if family not in family_best:
                family_best[family] = _summary_row(row, keys=FAMILY_BEST_ROW_KEYS)
        payload = {
            "name": self.name,
            "status": status,
            "completed_count": len(rows),
            "sortable_count": len(ranked),
            "sort_key": _sort_key_label(sort_key),
            "top": [
                {"rank": rank, **_summary_row(row, keys=SUMMARY_ROW_KEYS)}
                for rank, row in enumerate(ranked[:DEFAULT_TOP_K], start=1)
            ],
            "family_best": family_best,
            "family_stats": family_stats,
        }
        self._write_json(self.summary_path, payload)
        return payload

    def _score_candidate(
        self,
        index: int,
        candidate: Any,
        scorer: Callable[[Any], dict[str, Any]],
        sort_key: SortKey,
    ) -> dict[str, Any]:
        try:
            result = scorer(candidate)
            if not isinstance(result, dict):
                raise TypeError("Scout scorer must return a dict.")
        except _ScoutRuntimeTimeout:
            raise
        except Exception as exc:
            result = {
                "name": _candidate_name(candidate, index),
                "family": _candidate_family(candidate),
                "status": "error",
                "error": "candidate_error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
        row = _compact_result_row(
            candidate_index=index,
            candidate=candidate,
            result=result,
        )
        if row.get("status") == "error":
            return row
        try:
            row["sort_value"] = _json_safe_scalar(_sort_value(row, sort_key))
        except _ScoutRuntimeTimeout:
            raise
        except Exception as exc:
            row["status"] = "sort_error"
            row["error"] = "sort_key_error"
            row["error_type"] = type(exc).__name__
            row["error_message"] = str(exc)
        return row

    def _write_manifest(
        self,
        candidates: Iterable[Any],
        *,
        sort_key: SortKey,
        round_budget: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "candidate_count": _candidate_count(candidates),
            "runtime_policy": {
                "max_seconds": DEFAULT_MAX_SECONDS,
                "round_budget_seconds": DEFAULT_ROUND_BUDGET_SECONDS,
                "top_k": DEFAULT_TOP_K,
                "sort_key": _sort_key_label(sort_key),
            },
            "artifacts": self._artifact_paths(),
            "round_budget": round_budget,
            "started_at": _now_epoch(),
        }
        self.results_path.touch(exist_ok=True)
        self._write_json(self.manifest_path, payload)
        print(
            "scout_manifest "
            f"name={self.name} candidate_count={payload['candidate_count']} "
            f"max_seconds={DEFAULT_MAX_SECONDS} "
            f"round_budget_remaining={round_budget['remaining_seconds']} "
            f"sort_key={payload['runtime_policy']['sort_key']}"
        )
        print(f"artifacts manifest={self.manifest_path}")
        return payload

    def _artifact_paths(self) -> dict[str, str]:
        return {
            "manifest": str(self.manifest_path),
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
        effective_max_seconds: float,
        timeout_scope: str,
        round_budget: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "status": status,
            "next_candidate_index": int(next_candidate_index),
            "completed_count": int(completed_count),
            "skipped_count": int(skipped_count),
            "elapsed_seconds": round(float(elapsed_seconds), 3),
            "effective_max_seconds": round(float(effective_max_seconds), 3),
            "timeout_scope": timeout_scope,
            "round_budget": round_budget,
            "artifacts": self._artifact_paths(),
            "updated_at": _now_epoch(),
        }
        self._write_json(self.state_path, payload)
        return payload

    def _round_budget_snapshot(self) -> dict[str, Any]:
        recorded_rounds = self._recorded_round_count()
        key = f"recorded_rounds:{recorded_rounds}"
        state = self._read_round_budget_state()
        round_state = (state.get("rounds") or {}).get(key) or {}
        used = round(float(round_state.get("used_seconds") or 0.0), 3)
        remaining = max(round(DEFAULT_ROUND_BUDGET_SECONDS - used, 3), 0.0)
        return {
            "round_key": key,
            "recorded_rounds": recorded_rounds,
            "budget_seconds": round(DEFAULT_ROUND_BUDGET_SECONDS, 3),
            "used_seconds": used,
            "remaining_seconds": remaining,
            "state_path": str(self.round_budget_path),
        }

    def _record_round_budget(
        self,
        *,
        elapsed_seconds: float,
        status: str,
        effective_max_seconds: float,
    ) -> dict[str, Any]:
        snapshot = self._round_budget_snapshot()
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
        round_state["used_seconds"] = used
        round_state["remaining_seconds"] = max(
            round(DEFAULT_ROUND_BUDGET_SECONDS - used, 3),
            0.0,
        )
        round_state["runs"] = list(round_state.get("runs") or [])
        round_state["runs"].append(
            {
                "name": self.name,
                "status": status,
                "elapsed_seconds": round(elapsed, 3),
                "effective_max_seconds": round(float(effective_max_seconds), 3),
                "results": str(self.results_path),
                "state": str(self.state_path),
                "summary": str(self.summary_path),
                "updated_at": _now_epoch(),
            }
        )
        state["round_budget_seconds"] = round(DEFAULT_ROUND_BUDGET_SECONDS, 3)
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
        for path in (self.output_dir, *self.output_dir.parents):
            if (
                (path / "branches").is_dir()
                and (path / "events.tsv").exists()
                and (path / "exploration_path.md").exists()
            ):
                return path
        for path in (self.output_dir, *self.output_dir.parents):
            if (path / "branches").is_dir() and path.name != "scratch":
                return path
        return None

    def _infer_shared_scratch_dir(self) -> Path | None:
        session_dir = self._infer_session_dir()
        if session_dir is None:
            return None
        scratch_dir = session_dir / "scratch"
        if scratch_dir.exists() or self.output_dir == scratch_dir or scratch_dir in self.output_dir.parents:
            scratch_dir.mkdir(parents=True, exist_ok=True)
            return scratch_dir
        return None

    def _print_artifacts(self) -> None:
        print(
            "artifacts "
            f"manifest={self.manifest_path} results={self.results_path} "
            f"state={self.state_path} summary={self.summary_path} "
            f"round_budget={self.round_budget_path}"
        )

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _rank_rows(rows: list[dict[str, Any]], sort_key: SortKey) -> list[dict[str, Any]]:
    sortable = [
        dict(row)
        for row in rows
        if row.get("status") != "sort_error" and not row.get("error")
    ]
    sortable.sort(key=lambda row: _sort_value(row, sort_key), reverse=True)
    return sortable


@contextmanager
def _candidate_deadline(seconds: float):
    if seconds <= 0:
        raise _ScoutRuntimeTimeout("scout runtime budget exhausted")
    if not hasattr(signal, "SIGALRM") or not hasattr(signal, "setitimer"):
        yield
        return

    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, 0.0)

    def _handle_timeout(signum, frame):  # noqa: ARG001
        raise _ScoutRuntimeTimeout("scout runtime budget exhausted")

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.setitimer(signal.ITIMER_REAL, max(float(seconds), 0.001))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, previous_timer[0], previous_timer[1])


def _sort_value(row: dict[str, Any], sort_key: SortKey) -> Any:
    if isinstance(sort_key, str):
        if sort_key not in row:
            raise KeyError(f"sort_key field missing: {sort_key}")
        value = row[sort_key]
    else:
        value = sort_key(row)
    if value is None:
        raise ValueError("sort_key returned None")
    return value


def _sort_key_label(sort_key: SortKey) -> str:
    if isinstance(sort_key, str):
        return sort_key
    name = getattr(sort_key, "__name__", "")
    return name or "callable"


def _candidate_count(candidates: Iterable[Any]) -> int | None:
    try:
        return len(candidates)  # type: ignore[arg-type]
    except TypeError:
        return None


def _candidate_family(candidate: Any) -> str:
    mapping = _object_mapping(candidate)
    return str(
        mapping.get("family")
        or mapping.get("category")
        or mapping.get("group")
        or mapping.get("label")
        or "unknown"
    )


def _candidate_name(candidate: Any, index: int) -> str:
    mapping = _object_mapping(candidate)
    return str(mapping.get("name") or mapping.get("label") or index)


def _compact_result_row(
    *,
    candidate_index: int,
    candidate: Any,
    result: dict[str, Any],
) -> dict[str, Any]:
    candidate_dict = _object_mapping(candidate)
    result_dict = _object_mapping(result)
    row: dict[str, Any] = {
        "candidate_index": int(candidate_index),
        "name": str(
            result_dict.get("name")
            or candidate_dict.get("name")
            or result_dict.get("label")
            or candidate_dict.get("label")
            or candidate_index
        ),
        "family": str(
            result_dict.get("family")
            or result_dict.get("category")
            or result_dict.get("group")
            or candidate_dict.get("family")
            or candidate_dict.get("category")
            or candidate_dict.get("group")
            or candidate_dict.get("label")
            or "unknown"
        ),
    }
    for key in SCOUT_STATUS_KEYS:
        if key in result_dict:
            row[key] = _compact_value(result_dict[key])

    for key in SCOUT_METRIC_KEYS:
        value = result_dict.get(key)
        if value is None and key in candidate_dict:
            value = candidate_dict.get(key)
        if value is not None:
            row[key] = _compact_metric(value)

    params, omitted_keys = _extract_explicit_params(candidate_dict, result_dict)
    if params:
        row["params"] = params
    if omitted_keys:
        row["omitted_param_keys"] = omitted_keys
    return row


def _extract_explicit_params(
    candidate: dict[str, Any],
    result: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    params: dict[str, Any] = {}
    omitted: set[str] = set()
    _merge_explicit_params(params, omitted, candidate.get("params"), source="candidate.params")
    _merge_explicit_params(params, omitted, result.get("params"), source="result.params")
    _record_omitted_runtime_fields(omitted, candidate, source="candidate")
    _record_omitted_runtime_fields(omitted, result, source="result")
    return params, sorted(omitted)


def _merge_explicit_params(
    target: dict[str, Any],
    omitted: set[str],
    source_params: Any,
    *,
    source: str,
) -> None:
    if source_params is None:
        return
    if not isinstance(source_params, dict):
        omitted.add(source)
        return
    for key, value in source_params.items():
        compact = _param_value(value)
        if compact is None:
            omitted.add(str(key))
            continue
        target[str(key)] = compact


def _record_omitted_runtime_fields(
    omitted: set[str],
    source_dict: dict[str, Any],
    *,
    source: str,
) -> None:
    for key, value in source_dict.items():
        if key in SCOUT_IDENTITY_KEYS or key in SCOUT_METRIC_KEYS or key in SCOUT_STATUS_KEYS:
            continue
        if key in {"candidate", "result", "params"}:
            continue
        omitted_key = str(key)
        if omitted_key in omitted:
            omitted_key = f"{source}.{omitted_key}"
        omitted.add(omitted_key)


def _object_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        mapped = value.to_dict()
        return mapped if isinstance(mapped, dict) else {}
    return {}


def _summary_row(row: dict[str, Any], *, keys: tuple[str, ...]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key in keys:
        if key not in row:
            continue
        value = row[key]
        if key == "params":
            value = _compact_value(value)
        payload[key] = value
    return payload


def _compact_metric(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(value, 6)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return _compact_value(value)
    return round(parsed, 6)


def _param_value(value: Any) -> Any:
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (TypeError, ValueError):
            pass
    try:
        encoded = json.dumps(value, sort_keys=True)
    except (TypeError, ValueError):
        return None
    if len(encoded.encode("utf-8")) > MAX_PARAM_VALUE_JSON_BYTES:
        return None
    return value


def _compact_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, str):
        if len(value) <= 160:
            return value
        return f"{value[:157]}..."
    if isinstance(value, (list, tuple)):
        compact_values = [_compact_value(item) for item in list(value)[:12]]
        if len(value) > 12:
            compact_values.append(f"...(+{len(value) - 12})")
        return compact_values
    if isinstance(value, dict):
        compact_dict: dict[str, Any] = {}
        for key in sorted(value, key=str)[:24]:
            compact = _compact_value(value[key])
            if compact is not None:
                compact_dict[str(key)] = compact
        if len(value) > 24:
            compact_dict["_truncated_keys"] = len(value) - 24
        return compact_dict
    if hasattr(value, "item"):
        try:
            return _compact_value(value.item())
        except (TypeError, ValueError):
            pass
    return repr(value)[:160]


def _json_safe_scalar(value: Any) -> Any:
    compact = _compact_value(value)
    if isinstance(compact, (bool, int, float, str)):
        return compact
    return repr(compact)[:160]


def _now_epoch() -> float:
    return round(time.time(), 3)
