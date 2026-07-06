from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from abel_invest.narrative_core import scout_runtime
from abel_invest.narrative_core.scout_runtime import (
    DEFAULT_MAX_SECONDS,
    DEFAULT_ROUND_BUDGET_SECONDS,
    DEFAULT_TOP_K,
    ScoutRun,
)


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _session_scratch(tmp_path: Path) -> tuple[Path, Path]:
    session = tmp_path / "research" / "TSLA" / "demo-session"
    scratch = session / "scratch"
    (session / "branches").mkdir(parents=True)
    scratch.mkdir(parents=True)
    (session / "events.tsv").write_text("ts\tevent\n", encoding="utf-8")
    (session / "exploration_path.md").write_text("# Exploration Path\n", encoding="utf-8")
    return session, scratch


def _record_round(session: Path, branch_id: str = "candidate") -> None:
    branch_dir = session / "branches" / branch_id
    branch_dir.mkdir(parents=True, exist_ok=True)
    results_path = branch_dir / "results.tsv"
    results_path.write_text(
        "round_id\tverdict\tscore\n"
        "round-001\tFAIL\t4/9\n",
        encoding="utf-8",
    )


def test_scout_runtime_exposes_only_simplified_api(tmp_path):
    scout = ScoutRun("first_look", tmp_path)

    assert scout.manifest_path.name == "first_look.manifest.json"
    assert DEFAULT_MAX_SECONDS == 120.0
    assert DEFAULT_ROUND_BUDGET_SECONDS == 120.0
    assert DEFAULT_TOP_K == 20
    assert not hasattr(scout_runtime, "ScoutEstimate")
    assert not hasattr(scout_runtime, "ScoutFamilyBudget")
    assert not hasattr(scout, "write_dry_run")
    assert not hasattr(scout, "write_summary")

    with pytest.raises(TypeError):
        ScoutRun(name="first_look", output_dir=tmp_path)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        ScoutRun("first_look", tmp_path, max_seconds=1)  # type: ignore[call-arg]


def test_scout_run_requires_sort_key_before_execution(tmp_path):
    executed = {"count": 0}

    def scorer(candidate):
        executed["count"] += 1
        return {"name": candidate["name"], "score": 1.0}

    with pytest.raises(TypeError):
        ScoutRun("first_look", tmp_path).run([{"name": "a"}], scorer)  # type: ignore[call-arg]

    assert executed["count"] == 0
    assert not (tmp_path / "first_look.results.jsonl").exists()


def test_scout_run_writes_manifest_streams_rows_and_sorts_top_20(tmp_path, capsys):
    scout = ScoutRun("first_look", tmp_path)
    candidates = [{"name": f"c{i}", "family": "graph", "score": i} for i in range(25)]

    result = scout.run(
        candidates,
        lambda candidate: {
            "name": candidate["name"],
            "family": candidate["family"],
            "score": candidate["score"],
            "params": {"lag": candidate["score"]},
        },
        sort_key="score",
    )

    rows = _jsonl(scout.results_path)
    summary = json.loads(scout.summary_path.read_text(encoding="utf-8"))
    manifest = json.loads(scout.manifest_path.read_text(encoding="utf-8"))

    assert result["state"]["status"] == "completed"
    assert manifest["candidate_count"] == 25
    assert manifest["runtime_policy"]["max_seconds"] == 120.0
    assert manifest["runtime_policy"]["round_budget_seconds"] == 120.0
    assert manifest["runtime_policy"]["top_k"] == 20
    assert manifest["runtime_policy"]["sort_key"] == "score"
    assert len(rows) == 25
    assert all("candidate" not in row and "result" not in row for row in rows)
    assert rows[24]["params"]["lag"] == 24
    assert summary["sort_key"] == "score"
    assert summary["sortable_count"] == 25
    assert len(summary["top"]) == 20
    assert [row["name"] for row in summary["top"][:3]] == ["c24", "c23", "c22"]
    assert summary["top"][0]["rank"] == 1
    assert "artifacts" not in summary
    assert "round_budget" not in summary
    assert "completed_at" not in summary["top"][0]
    assert "elapsed_seconds" not in summary["top"][0]
    assert "omitted_params" not in summary["top"][0]

    output = capsys.readouterr().out
    assert "scout_manifest name=first_look candidate_count=25" in output
    assert "scout_complete name=first_look status=completed" in output
    assert "scout_top rank=1 name=c24 family=graph score=24" in output
    assert "c0" not in output


