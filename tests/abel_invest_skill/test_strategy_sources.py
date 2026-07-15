from __future__ import annotations

import json
from pathlib import Path

import pytest

from abel_invest.narrative_core.strategy_sources import (
    ROUND_SOURCE_SNAPSHOT_FILENAME,
    SOURCE_VERSION_LEGACY_BRANCH_FALLBACK,
    SOURCE_VERSION_ROUND_SNAPSHOT,
    StrategySourceError,
    cleanup_pending_round_source_snapshot,
    prepare_round_source_snapshot,
    publish_round_source_snapshot,
    resolve_round_strategy_source,
    verify_round_source_unchanged,
)


def _write_branch_sources(branch: Path) -> None:
    branch.mkdir(parents=True)
    (branch / "engine.py").write_text("from helper import VALUE\n", encoding="utf-8")
    (branch / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
    (branch / "models").mkdir()
    (branch / "models" / "weights.json").write_text('{"weight": 1}\n', encoding="utf-8")
    (branch / "branch.yaml").write_text("target: TSLA\n", encoding="utf-8")
    (branch / "inputs").mkdir()
    for name in (
        "dependencies.json",
        "data_manifest.json",
        "runtime_profile.json",
        "execution_constraints.json",
    ):
        (branch / "inputs" / name).write_text("{}\n", encoding="utf-8")
    (branch / "inputs" / "prepared-cache.csv").write_text(
        "date,close\n", encoding="utf-8"
    )
    (branch / "outputs").mkdir()
    (branch / "outputs" / "edge-result.json").write_text("{}\n", encoding="utf-8")
    (branch / ".env").write_text("SECRET=value\n", encoding="utf-8")


def test_round_snapshot_preserves_strategy_and_runtime_files_only(
    tmp_path: Path,
) -> None:
    branch = tmp_path / "session" / "branches" / "candidate"
    _write_branch_sources(branch)

    pending = prepare_round_source_snapshot(branch, "round-001")
    verify_round_source_unchanged(pending)
    final_dir = publish_round_source_snapshot(pending)
    resolution = resolve_round_strategy_source(branch, "round-001")

    assert final_dir == branch / "rounds" / "round-001"
    assert resolution.mode == SOURCE_VERSION_ROUND_SNAPSHOT
    assert resolution.workdir == final_dir / "source"
    assert resolution.snapshot_digest
    assert (resolution.workdir / "engine.py").is_file()
    assert (resolution.workdir / "helper.py").is_file()
    assert (resolution.workdir / "models" / "weights.json").is_file()
    assert (resolution.workdir / "branch.yaml").is_file()
    assert (resolution.workdir / "inputs" / "runtime_profile.json").is_file()
    assert not (resolution.workdir / "inputs" / "prepared-cache.csv").exists()
    assert not (resolution.workdir / "outputs").exists()
    assert not (resolution.workdir / ".env").exists()
    index = json.loads(
        (final_dir / ROUND_SOURCE_SNAPSHOT_FILENAME).read_text(encoding="utf-8")
    )
    indexed_paths = {item["path"] for item in index["files"]}
    assert "helper.py" in indexed_paths
    assert "inputs/data_manifest.json" in indexed_paths


def test_round_snapshot_is_immutable_after_live_branch_changes(tmp_path: Path) -> None:
    branch = tmp_path / "session" / "branches" / "candidate"
    _write_branch_sources(branch)
    pending = prepare_round_source_snapshot(branch, "round-001")
    publish_round_source_snapshot(pending)

    (branch / "engine.py").write_text("VALUE = 2\n", encoding="utf-8")
    (branch / "helper.py").write_text("VALUE = 2\n", encoding="utf-8")

    resolution = resolve_round_strategy_source(branch, "round-001")
    assert (
        resolution.source_path.read_text(encoding="utf-8")
        == "from helper import VALUE\n"
    )
    assert (resolution.workdir / "helper.py").read_text(
        encoding="utf-8"
    ) == "VALUE = 1\n"


def test_round_snapshot_detects_live_source_changes_during_run(tmp_path: Path) -> None:
    branch = tmp_path / "session" / "branches" / "candidate"
    _write_branch_sources(branch)
    pending = prepare_round_source_snapshot(branch, "round-001")
    (branch / "helper.py").write_text("VALUE = 2\n", encoding="utf-8")

    with pytest.raises(StrategySourceError) as exc_info:
        verify_round_source_unchanged(pending)

    assert exc_info.value.code == "strategy_source_changed_during_round"
    cleanup_pending_round_source_snapshot(pending)


def test_round_snapshot_reports_deleted_engine_as_during_round_change(
    tmp_path: Path,
) -> None:
    branch = tmp_path / "session" / "branches" / "candidate"
    _write_branch_sources(branch)
    pending = prepare_round_source_snapshot(branch, "round-001")
    (branch / "engine.py").unlink()

    with pytest.raises(StrategySourceError) as exc_info:
        verify_round_source_unchanged(pending)

    assert exc_info.value.code == "strategy_source_changed_during_round"
    cleanup_pending_round_source_snapshot(pending)


@pytest.mark.parametrize("corruption", ["changed", "extra", "missing_index"])
def test_round_snapshot_corruption_fails_closed(
    tmp_path: Path, corruption: str
) -> None:
    branch = tmp_path / "session" / "branches" / "candidate"
    _write_branch_sources(branch)
    pending = prepare_round_source_snapshot(branch, "round-001")
    final_dir = publish_round_source_snapshot(pending)
    if corruption == "changed":
        (final_dir / "source" / "helper.py").write_text("VALUE = 3\n", encoding="utf-8")
    elif corruption == "extra":
        (final_dir / "source" / "extra.py").write_text(
            "EXTRA = True\n", encoding="utf-8"
        )
    else:
        (final_dir / ROUND_SOURCE_SNAPSHOT_FILENAME).unlink()

    with pytest.raises(StrategySourceError) as exc_info:
        resolve_round_strategy_source(branch, "round-001")

    assert exc_info.value.code == "round_source_snapshot_invalid"


def test_absent_round_snapshot_uses_legacy_branch_path(tmp_path: Path) -> None:
    branch = tmp_path / "session" / "branches" / "candidate"
    _write_branch_sources(branch)

    resolution = resolve_round_strategy_source(branch, "round-001")

    assert resolution.mode == SOURCE_VERSION_LEGACY_BRANCH_FALLBACK
    assert resolution.workdir == branch.resolve()
    assert resolution.source_path == branch.resolve() / "engine.py"
    assert resolution.snapshot_digest is None


def test_dangling_snapshot_path_is_invalid_not_legacy(tmp_path: Path) -> None:
    branch = tmp_path / "session" / "branches" / "candidate"
    _write_branch_sources(branch)
    rounds = branch / "rounds"
    rounds.mkdir()
    (rounds / "round-001").symlink_to(tmp_path / "missing-snapshot")

    with pytest.raises(StrategySourceError) as exc_info:
        resolve_round_strategy_source(branch, "round-001")

    assert exc_info.value.code == "round_source_snapshot_invalid"


def test_snapshot_directory_symlink_is_invalid(tmp_path: Path) -> None:
    branch = tmp_path / "session" / "branches" / "candidate"
    _write_branch_sources(branch)
    pending = prepare_round_source_snapshot(branch, "round-001")
    snapshot = publish_round_source_snapshot(pending)
    external_snapshot = tmp_path / "external-snapshot"
    snapshot.rename(external_snapshot)
    snapshot.symlink_to(external_snapshot, target_is_directory=True)

    with pytest.raises(StrategySourceError) as exc_info:
        resolve_round_strategy_source(branch, "round-001")

    assert exc_info.value.code == "round_source_snapshot_invalid"


def test_source_symlink_cannot_escape_branch(tmp_path: Path) -> None:
    branch = tmp_path / "session" / "branches" / "candidate"
    _write_branch_sources(branch)
    external = tmp_path / "external.json"
    external.write_text("{}\n", encoding="utf-8")
    (branch / "external.json").symlink_to(external)

    with pytest.raises(StrategySourceError) as exc_info:
        prepare_round_source_snapshot(branch, "round-001")

    assert exc_info.value.code == "strategy_source_symlink_escape"


def test_uncommitted_snapshot_can_be_replaced_but_dsr_record_protects_history(
    tmp_path: Path,
) -> None:
    session = tmp_path / "session"
    branch = session / "branches" / "candidate"
    _write_branch_sources(branch)
    first = prepare_round_source_snapshot(branch, "round-001")
    publish_round_source_snapshot(first)

    replacement = prepare_round_source_snapshot(branch, "round-001")
    cleanup_pending_round_source_snapshot(replacement)
    protected = prepare_round_source_snapshot(branch, "round-001")
    publish_round_source_snapshot(protected)
    (session / "dsr_trials.jsonl").write_text(
        json.dumps({"branch_id": "candidate", "round_id": "round-001"}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(StrategySourceError) as exc_info:
        prepare_round_source_snapshot(branch, "round-001")

    assert exc_info.value.code == "round_source_snapshot_exists"
