"""Round-scoped strategy source inventory and snapshot helpers."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROUND_SOURCE_SNAPSHOT_SCHEMA = "abel-invest.round-source-snapshot/v1"
ROUND_SOURCE_SNAPSHOT_FILENAME = "source-snapshot.json"
ROUND_SOURCE_DIRNAME = "source"
SOURCE_VERSION_ROUND_SNAPSHOT = "round_snapshot"
SOURCE_VERSION_LEGACY_BRANCH_FALLBACK = "legacy_branch_fallback"

DENYLISTED_STRATEGY_PARTS = {
    ".git",
    ".abel-runtime",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "inputs",
    "outputs",
    "promotions",
    "rounds",
    "strategy_artifacts",
    "venv",
}
DENYLISTED_STRATEGY_FILENAMES = {
    ".env",
    "branch_state.json",
    "id_rsa",
    "id_rsa.pub",
    "results.tsv",
    "state_intent.json",
}
DENYLISTED_STRATEGY_SUFFIXES = {
    ".key",
    ".pem",
    ".pyc",
    ".pyo",
}
STRATEGY_EXTRA_FILE_SUFFIXES = {
    ".csv",
    ".json",
    ".joblib",
    ".npy",
    ".npz",
    ".pkl",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}
RUNTIME_CONTRACT_PATHS = (
    Path("branch.yaml"),
    Path("inputs/dependencies.json"),
    Path("inputs/data_manifest.json"),
    Path("inputs/runtime_profile.json"),
    Path("inputs/execution_constraints.json"),
)


class StrategySourceError(RuntimeError):
    """A stable machine-readable strategy source failure."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class StrategySourceEntry:
    path: str
    bytes: int
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {"path": self.path, "bytes": self.bytes, "sha256": self.sha256}


@dataclass(frozen=True)
class PendingRoundSourceSnapshot:
    branch: Path
    round_id: str
    temporary_dir: Path
    final_dir: Path
    entries: tuple[StrategySourceEntry, ...]
    digest: str


@dataclass(frozen=True)
class StrategySourceResolution:
    workdir: Path
    source_path: Path
    mode: str
    snapshot_digest: str | None


def is_denylisted_strategy_source(relative: Path) -> bool:
    """Return whether a branch-relative file is excluded from strategy packaging."""

    if any(part in DENYLISTED_STRATEGY_PARTS for part in relative.parts):
        return True
    if relative.name in DENYLISTED_STRATEGY_FILENAMES:
        return True
    if relative.suffix in DENYLISTED_STRATEGY_SUFFIXES:
        return True
    if relative.name == "branch.yaml":
        return True
    return relative.suffix not in STRATEGY_EXTRA_FILE_SUFFIXES


def collect_strategy_source_entries(root: Path) -> tuple[StrategySourceEntry, ...]:
    """Inventory the exact strategy and runtime-contract files under ``root``."""

    root = root.resolve()
    if not root.is_dir():
        raise StrategySourceError(
            "strategy_source_root_missing",
            f"strategy source root is missing: {root}",
        )
    included: dict[str, Path] = {}
    runtime_paths = {path.as_posix() for path in RUNTIME_CONTRACT_PATHS}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        relative_text = relative.as_posix()
        is_runtime_contract = relative_text in runtime_paths
        if not is_runtime_contract and is_denylisted_strategy_source(relative):
            continue
        if path.is_symlink():
            resolved = _validated_source_file(path, root=root)
            included[relative_text] = resolved
            continue
        if path.is_file():
            included[relative_text] = path

    if "engine.py" not in included:
        raise StrategySourceError(
            "strategy_source_missing",
            f"strategy source is missing engine.py under {root}",
        )
    return tuple(
        StrategySourceEntry(
            path=relative,
            bytes=source.stat().st_size,
            sha256=_sha256_file(source),
        )
        for relative, source in sorted(included.items())
    )