def test_scout_run_accepts_callable_sort_key(tmp_path):
    scout = ScoutRun("first_look", tmp_path)

    result = scout.run(
        [{"name": "a"}, {"name": "b"}, {"name": "c"}],
        lambda candidate: {
            "name": candidate["name"],
            "family": "graph",
            "sharpe": {"a": 1.0, "b": 2.0, "c": 1.5}[candidate["name"]],
            "max_drawdown": {"a": -0.1, "b": -0.9, "c": -0.2}[candidate["name"]],
        },
        sort_key=lambda row: row["sharpe"] - abs(row["max_drawdown"]),
    )

    assert [row["name"] for row in result["summary"]["top"]] == ["c", "b", "a"]


def test_scout_run_records_sort_key_errors_and_keeps_single_summary_semantics(tmp_path):
    scout = ScoutRun("first_look", tmp_path)

    result = scout.run(
        [{"name": "ok"}, {"name": "missing"}],
        lambda candidate: (
            {"name": candidate["name"], "family": "graph", "score": 2.0}
            if candidate["name"] == "ok"
            else {"name": candidate["name"], "family": "graph", "sharpe": 1.0}
        ),
        sort_key="score",
    )

    rows = _jsonl(scout.results_path)
    assert rows[1]["status"] == "sort_error"
    assert rows[1]["error"] == "sort_key_error"
    assert result["summary"]["sortable_count"] == 1
    assert [row["name"] for row in result["summary"]["top"]] == ["ok"]
    assert "sample_rows" not in result["summary"]


def test_scout_run_automatic_resume_skips_completed_candidates(tmp_path, monkeypatch):
    monkeypatch.setattr(scout_runtime, "DEFAULT_MAX_SECONDS", 0.025)
    scout = ScoutRun("first_look", tmp_path)
    candidates = [{"name": f"c{i}", "score": i} for i in range(5)]

    def slow_score(candidate):
        time.sleep(0.01)
        return {"name": candidate["name"], "family": "graph", "score": candidate["score"]}

    first = scout.run(candidates, slow_score, sort_key="score")
    assert first["state"]["status"] == "timeout"
    first_rows = _jsonl(scout.results_path)
    assert 1 <= len(first_rows) < len(candidates)

    monkeypatch.setattr(scout_runtime, "DEFAULT_MAX_SECONDS", 1.0)
    second = scout.run(candidates, slow_score, sort_key="score")

    rows = _jsonl(scout.results_path)
    assert [row["candidate_index"] for row in rows] == list(range(5))
    assert second["state"]["status"] == "completed"
    assert second["state"]["skipped_count"] == len(first_rows)
    assert second["summary"]["top"][0]["name"] == "c4"


def test_scout_round_budget_is_internal_and_resets_after_recorded_round(tmp_path, monkeypatch):
    session, scratch = _session_scratch(tmp_path)
    monkeypatch.setattr(scout_runtime, "DEFAULT_ROUND_BUDGET_SECONDS", 0.001)
    first = ScoutRun("first_look", scratch)

    first.run(
        [{"name": "slow", "score": 1.0}],
        lambda candidate: (time.sleep(0.003) or {"name": candidate["name"], "score": 1.0}),
        sort_key="score",
    )
    budget_state = json.loads(first.round_budget_path.read_text(encoding="utf-8"))
    round_state = budget_state["rounds"]["recorded_rounds:0"]
    assert round_state["used_seconds"] > 0.001
    assert round_state["remaining_seconds"] == 0.0

    executed = {"count": 0}
    second = ScoutRun("second_look", scratch)
    result = second.run(
        [{"name": "should_not_run", "score": 1.0}],
        lambda candidate: executed.__setitem__("count", executed["count"] + 1)
        or {"name": candidate["name"], "score": 1.0},
        sort_key="score",
    )

    assert executed["count"] == 0
    assert result["state"]["status"] == "budget_exhausted"
    assert result["state"]["round_budget"]["round_key"] == "recorded_rounds:0"

    _record_round(session)
    next_scout = ScoutRun("after_branch", scratch)
    payload = next_scout.run(
        [{"name": "fresh", "score": 1.0}],
        lambda candidate: {"name": candidate["name"], "score": 1.0},
        sort_key="score",
    )

    assert payload["state"]["round_budget"]["round_key"] == "recorded_rounds:1"
    assert payload["state"]["status"] == "completed"


