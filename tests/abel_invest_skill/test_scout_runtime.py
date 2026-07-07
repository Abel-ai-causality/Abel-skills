from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from abel_invest.narrative_core import scout_runtime
from abel_invest.narrative_core.scout_runtime import ScoutRun


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_scout_runtime_exposes_minimal_stability_wrapper_api(tmp_path):
    scout = ScoutRun("first_look", tmp_path)

    assert scout.manifest_path.name == "first_look.manifest.json"
    assert scout.results_path.name == "first_look.results.jsonl"
    assert scout.state_path.name == "first_look.state.json"
    assert not hasattr(scout_runtime, "DEFAULT_MAX_SECONDS")
    assert not hasattr(scout, "summary_path")
    assert not hasattr(scout, "round_budget_path")
    assert not hasattr(scout_runtime, "DEFAULT_TOP_K")
    assert not hasattr(scout_runtime, "DEFAULT_FAMILY_TOP_K")
    assert not hasattr(scout_runtime, "DEFAULT_ROUND_BUDGET_SECONDS")
    assert not hasattr(scout_runtime, "ScoutEstimate")
    assert not hasattr(scout_runtime, "ScoutFamilyBudget")
    assert not hasattr(scout, "write_dry_run")
    assert not hasattr(scout, "write_summary")

    with pytest.raises(TypeError):
        ScoutRun(name="first_look", output_dir=tmp_path)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        ScoutRun("first_look", tmp_path, max_seconds=1)  # type: ignore[call-arg]


def test_scout_run_writes_flat_streamed_rows_manifest_and_state(tmp_path, capsys):
    scout = ScoutRun("first_look", tmp_path)
    candidates = [{"name": f"c{i}", "score": i} for i in range(3)]

    result = scout.run(
        candidates,
        lambda candidate: {
            "name": candidate["name"],
            "family": "graph",
            "score": candidate["score"],
            "sharpe": 1.23456789 + candidate["score"],
            "mode": "avg",
        },
    )

    rows = _jsonl(scout.results_path)
    manifest = json.loads(scout.manifest_path.read_text(encoding="utf-8"))
    state = json.loads(scout.state_path.read_text(encoding="utf-8"))

    assert result["state"]["status"] == "completed"
    assert manifest["candidate_count"] == 3
    assert "runtime_policy" not in manifest
    assert set(manifest["artifacts"]) == {"manifest", "results", "state"}
    assert len(rows) == 3
    assert rows[0] == {
        "i": 0,
        "family": "graph",
        "mode": "avg",
        "name": "c0",
        "score": 0,
        "sharpe": 1.234568,
    }
    assert "ok" not in rows[0]
    assert "status" not in rows[0]
    assert "sort_value" not in rows[0]
    assert "candidate" not in rows[0]
    assert "result" not in rows[0]
    assert state["completed_count"] == 3
    assert state["skipped_count"] == 0
    assert "effective_max_seconds" not in state
    assert state["artifacts"] == manifest["artifacts"]
    assert not (tmp_path / "first_look.summary.json").exists()
    assert not (tmp_path / "scout_budget_state.json").exists()

    output = capsys.readouterr().out
    assert "scout_manifest name=first_look candidate_count=3" in output
    assert "scout_complete name=first_look status=completed" in output
    assert "scout_family" not in output
    assert "scout_top" not in output
    assert "summary=" not in output
    assert "round_budget" not in output
    assert "max_seconds" not in output


def test_scout_run_writes_compact_error_row_without_ok_flag(tmp_path):
    scout = ScoutRun("first_look", tmp_path)

    scout.run(
        [{"name": "bad"}],
        lambda candidate: (_ for _ in ()).throw(ValueError("broken")),
    )

    rows = _jsonl(scout.results_path)
    assert rows == [{"i": 0, "name": "bad", "error": "ValueError: broken"}]
    assert "ok" not in rows[0]
    assert "status" not in rows[0]


def test_scout_run_automatic_resume_skips_completed_candidates(tmp_path, monkeypatch):
    monkeypatch.setattr(scout_runtime, "_MAX_SECONDS", 0.025)
    scout = ScoutRun("first_look", tmp_path)
    candidates = [{"name": f"c{i}", "score": i} for i in range(5)]

    def slow_score(candidate):
        time.sleep(0.01)
        return {"name": candidate["name"], "score": candidate["score"]}

    first = scout.run(candidates, slow_score)
    assert first["state"]["status"] == "timeout"
    first_rows = _jsonl(scout.results_path)
    assert 1 <= len(first_rows) < len(candidates)

    monkeypatch.setattr(scout_runtime, "_MAX_SECONDS", 1.0)
    second = scout.run(candidates, slow_score)

    rows = _jsonl(scout.results_path)
    assert [row["i"] for row in rows] == list(range(5))
    assert second["state"]["status"] == "completed"
    assert second["state"]["skipped_count"] == len(first_rows)


def test_scout_results_keep_scorer_fields_flat_and_compact(tmp_path):
    scout = ScoutRun("first_look", tmp_path)

    scout.run(
        [{"name": "candidate_a"}],
        lambda candidate: {
            "name": candidate["name"],
            "sharpe": 1.23456789,
            "total_return": 0.987654321,
            "max_drawdown": -0.123456789,
            "members": [f"driver_{index}" for index in range(30)],
            "note": "x" * 200,
        },
    )

    row = _jsonl(scout.results_path)[0]
    assert set(row) == {
        "i",
        "name",
        "sharpe",
        "total_return",
        "max_drawdown",
        "members",
        "note",
    }
    assert row["sharpe"] == 1.234568
    assert row["total_return"] == 0.987654
    assert row["max_drawdown"] == -0.123457
    assert len(row["members"]) == 25
    assert row["members"][-1] == "...(+6)"
    assert row["note"].endswith("...")


def test_experiment_loop_documents_minimal_scout_runtime_hook():
    repo_root = Path(__file__).resolve().parents[2]
    reference = repo_root / "skills" / "abel-invest" / "references" / "experiment-loop.md"
    text = reference.read_text(encoding="utf-8")

    assert "Use a compact scored scout to choose, not just describe" in text
    assert "roughly 5 minutes" in text
    assert "still making progress" in text
    assert "then rank what looks worth" in text
    assert "formal validation before broad" in text
    assert "recorded work" in text
    assert "scratch work evaluates a set of" in text
    assert "candidate variants to choose what to validate" in text
    assert "from abel_invest.narrative_core.scout_runtime import ScoutRun" in text
    assert "ScoutRun(name, scratch).run(candidates, scorer)" in text
    assert "result" in text
    assert "rows" in text
    assert "stream to disk" in text
    assert "available rows as the current scout output" in text
    assert "timeout/resume" not in text
    assert "reading\nback or reordering already" in text.lower()
    assert "scored results does not need another" in text
    assert "promote the" in text.lower()
    assert "script still owns" not in text.lower()
    assert "continuing private" not in text
    assert "sort_key" not in text
    assert "summary.json" not in text
    assert "family_top" not in text
    assert "round_budget_seconds" not in text
    assert "ScoutEstimate" not in text
    assert "write_dry_run" not in text
