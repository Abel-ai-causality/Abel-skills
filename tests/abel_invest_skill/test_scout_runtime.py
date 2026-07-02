from __future__ import annotations

import json
import time
from pathlib import Path

from abel_invest.narrative_core.scout_runtime import (
    DEFAULT_MAX_SECONDS,
    DEFAULT_ROUND_BUDGET_SECONDS,
    ScoutEstimate,
    ScoutFamilyBudget,
    ScoutFamilyEstimate,
    ScoutRun,
    estimate_seconds,
)


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _session_scratch(tmp_path: Path) -> tuple[Path, Path]:
    session = tmp_path / "research" / "TSLA" / "demo-session"
    scratch = session / "scratch"
    (session / "branches").mkdir(parents=True)
    scratch.mkdir(parents=True)
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


def test_scout_dry_run_writes_estimate_without_executing_candidates(tmp_path, capsys):
    scout = ScoutRun(name="first_look", output_dir=tmp_path)
    estimate = ScoutEstimate(
        name="first_look",
        target="AAPL",
        candidate_count=120,
        row_count=800,
        feed_symbols=["AAPL", "AREB"],
        planned_families=["target", "graph"],
        budget_seconds=estimate_seconds(120, seconds_per_candidate=0.5),
        max_seconds=30,
    )

    payload = scout.write_dry_run(estimate)

    assert payload["within_budget"] is False
    assert "drop over-budget slow families" in payload["reduction_hint"]
    assert json.loads(scout.dry_run_path.read_text(encoding="utf-8"))["candidate_count"] == 120
    output = capsys.readouterr().out
    assert "scout_dry_run name=first_look target=AAPL" in output
    assert "budget_seconds=60.0" in output
    assert "estimated_seconds=" not in output
    assert "within_budget=false" in output
    assert not scout.results_path.exists()


def test_default_scout_budget_is_120_seconds():
    assert DEFAULT_MAX_SECONDS == 120.0
    assert DEFAULT_ROUND_BUDGET_SECONDS == 120.0
    assert ScoutEstimate(name="first_look", target="AAPL", candidate_count=1).max_seconds == 120.0
    assert ScoutRun(name="first_look", output_dir=Path.cwd()).max_seconds == 120.0
    assert ScoutRun(name="first_look", output_dir=Path.cwd()).round_budget_seconds == 120.0


def test_scout_dry_run_records_free_form_family_budget(tmp_path, capsys):
    scout = ScoutRun(name="first_look", output_dir=tmp_path)
    estimate = ScoutEstimate(
        name="first_look",
        target="TSLA",
        candidate_count=204,
        row_count=900,
        planned_families=["graph", "model"],
        family_breakdown=[
            ScoutFamilyBudget(
                label="sfi_graph_thresholds",
                candidate_count=180,
                budget_seconds=18.0,
                max_candidate_seconds=0.2,
                cost_traits=["graph", "vectorized"],
                reduction_axes=["lags", "thresholds"],
            ),
            {
                "label": "nonlinear_walk_forward_models",
                "candidate_count": 24,
                "budget_seconds": 90.0,
                "max_candidate_seconds": 18.0,
                "cost_traits": ["walk_forward", "slow_estimator"],
                "reduction_axes": ["model_types", "train_windows"],
            },
        ],
        budget_seconds=108.0,
        max_seconds=120.0,
        max_family_seconds=72.0,
        max_candidate_seconds=10.0,
    )

    payload = scout.write_dry_run(estimate)

    assert payload["within_budget"] is False
    assert payload["slowest_family"]["label"] == "nonlinear_walk_forward_models"
    assert payload["over_budget_families"][0]["label"] == "nonlinear_walk_forward_models"
    assert payload["slow_candidate_families"][0]["label"] == "nonlinear_walk_forward_models"
    assert payload["family_breakdown"][0]["budget_seconds"] == 18.0
    assert payload["family_breakdown"][0]["estimated_seconds"] == 18.0
    assert payload["budget_seconds"] == 108.0
    assert payload["estimated_seconds"] == 108.0
    output = capsys.readouterr().out
    assert "scout_family label=sfi_graph_thresholds" in output
    assert "budget_seconds=18.0" in output
    assert "scout_family label=nonlinear_walk_forward_models" in output


