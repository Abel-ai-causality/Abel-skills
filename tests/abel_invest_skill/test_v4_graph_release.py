"""V4 graph-release opt-in without changing the default V3 surface."""

from __future__ import annotations

import json
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

from abel_edge.plugins.abel.graph_driver import describe_v4_node
from abel_edge.plugins.abel.graph_release import GraphReleaseConfig
from abel_invest.narrative_core.commands import main
from abel_invest.narrative_core.contracts.branch_spec import (
    branch_dependencies_payload,
    branch_selected_graph_nodes,
    branch_selected_input_entries,
    build_default_branch_spec,
)
from abel_invest.narrative_core.contracts.constants import GRAPH_RELEASE_FILENAME
from abel_invest.narrative_core.evidence import graph_frontier
from abel_invest.narrative_core.session_lifecycle import init_branch_dir
from abel_invest.narrative_core.session_lifecycle import init_session_dir
from abel_invest.narrative_core.command_handlers import branch as branch_handler
from abel_invest.narrative_core.runtime.context import build_branch_context


NODE_ID = "health.openfda.drug.events:event_count#96bc3e82"
_RELEASE_CONFIG = GraphReleaseConfig.from_mapping(
    {
        "contract": "abel-edge.graph-release/v1",
        "provider": "abel",
        "graph_ref": {
            "graph_id": "abel-main",
            "graph_version": "CausalNodeV4",
        },
    }
)
RELEASE = _RELEASE_CONFIG.payload
RELEASE_SHA256 = _RELEASE_CONFIG.sha256


def _v4_discovery(target_node: str = "ABG.price") -> dict:
    target_ref = describe_v4_node(target_node)
    parent = describe_v4_node(NODE_ID)
    parent["source_rank"] = 1
    return {
        "contract": "abel-edge.graph-discovery/v2",
        "ticker": target_ref["ticker"],
        "target_asset": target_ref["ticker"],
        "target_node": target_node,
        "target_ref": target_ref,
        "source": "abel_live",
        "mode": "all",
        "K_discovery": 1,
        "created_at": "2026-08-16T00:00:00+00:00",
        "graph_release": RELEASE,
        "graph_release_sha256": RELEASE_SHA256,
        "parents": [parent],
        "blanket_new": [],
        "children": [],
    }


def test_v4_frontier_preserves_exact_typed_node_and_branch_selection(tmp_path):
    frontier = graph_frontier.graph_frontier_from_discovery_payload(
        _v4_discovery(),
        backtest_start="2020-01-01",
        expansion_mode="all",
        expansion_limit=10,
    )

    assert frontier["schema_version"] == 2
    assert frontier["graph_release"] == RELEASE
    assert frontier["graph_release_sha256"] == RELEASE_SHA256
    assert frontier["target_ref"]["node_id"] == "ABG.price"
    parent = next(node for node in frontier["nodes"] if node["node_id"] == NODE_ID)
    assert parent["asset"] == ""
    assert parent["field"] == "value"
    assert parent["family"] == "health.openfda.drug.events"
    assert parent["source_rank"] == 1
    assert parent["driver_ref"]["node_id"] == NODE_ID

    session = tmp_path / "research" / "abg" / "abg-v4"
    session.mkdir(parents=True)
    branch = init_branch_dir(session, "canonical")
    spec = build_default_branch_spec(
        branch=branch,
        discovery=graph_frontier.graph_frontier_to_discovery(frontier),
        readiness={},
        graph_frontier=frontier,
    )

    assert branch_selected_graph_nodes(spec) == [NODE_ID]
    entries = branch_selected_input_entries(spec)
    assert entries[0]["node_id"] == NODE_ID
    assert entries[0]["driver_ref"]["kind"] == "canonical_node"
    assert entries[0]["driver_ref_sha256"] == describe_v4_node(NODE_ID)[
        "driver_ref_sha256"
    ]


