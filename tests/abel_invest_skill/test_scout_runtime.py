from __future__ import annotations

import json
import time
from pathlib import Path

from abel_invest.narrative_core.scout_runtime import (
    ScoutEstimate,
    ScoutRun,
    estimate_seconds,
)


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_scout_dry_run_writes_estimate_without_executing_candidates(tmp_path, capsys):
    scout = ScoutRun(name="first_look", output_dir=tmp_path)
    estimate = ScoutEstimate(
        name="first_look",
        target="AAPL",
        candidate_count=120,
        row_count=800,
        feed_symbols=["AAPL", "AREB"],
        planned_families=["target", "graph"],
        estimated_seconds=estimate_seconds(120, seconds_per_candidate=0.5),
        max_seconds=30,
    )

    payload = scout.write_dry_run(estimate)

    assert payload["within_budget"] is False
    assert "reduce candidate families" in payload["reduction_hint"]
    assert json.loads(scout.dry_run_path.read_text(encoding="utf-8"))["candidate_count"] == 120
    output = capsys.readouterr().out
    assert "scout_dry_run name=first_look target=AAPL" in output
    assert "within_budget=false" in output
    assert not scout.results_path.exists()


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

    assert "from abel_invest.narrative_core.scout_runtime import ScoutEstimate, ScoutRun" in text
    assert "scout.write_dry_run(estimate)" in text
    assert "scout.run(candidates, score_candidate, resume=args.resume" in text
    assert "do not inspect the helper source" in text