def test_scout_dry_run_records_round_budget_for_session_scratch(tmp_path, capsys):
    _, scratch = _session_scratch(tmp_path)
    scout = ScoutRun(name="first_look", output_dir=scratch, round_budget_seconds=7.5)
    estimate = ScoutEstimate(name="first_look", target="TSLA", candidate_count=3)

    payload = scout.write_dry_run(estimate)

    assert payload["round_budget"]["round_key"] == "recorded_rounds:0"
    assert payload["round_budget"]["budget_seconds"] == 7.5
    assert payload["round_budget"]["used_seconds"] == 0.0
    assert payload["round_budget"]["remaining_seconds"] == 7.5
    output = capsys.readouterr().out
    assert "round_budget_remaining=7.5" in output


def test_scout_runtime_exhausts_shared_round_budget_without_reexecuting(tmp_path):
    _, scratch = _session_scratch(tmp_path)
    first = ScoutRun(name="first_look", output_dir=scratch, round_budget_seconds=0.001)

    first.run(
        [{"name": "slow"}],
        lambda candidate: (time.sleep(0.003) or {"name": candidate["name"], "sharpe": 1.0}),
        max_seconds=1,
    )
    budget_state = json.loads(first.round_budget_path.read_text(encoding="utf-8"))
    round_state = budget_state["rounds"]["recorded_rounds:0"]
    assert round_state["used_seconds"] > 0.001
    assert round_state["remaining_seconds"] == 0.0

    executed = {"count": 0}
    second = ScoutRun(name="second_look", output_dir=scratch, round_budget_seconds=0.001)

    result = second.run(
        [{"name": "should_not_run"}],
        lambda candidate: executed.__setitem__("count", executed["count"] + 1) or {},
        max_seconds=1,
    )

    assert executed["count"] == 0
    assert result["state"]["status"] == "budget_exhausted"
    assert result["state"]["round_budget"]["round_key"] == "recorded_rounds:0"
    assert result["state"]["round_budget"]["remaining_seconds"] == 0.0


def test_scout_round_budget_resets_after_recorded_round(tmp_path):
    session, scratch = _session_scratch(tmp_path)
    scout = ScoutRun(name="first_look", output_dir=scratch, round_budget_seconds=0.001)
    scout.run(
        [{"name": "slow"}],
        lambda candidate: (time.sleep(0.003) or {"name": candidate["name"], "sharpe": 1.0}),
        max_seconds=1,
    )

    _record_round(session)
    next_scout = ScoutRun(name="after_branch", output_dir=scratch, round_budget_seconds=0.001)
    payload = next_scout.write_dry_run(
        ScoutEstimate(name="after_branch", target="TSLA", candidate_count=1)
    )

    assert payload["round_budget"]["round_key"] == "recorded_rounds:1"
    assert payload["round_budget"]["used_seconds"] == 0.0
    assert payload["round_budget"]["remaining_seconds"] == 0.001


def test_legacy_scout_family_estimate_alias_still_accepts_estimated_seconds():
    budget = ScoutFamilyEstimate(
        label="legacy_graph_grid",
        candidate_count=12,
        estimated_seconds=3.5,
    ).to_dict()

    assert budget["budget_seconds"] == 3.5
    assert budget["estimated_seconds"] == 3.5


def test_scout_estimate_accepts_legacy_seconds_but_normalizes_to_budget():
    estimate = ScoutEstimate(
        name="legacy",
        target="AAPL",
        candidate_count=7,
        estimated_seconds=12.5,
        max_seconds=120.0,
    )

    payload = estimate.to_dict()

    assert payload["budget_seconds"] == 12.5
    assert payload["estimated_seconds"] == 12.5


def test_scout_run_streams_results_and_writes_compact_summary(tmp_path, capsys):
    scout = ScoutRun(name="first_look", output_dir=tmp_path, top_k=2)

    result = scout.run(
        [{"name": "weak"}, {"name": "strong"}, {"name": "middle"}],
        lambda candidate: {
            "name": candidate["name"],
            "family": "graph",
            "sharpe": {"weak": 0.1, "strong": 2.0, "middle": 1.0}[candidate["name"]],
        },
    )

    rows = _jsonl(scout.results_path)
    assert [row["candidate_index"] for row in rows] == [0, 1, 2]
    assert result["state"]["status"] == "completed"
    assert result["summary"]["top"][0]["result"]["name"] == "strong"
    assert json.loads(scout.summary_path.read_text(encoding="utf-8"))["top"][1]["result"]["name"] == "middle"
    output = capsys.readouterr().out
    assert "scout_complete name=first_look status=completed" in output
    assert "scout_top rank=1 name=strong family=graph score=2.0" in output
    assert "weak" not in output