def prepare_round_source_snapshot(
    branch: Path,
    round_id: str,
) -> PendingRoundSourceSnapshot:
    """Copy a stable pre-run source snapshot into a temporary round directory."""

    branch = branch.resolve()
    final_dir = branch / "rounds" / round_id
    _discard_uncommitted_snapshot(final_dir, branch=branch, round_id=round_id)
    if _path_present(final_dir):
        raise StrategySourceError(
            "round_source_snapshot_exists",
            f"round source snapshot already exists: {final_dir}",
        )

    entries = collect_strategy_source_entries(branch)
    digest = _entries_digest(entries)
    temporary_dir = final_dir.parent / f".{round_id}.{uuid.uuid4().hex}.tmp"
    source_root = temporary_dir / ROUND_SOURCE_DIRNAME
    try:
        for entry in entries:
            source = _validated_source_file(branch / entry.path, root=branch)
            destination = source_root / entry.path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        copied_entries = collect_strategy_source_entries(source_root)
        if copied_entries != entries:
            raise StrategySourceError(
                "strategy_source_changed_during_snapshot",
                "strategy source changed while the round snapshot was being copied",
            )
        current_entries = collect_strategy_source_entries(branch)
        if current_entries != entries:
            raise StrategySourceError(
                "strategy_source_changed_during_snapshot",
                "strategy source changed while the round snapshot was being copied",
            )
        index = {
            "schema": ROUND_SOURCE_SNAPSHOT_SCHEMA,
            "branchId": branch.name,
            "roundId": round_id,
            "digest": digest,
            "files": [entry.as_dict() for entry in entries],
        }
        (temporary_dir / ROUND_SOURCE_SNAPSHOT_FILENAME).write_text(
            json.dumps(index, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except Exception:
        shutil.rmtree(temporary_dir, ignore_errors=True)
        raise
    return PendingRoundSourceSnapshot(
        branch=branch,
        round_id=round_id,
        temporary_dir=temporary_dir,
        final_dir=final_dir,
        entries=entries,
        digest=digest,
    )


def verify_round_source_unchanged(pending: PendingRoundSourceSnapshot) -> None:
    """Fail when the live branch source changed while Edge evaluated it."""

    try:
        current_entries = collect_strategy_source_entries(pending.branch)
    except StrategySourceError as exc:
        raise StrategySourceError(
            "strategy_source_changed_during_round",
            f"strategy source became invalid while Abel Edge evaluated the round: {exc}",
        ) from exc
    if current_entries != pending.entries:
        raise StrategySourceError(
            "strategy_source_changed_during_round",
            "strategy source changed while Abel Edge was evaluating the round",
        )


def publish_round_source_snapshot(pending: PendingRoundSourceSnapshot) -> Path:
    """Atomically make a prepared snapshot visible for the recorded round."""

    if _path_present(pending.final_dir):
        raise StrategySourceError(
            "round_source_snapshot_exists",
            f"refusing to overwrite round source history: {pending.final_dir}",
        )
    pending.final_dir.parent.mkdir(parents=True, exist_ok=True)
    pending.temporary_dir.rename(pending.final_dir)
    return pending.final_dir


def cleanup_pending_round_source_snapshot(pending: PendingRoundSourceSnapshot) -> None:
    shutil.rmtree(pending.temporary_dir, ignore_errors=True)


def resolve_round_strategy_source(
    branch: Path, round_id: str
) -> StrategySourceResolution:
    """Resolve a selected round to a validated snapshot or the legacy branch root."""

    branch = branch.resolve()
    snapshot_dir = branch / "rounds" / round_id
    if not _path_present(snapshot_dir):
        source_path = branch / "engine.py"
        if not source_path.is_file():
            raise StrategySourceError(
                "strategy_source_missing",
                f"legacy strategy source is missing: {source_path}",
            )
        return StrategySourceResolution(
            workdir=branch,
            source_path=source_path,
            mode=SOURCE_VERSION_LEGACY_BRANCH_FALLBACK,
            snapshot_digest=None,
        )
    if snapshot_dir.is_symlink() or not snapshot_dir.is_dir():
        raise _invalid_snapshot(
            f"round snapshot path is not a directory: {snapshot_dir}"
        )

    index_path = snapshot_dir / ROUND_SOURCE_SNAPSHOT_FILENAME
    source_root = snapshot_dir / ROUND_SOURCE_DIRNAME
    if (
        not index_path.is_file()
        or index_path.is_symlink()
        or not source_root.is_dir()
        or source_root.is_symlink()
    ):
        raise _invalid_snapshot(f"round snapshot is incomplete: {snapshot_dir}")
    if any(path.is_symlink() for path in source_root.rglob("*")):
        raise _invalid_snapshot(
            "round snapshot contains a symlink instead of copied file content"
        )
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _invalid_snapshot(f"round snapshot index is unreadable: {exc}") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schema") != ROUND_SOURCE_SNAPSHOT_SCHEMA
    ):
        raise _invalid_snapshot("round snapshot index schema is invalid")
    if payload.get("branchId") != branch.name or payload.get("roundId") != round_id:
        raise _invalid_snapshot(
            "round snapshot identity does not match the selected round"
        )
    indexed_entries = _parse_index_entries(payload.get("files"))
    expected_digest = _entries_digest(indexed_entries)
    if payload.get("digest") != expected_digest:
        raise _invalid_snapshot("round snapshot digest does not match its file index")
    try:
        actual_entries = collect_strategy_source_entries(source_root)
    except StrategySourceError as exc:
        raise _invalid_snapshot(str(exc)) from exc
    if actual_entries != indexed_entries:
        raise _invalid_snapshot("round snapshot files do not match the integrity index")
    return StrategySourceResolution(
        workdir=source_root,
        source_path=source_root / "engine.py",
        mode=SOURCE_VERSION_ROUND_SNAPSHOT,
        snapshot_digest=expected_digest,
    )


def _validated_source_file(path: Path, *, root: Path) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise StrategySourceError(
            "strategy_source_invalid",
            f"strategy source cannot be resolved: {path}: {exc}",
        ) from exc
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise StrategySourceError(
            "strategy_source_symlink_escape",
            f"strategy source escapes its branch through a symlink: {path}",
        ) from exc
    if not resolved.is_file():
        raise StrategySourceError(
            "strategy_source_invalid",
            f"strategy source is not a regular file: {path}",
        )
    return resolved


def _parse_index_entries(raw_entries: Any) -> tuple[StrategySourceEntry, ...]:
    if not isinstance(raw_entries, list) or not raw_entries:
        raise _invalid_snapshot("round snapshot file index is empty or invalid")
    entries: list[StrategySourceEntry] = []
    seen: set[str] = set()
    for raw in raw_entries:
        if not isinstance(raw, dict):
            raise _invalid_snapshot("round snapshot file index contains a non-object")
        path = str(raw.get("path") or "").strip()
        relative = Path(path)
        if not path or relative.is_absolute() or ".." in relative.parts:
            raise _invalid_snapshot(
                f"round snapshot contains an invalid file path: {path!r}"
            )
        if path in seen:
            raise _invalid_snapshot(
                f"round snapshot contains a duplicate file path: {path}"
            )
        seen.add(path)
        try:
            size = int(raw.get("bytes"))
        except (TypeError, ValueError) as exc:
            raise _invalid_snapshot(
                f"round snapshot file size is invalid: {path}"
            ) from exc
        sha256 = str(raw.get("sha256") or "").strip().lower()
        if (
            size < 0
            or len(sha256) != 64
            or any(char not in "0123456789abcdef" for char in sha256)
        ):
            raise _invalid_snapshot(f"round snapshot file metadata is invalid: {path}")
        entries.append(StrategySourceEntry(path=path, bytes=size, sha256=sha256))
    if [entry.path for entry in entries] != sorted(entry.path for entry in entries):
        raise _invalid_snapshot("round snapshot file index is not canonically ordered")
    return tuple(entries)


def _entries_digest(entries: tuple[StrategySourceEntry, ...]) -> str:
    canonical = json.dumps(
        [entry.as_dict() for entry in entries],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _discard_uncommitted_snapshot(
    final_dir: Path, *, branch: Path, round_id: str
) -> None:
    if not _path_present(final_dir):
        return
    session = branch.parent.parent
    recorded_in_branch = any(
        row.get("round_id") == round_id
        for row in _read_tsv_rows(branch / "results.tsv")
    )
    recorded_in_session = any(
        row.get("event") == "round_recorded"
        and row.get("branch_id") == branch.name
        and row.get("round_id") == round_id
        for row in _read_tsv_rows(session / "events.tsv")
    )
    recorded_in_dsr = any(
        str(row.get("branch_id") or "") == branch.name
        and str(row.get("round_id") or "") == round_id
        for row in _read_jsonl(session / "dsr_trials.jsonl")
    )
    if recorded_in_branch or recorded_in_session or recorded_in_dsr:
        return
    if final_dir.is_dir() and not final_dir.is_symlink():
        shutil.rmtree(final_dir)
    else:
        final_dir.unlink()


def _read_tsv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _invalid_snapshot(message: str) -> StrategySourceError:
    return StrategySourceError("round_source_snapshot_invalid", message)


def _path_present(path: Path) -> bool:
    return path.exists() or path.is_symlink()