def test_init_session_v4_freezes_release_and_passes_it_to_edge(
    tmp_path,
    monkeypatch,
):
    release_path = tmp_path / "v4.json"
    release_path.write_text(json.dumps(RELEASE), encoding="utf-8")
    observed = []

    def fake_fetch_live_graph_frontier(
        ticker: str,
        *,
        limit: int,
        backtest_start: str,
        graph_release: dict | None = None,
    ) -> dict:
        observed.append(graph_release)
        return graph_frontier.graph_frontier_from_discovery_payload(
            _v4_discovery(),
            backtest_start=backtest_start,
            expansion_mode="all",
            expansion_limit=limit,
        )

    monkeypatch.setattr(
        graph_frontier,
        "fetch_live_graph_frontier",
        fake_fetch_live_graph_frontier,
    )
    monkeypatch.setattr(
        "abel_invest.narrative_core.session_lifecycle.refresh_data_readiness",
        lambda **_: {},
    )
    monkeypatch.setattr(
        "abel_invest.narrative_core.command_handlers.session.ensure_sample_strategy_context",
        lambda **_: {"status": "unavailable"},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "abel-invest",
            "init-session",
            "--ticker",
            "ABG",
            "--exp-id",
            "abg-v4",
            "--root",
            str(tmp_path / "research"),
            "--allow-outside-workspace",
            "--graph-release",
            str(release_path),
        ],
    )

    assert main() == 0
    session = tmp_path / "research" / "abg" / "abg-v4"
    assert observed == [RELEASE]
    assert json.loads((session / GRAPH_RELEASE_FILENAME).read_text(encoding="utf-8")) == RELEASE


def test_default_v3_discovery_call_does_not_inject_graph_release(monkeypatch):
    observed = []

    def fake_discover_graph_payload(ticker, *, mode, limit):
        observed.append((ticker, mode, limit))
        return {
            "ticker": ticker,
            "target_asset": ticker,
            "target_node": f"{ticker}.price",
            "source": "abel_live",
            "mode": mode,
            "K_discovery": 0,
            "parents": [],
            "blanket_new": [],
            "children": [],
        }

    monkeypatch.setattr(
        "abel_edge.plugins.abel.discover.discover_graph_payload",
        fake_discover_graph_payload,
    )
    monkeypatch.setattr(
        "abel_edge.plugins.abel.credentials.require_api_key",
        lambda: "test",
    )

    graph_frontier.fetch_live_graph_frontier(
        "AAPL",
        limit=10,
        backtest_start="2020-01-01",
    )

    assert observed == [("AAPL", "all", 10)]


def test_live_v4_discovery_preserves_requested_dotted_ticker_identity(
    tmp_path,
    monkeypatch,
):
    def fake_discover_graph_payload(
        ticker,
        *,
        mode,
        limit,
        graph_release=None,
    ):
        assert (ticker, mode, limit, graph_release) == (
            "000858.SZ",
            "all",
            10,
            RELEASE,
        )
        return _v4_discovery("000858.SZ.price")

    monkeypatch.setattr(
        "abel_edge.plugins.abel.discover.discover_graph_payload",
        fake_discover_graph_payload,
    )
    monkeypatch.setattr(
        "abel_edge.plugins.abel.credentials.require_api_key",
        lambda: "test",
    )

    frontier = graph_frontier.fetch_live_graph_frontier(
        "000858.SZ",
        limit=10,
        backtest_start="2020-01-01",
        graph_release=RELEASE,
    )
    discovery = graph_frontier.graph_frontier_to_discovery(frontier)
    branch = (
        tmp_path
        / "research"
        / "000858.sz"
        / "000858.sz-v4"
        / "branches"
        / "canonical"
    )
    branch.mkdir(parents=True)
    spec = build_default_branch_spec(
        branch=branch,
        discovery=discovery,
        readiness={},
        graph_frontier=frontier,
    )
    dependencies = branch_dependencies_payload(
        branch=branch,
        branch_spec=spec,
        target="000858.SZ",
        selected_inputs=[],
        requested_start="2020-01-01",
    )

    assert frontier["target_asset"] == "000858.SZ"
    assert frontier["target_node"] == "000858.SZ.price"
    assert discovery["ticker"] == "000858.SZ"
    assert spec["target"] == "000858.SZ"
    assert spec["target_node"] == "000858.SZ.price"
    assert dependencies["target_node"] == "000858.SZ.price"
    assert dependencies["version"] == 2


