"""Small runtime wrapper for resumable Abel Invest scratch scouts."""

from __future__ import annotations

import json
import signal
import time
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from pathlib import Path
from typing import Any


DEFAULT_MAX_SECONDS = 180.0
DEFAULT_PROGRESS_INTERVAL_SECONDS = 30.0

MAX_COLLECTION_ITEMS = 24
MAX_STRING_CHARS = 160


class _ScoutRuntimeTimeout(TimeoutError):
    """Internal timeout used to return control to ScoutRun."""


class ScoutRun:
    """Stability wrapper for baseline-style batch scout scripts.

    The helper only owns streamed persistence, automatic resume, and an
    internal runtime timeout.
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

    def run(
        self,
        candidates: Iterable[Any],
        scorer: Callable[[Any], dict[str, Any]],
    ) -> dict[str, Any]:
        manifest = self._write_manifest(candidates)
        completed_indices = self._completed_indices()
        start_time = time.monotonic()
        last_progress = start_time
        completed_this_run = 0
        skipped = 0
        status = "completed"
        timeout_scope = ""

        for index, candidate in enumerate(candidates):
            if index in completed_indices:
                skipped += 1
                continue

            elapsed = time.monotonic() - start_time
            if elapsed >= DEFAULT_MAX_SECONDS:
                status = "timeout"
                timeout_scope = "run"
                break

            try:
                with _candidate_deadline(DEFAULT_MAX_SECONDS - elapsed):
                    row = self._score_candidate(index, candidate, scorer)
            except _ScoutRuntimeTimeout:
                status = "timeout"
                timeout_scope = "run"
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
                    timeout_scope="",
                )
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
        state = self._write_state(
            status=status,
            next_candidate_index=next_index,
            completed_count=len(completed_indices),
            skipped_count=skipped,
            elapsed_seconds=elapsed,
            timeout_scope=timeout_scope,
        )
        print(
            "scout_complete "
            f"name={self.name} status={status} "
            f"completed={completed_this_run} total_completed={len(completed_indices)} "
            f"elapsed_seconds={round(elapsed, 3)}"
        )
        self._print_artifacts()
        return {"manifest": manifest, "state": state}

    def _score_candidate(
        self,
        index: int,
        candidate: Any,
        scorer: Callable[[Any], dict[str, Any]],
    ) -> dict[str, Any]:
        try:
            result = scorer(candidate)
            if not isinstance(result, dict):
                raise TypeError("Scout scorer must return a dict.")
        except _ScoutRuntimeTimeout:
            raise
        except Exception as exc:
            row = {"i": int(index)}
            name = _candidate_name(candidate)
            if name is not None:
                row["name"] = name
            row["error"] = _compact_error(exc)
            return row

        row = {"i": int(index)}
        for key, value in result.items():
            if key == "i":
                continue
            row[str(key)] = _compact_value(value)
        return row

    def _write_manifest(self, candidates: Iterable[Any]) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "candidate_count": _candidate_count(candidates),
            "runtime_policy": {
                "max_seconds": DEFAULT_MAX_SECONDS,
            },
            "artifacts": self._artifact_paths(),
            "started_at": _now_epoch(),
        }
        self.results_path.touch(exist_ok=True)
        self._write_json(self.manifest_path, payload)
        print(
            "scout_manifest "
            f"name={self.name} candidate_count={payload['candidate_count']} "
            f"max_seconds={DEFAULT_MAX_SECONDS}"
        )
        print(f"artifacts manifest={self.manifest_path}")
        return payload

    def _artifact_paths(self) -> dict[str, str]:
        return {
            "manifest": str(self.manifest_path),
            "results": str(self.results_path),
            "state": str(self.state_path),
        }

    def _completed_indices(self) -> set[int]:
        indices: set[int] = set()
        for row in self._read_results():
            try:
                indices.add(int(row.get("i")))
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
        timeout_scope: str,
    ) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "status": status,
            "next_candidate_index": int(next_candidate_index),
            "completed_count": int(completed_count),
            "skipped_count": int(skipped_count),
            "elapsed_seconds": round(float(elapsed_seconds), 3),
            "effective_max_seconds": round(float(DEFAULT_MAX_SECONDS), 3),
            "timeout_scope": timeout_scope,
            "artifacts": self._artifact_paths(),
            "updated_at": _now_epoch(),
        }
        self._write_json(self.state_path, payload)
        return payload

    def _print_artifacts(self) -> None:
        print(
            "artifacts "
            f"manifest={self.manifest_path} results={self.results_path} "
            f"state={self.state_path}"
        )

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


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


def _candidate_count(candidates: Iterable[Any]) -> int | None:
    try:
        return len(candidates)  # type: ignore[arg-type]
    except TypeError:
        return None


def _candidate_name(candidate: Any) -> str | None:
    mapping = _object_mapping(candidate)
    name = mapping.get("name") or mapping.get("label")
    return str(name) if name is not None else None


def _object_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        mapped = value.to_dict()
        return mapped if isinstance(mapped, dict) else {}
    return {}


def _compact_error(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}"
    return text if len(text) <= MAX_STRING_CHARS else f"{text[: MAX_STRING_CHARS - 3]}..."


def _compact_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, str):
        return value if len(value) <= MAX_STRING_CHARS else f"{value[: MAX_STRING_CHARS - 3]}..."
    if isinstance(value, (list, tuple)):
        compact_values = [_compact_value(item) for item in list(value)[:MAX_COLLECTION_ITEMS]]
        if len(value) > MAX_COLLECTION_ITEMS:
            compact_values.append(f"...(+{len(value) - MAX_COLLECTION_ITEMS})")
        return compact_values
    if isinstance(value, dict):
        compact_dict: dict[str, Any] = {}
        for key in sorted(value, key=str)[:MAX_COLLECTION_ITEMS]:
            compact = _compact_value(value[key])
            if compact is not None:
                compact_dict[str(key)] = compact
        if len(value) > MAX_COLLECTION_ITEMS:
            compact_dict["_truncated_keys"] = len(value) - MAX_COLLECTION_ITEMS
        return compact_dict
    if hasattr(value, "item"):
        try:
            return _compact_value(value.item())
        except (TypeError, ValueError):
            pass
    return repr(value)[:MAX_STRING_CHARS]


def _now_epoch() -> float:
    return round(time.time(), 3)
