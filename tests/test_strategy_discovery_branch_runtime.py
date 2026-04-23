from __future__ import annotations

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

from abel_strategy_discovery import narrative_impl as ni


def _sample_discovery() -> dict:
    return {
        "ticker": "TSLA",
        "parents": [{"ticker": "AAPL"}, {"ticker": "MSFT"}],
        "blanket_new": [],
        "children": [],
        "backtest": {"start": "2020-01-01"},
    }


def _sample_readiness() -> dict:
    return {
        "results": [
            {
                "ticker": "TSLA",
                "status": "full",
                "usable": True,
                "covers_requested_start": True,
            },
            {
                "ticker": "AAPL",
                "status": "full",
                "usable": True,
                "covers_requested_start": True,
            },
            {
                "ticker": "MSFT",
                "status": "partial",
                "usable": True,
                "covers_requested_start": False,
            },
        ]
    }


def _write_runtime_files(branch: Path) -> None:
    ni.dependencies_path(branch).parent.mkdir(parents=True, exist_ok=True)
    ni.dependencies_path(branch).write_text(
        json.dumps(
            {
                "version": 1,
                "cache": {
                    "adapter": "abel",
                    "timeframe": "1d",
                    "profile": "daily",
                    "cache_root": "/tmp/cache",
                    "results": [
                        {
                            "symbol": "TSLA",
                            "ok": True,
                            "row_count": 120,
                            "available_range": {"start": "2020-01-01", "end": "2020-12-31"},
                        },
                        {
                            "symbol": "AAPL",
                            "ok": True,
                            "row_count": 120,
                            "available_range": {"start": "2020-01-01", "end": "2020-12-31"},
                        },
                        {
                            "symbol": "MSFT",
                            "ok": True,
                            "row_count": 90,
                            "available_range": {"start": "2020-03-01", "end": "2020-12-31"},
                        },
                    ],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    ni.runtime_profile_path(branch).write_text(
        json.dumps(
            {
                "profile": "daily",
                "target": "TSLA",
                "decision_event": "bar_close",
                "execution_delay_bars": 2,
                "return_basis": "close_to_close",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    ni.execution_constraints_path(branch).write_text(
        json.dumps({"long_only": False, "position_bounds": [-0.5, 0.5]}, indent=2),
        encoding="utf-8",
    )
    ni.data_manifest_path(branch).write_text(
        json.dumps(
            {
                "version": 1,
                "target": "TSLA",
                "selected_drivers": ["AAPL", "MSFT"],
                "feeds": [
                    {
                        "name": "primary",
                        "symbol": "TSLA",
                        "role": "target",
                        "adapter": "abel",
                        "timeframe": "1d",
                        "profile": "daily",
                        "cache_root": "/tmp/cache",
                    },
                    {
                        "name": "AAPL",
                        "symbol": "AAPL",
                        "role": "driver",
                        "adapter": "abel",
                        "timeframe": "1d",
                        "profile": "daily",
                        "cache_root": "/tmp/cache",
                    },
                    {
                        "name": "MSFT",
                        "symbol": "MSFT",
                        "role": "driver",
                        "adapter": "abel",
                        "timeframe": "1d",
                        "profile": "daily",
                        "cache_root": "/tmp/cache",
                    },
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    ni.probe_samples_path(branch).write_text(
        json.dumps(
            {
                "version": 1,
                "target": "TSLA",
                "requested_start": "2020-01-01",
                "sample_decision_dates": ["2020-01-01", "2020-06-17", "2020-12-31"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    ni.context_guide_path(branch).write_text(
        "# TSLA Branch Context Guide\n\n- use `ctx.target.series(\"close\")`\n",
        encoding="utf-8",
    )


def test_prepare_branch_inputs_writes_runtime_contract_artifacts(tmp_path, monkeypatch) -> None:
    session = ni.init_session_dir("TSLA", "tsla-v1", tmp_path / "research")
    ni.write_discovery(session, _sample_discovery())
    ni.write_readiness(session, _sample_readiness())
    branch = ni.init_branch_dir(session, "graph-v1")

    spec = ni.load_branch_spec(branch)
    spec["target"] = "TSLA"
    spec["requested_start"] = "2020-01-01"
    spec["selected_drivers"] = ["AAPL", "MSFT"]
    spec["position_bounds"] = [-1.0, 1.0]
    ni.write_branch_spec(branch, spec)

    calls = []

    def fake_subprocess_run(command, cwd=None, capture_output=None, text=None, env=None):
        calls.append(list(command))
        output_path = Path(command[command.index("--output-json") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "adapter": "abel",
                    "timeframe": "1d",
                    "profile": "daily",
                    "results": [
                        {
                            "symbol": "TSLA",
                            "ok": True,
                            "row_count": 150,
                            "available_range": {"start": "2020-01-01", "end": "2020-12-31"},
                        },
                        {
                            "symbol": "AAPL",
                            "ok": True,
                            "row_count": 150,
                            "available_range": {"start": "2020-01-01", "end": "2020-12-31"},
                        },
                        {
                            "symbol": "MSFT",
                            "ok": True,
                            "row_count": 110,
                            "available_range": {"start": "2020-03-01", "end": "2020-12-31"},
                        },
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(ni.subprocess, "run", fake_subprocess_run)

    result = ni.prepare_branch_inputs(
        Namespace(
            branch=str(branch),
            python_bin=sys.executable,
            cache_limit=400,
        )
    )

    assert result == 0
    assert calls and "warm-cache" in calls[0]
    assert ni.branch_inputs_ready(branch)

    runtime_profile = json.loads(ni.runtime_profile_path(branch).read_text(encoding="utf-8"))
    data_manifest = json.loads(ni.data_manifest_path(branch).read_text(encoding="utf-8"))
    probe_samples = json.loads(ni.probe_samples_path(branch).read_text(encoding="utf-8"))
    context_guide = ni.context_guide_path(branch).read_text(encoding="utf-8")

    assert runtime_profile["target"] == "TSLA"
    assert [feed["name"] for feed in data_manifest["feeds"]] == ["primary", "AAPL", "MSFT"]
    assert probe_samples["target"] == "TSLA"
    assert len(probe_samples["sample_decision_dates"]) >= 2
    assert "DecisionContext" in context_guide


def test_build_branch_context_prefers_prepared_runtime_inputs(tmp_path) -> None:
    session = ni.init_session_dir("TSLA", "tsla-v2", tmp_path / "research")
    discovery = _sample_discovery()
    readiness = _sample_readiness()
    ni.write_discovery(session, discovery)
    ni.write_readiness(session, readiness)
    branch = ni.init_branch_dir(session, "graph-v1")

    spec = ni.load_branch_spec(branch)
    spec["target"] = "TSLA"
    spec["selected_drivers"] = ["AAPL", "MSFT"]
    ni.write_branch_spec(branch, spec)
    _write_runtime_files(branch)

    context = ni.build_branch_context(
        branch=branch,
        session=session,
        discovery=discovery,
        readiness=readiness,
        round_id="round-001",
        backtest_start="2020-01-01",
    )

    assert context["runtime_profile"]["execution_delay_bars"] == 2
    assert context["_execution_constraints"]["position_bounds"] == [-0.5, 0.5]
    assert sorted(context["_feeds"].keys()) == ["AAPL", "MSFT", "primary"]
    assert context["_feeds"]["AAPL"]["symbol"] == "AAPL"
    assert context["data_manifest"]["selected_drivers"] == ["AAPL", "MSFT"]