def test_scout_round_budget_is_shared_from_nested_scout_dirs(tmp_path, monkeypatch):
    session, scratch = _session_scratch(tmp_path)
    monkeypatch.setattr(scout_runtime, "DEFAULT_ROUND_BUDGET_SECONDS", 0.001)

    first = ScoutRun("first_look", scratch / "first_look_scout")
    first.run(
        [{"name": "slow", "score": 1.0}],
        lambda candidate: (time.sleep(0.003) or {"name": candidate["name"], "score": 1.0}),
        sort_key="score",
    )

    assert first.round_budget_path == scratch / "scout_budget_state.json"
    budget_state = json.loads(first.round_budget_path.read_text(encoding="utf-8"))
    assert budget_state["rounds"]["recorded_rounds:0"]["remaining_seconds"] == 0.0

    blocked = ScoutRun("second_look", scratch / "second_scout").run(
        [{"name": "blocked", "score": 1.0}],
        lambda candidate: {"name": candidate["name"], "score": 1.0},
        sort_key="score",
    )
    assert blocked["state"]["status"] == "budget_exhausted"
    assert blocked["state"]["round_budget"]["round_key"] == "recorded_rounds:0"

    _record_round(session)
    fresh = ScoutRun("after_branch", scratch / "after_branch_scout").run(
        [{"name": "fresh", "score": 1.0}],
        lambda candidate: {"name": candidate["name"], "score": 1.0},
        sort_key="score",
    )
    assert fresh["state"]["status"] == "completed"
    assert fresh["state"]["round_budget"]["round_key"] == "recorded_rounds:1"


def test_scout_results_persist_explicit_params_only(tmp_path):
    scout = ScoutRun("first_look", tmp_path)

    scout.run(
        [
            {
                "name": "candidate_a",
                "family": "graph",
                "params": {
                    "lag": 5,
                    "window": 20,
                    "members": [f"driver_{index}" for index in range(20)],
                },
                "payload": {"position": object()},
                "position": object(),
            }
        ],
        lambda candidate: {
            "name": candidate["name"],
            "family": candidate["family"],
            "params": {"threshold": 0.7},
            "payload": {"prediction": object()},
            "score": 1.0,
            "sharpe": 1.23456789,
            "total_return": 0.987654321,
            "max_drawdown": -0.123456789,
        },
        sort_key="score",
    )

    row = _jsonl(scout.results_path)[0]
    assert set(row) >= {
        "candidate_index",
        "name",
        "family",
        "score",
        "sharpe",
        "total_return",
        "max_drawdown",
        "params",
    }
    assert "candidate" not in row
    assert "result" not in row
    assert "elapsed_seconds" not in row
    assert "completed_at" not in row
    assert "omitted_params" not in row
    assert row["sharpe"] == 1.234568
    assert row["params"]["lag"] == 5
    assert row["params"]["window"] == 20
    assert row["params"]["threshold"] == 0.7
    assert len(row["params"]["members"]) == 20
    assert "position" not in row["params"]
    assert "payload" not in row["params"]
    assert row["omitted_param_keys"] == ["payload", "position", "result.payload"]

    summary = json.loads(scout.summary_path.read_text(encoding="utf-8"))
    top = summary["top"][0]
    assert "omitted_param_keys" not in top
    assert "completed_at" not in top
    assert "elapsed_seconds" not in top
    assert "params" in top


def test_experiment_loop_documents_required_scorer_sort_key_pattern():
    repo_root = Path(__file__).resolve().parents[2]
    reference = repo_root / "skills" / "abel-invest" / "references" / "experiment-loop.md"
    text = reference.read_text(encoding="utf-8")

    assert "Use a compact scored scout to choose, not just describe" in text
    assert "from abel_invest.narrative_core.scout_runtime import ScoutRun" in text
    assert "`ScoutRun` with an agent-owned scorer" in text
    assert "compact result rows stream to disk" in text
    assert "resumable artifacts" in text
    assert "survive interruptions" in text
    assert "sort_key" in text
    assert "agent-owned" in text
    assert "max_seconds" not in text
    assert "round_budget_seconds" not in text
    assert "ScoutEstimate" not in text
    assert "write_dry_run" not in text