def test_prepare_v4_branch_materializes_canonical_feed_through_edge(
    tmp_path,
    monkeypatch,
):
    session = init_session_dir("ABG", "abg-v4", tmp_path / "research")
    frontier = graph_frontier.graph_frontier_from_discovery_payload(
        _v4_discovery(),
        backtest_start="2020-01-01",
        expansion_mode="all",
        expansion_limit=10,
    )
    graph_frontier.write_graph_frontier(session, frontier)
    branch = init_branch_dir(session, "canonical")
    spec = build_default_branch_spec(
        branch=branch,
        discovery=graph_frontier.graph_frontier_to_discovery(frontier),
        readiness={},
        graph_frontier=frontier,
    )
    spec["data_requirements"]["end"] = "2025-06-29"
    from abel_invest.narrative_core.contracts.branch_spec import write_branch_spec

    write_branch_spec(branch, spec)

    def fake_subprocess_run(command, cwd=None, capture_output=None, text=None, env=None):
        output_path = Path(command[command.index("--output-json") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "adapter": "abel",
                    "timeframe": "1d",
                    "profile": "daily",
                    "results": [
                        {
                            "symbol": "ABG",
                            "ok": True,
                            "row_count": 100,
                            "available_range": {
                                "start": "2020-01-01",
                                "end": "2026-05-28",
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    point_spec = {
        "contract": "abel-edge.point-in-time-series/v1",
        "series_id": NODE_ID,
        "source": {
            "adapter": "abel",
            "request": {
                "node_id": NODE_ID,
                "retrieval_mode": "node_series",
                "graph_ref": RELEASE["graph_ref"],
            },
        },
        "schema": {
            "event_time_field": "event_time",
            "available_at_field": "timestamp",
            "value_field": "value",
        },
        "materialization": {
            "frequency": "irregular",
            "timezone": "UTC",
            "missing_policy": "none",
            "alignment_policy": "asof",
        },
        "transforms": [],
        "availability": {"mode": "explicit"},
        "provenance": {"source_receipt_sha256": "c" * 64},
    }
    monkeypatch.setattr(branch_handler.subprocess, "run", fake_subprocess_run)
    monkeypatch.setattr(
        branch_handler,
        "_prepare_canonical_series_specs",
        lambda **_: {NODE_ID: point_spec},
    )

    assert branch_handler.prepare_branch_inputs(
        Namespace(
            branch=str(branch),
            python_bin=sys.executable,
            cache_limit=400,
            verbose=False,
            audit=False,
        )
    ) == 0

    manifest = json.loads(
        (branch / "inputs" / "data_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["version"] == 2
    canonical = next(feed for feed in manifest["feeds"] if feed["kind"] == "point_in_time_series")
    assert canonical["graph_node_id"] == NODE_ID
    assert canonical["driver_ref"]["kind"] == "canonical_node"
    assert canonical["series_spec"] == point_spec
    assert canonical["series_receipt_sha256"] == "c" * 64
    assert canonical["name"].startswith("graph_node_")
    context = build_branch_context(
        branch=branch,
        session=session,
        discovery=graph_frontier.graph_frontier_to_discovery(frontier),
        readiness={},
        round_id="r001",
        backtest_start="2020-01-01",
    )
    runtime_feed = context["_feeds"][canonical["name"]]
    assert runtime_feed["kind"] == "point_in_time_series"
    assert runtime_feed["series_spec"] == point_spec
    assert runtime_feed["source_start"] == "2020-01-01"
    assert runtime_feed["source_end"] == "2025-06-29"


def test_frontier_expand_preserves_v4_node_ids_and_release(
    tmp_path,
    monkeypatch,
):
    session = init_session_dir("ABG", "abg-v4-expand", tmp_path / "research")
    frontier = graph_frontier.graph_frontier_from_discovery_payload(
        _v4_discovery(),
        backtest_start="2020-01-01",
        expansion_mode="all",
        expansion_limit=10,
    )
    graph_frontier.write_graph_frontier(session, frontier)
    child_node = "macro.fred:GDP#quarterly"
    observed = []

    def fake_fetch_live_graph_expansion(
        anchor_node: str,
        *,
        mode: str,
        limit: int,
        graph_release: dict | None = None,
    ) -> dict:
        observed.append((anchor_node, graph_release))
        target_ref = describe_v4_node(anchor_node)
        return {
            "contract": "abel-edge.graph-discovery/v2",
            "ticker": "",
            "target_asset": "",
            "target_node": anchor_node,
            "target_ref": target_ref,
            "source": "abel_live",
            "graph_release": RELEASE,
            "graph_release_sha256": RELEASE_SHA256,
            "parents": [{**describe_v4_node(child_node), "source_rank": 2}],
            "blanket_new": [],
            "children": [],
            "created_at": "2026-08-16T00:01:00+00:00",
        }

    monkeypatch.setattr(
        graph_frontier,
        "fetch_live_graph_expansion",
        fake_fetch_live_graph_expansion,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "abel-invest",
            "frontier",
            "expand",
            "--session",
            str(session),
            "--node",
            NODE_ID,
            "--mode",
            "parents",
            "--limit",
            "5",
        ],
    )

    assert main() == 0
    assert observed == [(NODE_ID, RELEASE)]
    updated = graph_frontier.load_graph_frontier(session)
    child = next(node for node in updated["nodes"] if node["node_id"] == child_node)
    assert child["driver_ref"]["node_id"] == child_node
    assert child["family"] == "macro.fred"
    assert child["source_rank"] == 2
    assert updated["expansions"][-1]["anchor_node"] == NODE_ID