def test_scout_resume_skips_completed_candidates_after_timeout(tmp_path):
    scout = ScoutRun(name="first_look", output_dir=tmp_path, top_k=3)
    candidates = [{"name": f"c{i}", "score": i} for i in range(5)]

    def slow_score(candidate):
        time.sleep(0.01)
        return {"name": candidate["name"], "family": "graph", "sharpe": candidate["score"]}

    first = scout.run(candidates, slow_score, max_seconds=0.025)
    assert first["state"]["status"] == "timeout"
    first_rows = _jsonl(scout.results_path)
    assert 1 <= len(first_rows) < len(candidates)

    second = scout.run(candidates, slow_score, resume=True, max_seconds=1)

    rows = _jsonl(scout.results_path)
    assert [row["candidate_index"] for row in rows] == list(range(5))
    assert second["state"]["status"] == "completed"
    assert second["state"]["skipped_count"] == len(first_rows)
    assert second["summary"]["top"][0]["result"]["name"] == "c4"


def test_scout_runtime_times_out_single_slow_candidate(tmp_path):
    scout = ScoutRun(name="first_look", output_dir=tmp_path, top_k=3, max_candidate_seconds=0.02)
    candidates = [
        {"name": "fast", "family": "graph"},
        {"name": "slow", "family": "nonlinear_model"},
        {"name": "later", "family": "graph"},
    ]

    def score(candidate):
        if candidate["name"] == "slow":
            time.sleep(0.2)
        return {"name": candidate["name"], "family": candidate["family"], "sharpe": 1.0}

    result = scout.run(candidates, score, max_seconds=1)

    rows = _jsonl(scout.results_path)
    assert [row["candidate_index"] for row in rows] == [0, 1]
    assert result["state"]["status"] == "timeout"
    assert result["state"]["timeout_scope"] == "candidate"
    assert result["state"]["timeout_enforcement"] in {"signal", "cooperative"}
    assert rows[1]["result"]["error"] == "candidate_timeout"
    assert result["summary"]["family_stats"]["nonlinear_model"]["timeout_count"] == 1


def test_scout_runtime_records_bad_candidate_and_continues(tmp_path):
    scout = ScoutRun(name="first_look", output_dir=tmp_path, top_k=3)
    candidates = [
        {"name": "ok1", "family": "graph"},
        {"name": "bad", "family": "graph"},
        {"name": "ok2", "family": "target"},
    ]

    def score(candidate):
        if candidate["name"] == "bad":
            raise ValueError("bad rolling window")
        return {"name": candidate["name"], "family": candidate["family"], "sharpe": 1.0}

    result = scout.run(candidates, score)

    rows = _jsonl(scout.results_path)
    assert [row["candidate_index"] for row in rows] == [0, 1, 2]
    assert rows[1]["result"]["status"] == "error"
    assert rows[1]["result"]["error_type"] == "ValueError"
    assert result["state"]["status"] == "completed"
    assert result["summary"]["family_stats"]["graph"]["error_count"] == 1


def test_scout_summary_tracks_family_best(tmp_path):
    scout = ScoutRun(name="first_look", output_dir=tmp_path, top_k=2)

    scout.run(
        [{"name": "a"}, {"name": "b"}, {"name": "c"}],
        lambda candidate: {
            "name": candidate["name"],
            "family": "target" if candidate["name"] == "a" else "graph",
            "selection_score": {"a": 1.0, "b": 0.5, "c": 2.0}[candidate["name"]],
        },
    )

    summary = json.loads(scout.summary_path.read_text(encoding="utf-8"))
    assert summary["family_best"]["target"]["result"]["name"] == "a"
    assert summary["family_best"]["graph"]["result"]["name"] == "c"
    assert [row["result"]["name"] for row in summary["top"]] == ["c", "a"]


def test_experiment_loop_documents_minimal_scout_runtime_pattern():
    repo_root = Path(__file__).resolve().parents[2]
    reference = repo_root / "skills" / "abel-invest" / "references" / "experiment-loop.md"
    text = reference.read_text(encoding="utf-8")

    assert "ScoutFamilyBudget" in text
    assert "search-space declaration" in text
    assert "scout.write_dry_run(estimate)" in text
    assert "scout.run(" in text
    assert "max_candidate_seconds=args.max_candidate_seconds" in text
    assert "do not inspect the helper source" in text
    assert "do not run signature probes" in text
    assert "cumulative scout runtime budget" in text
    assert "recorded-round interval" in text
    assert "strategic continue, stop, or final-report" in text
    assert "after `run-branch` records a result" in text
