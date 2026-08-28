"""Cross-layer graph contract regressions for legacy V3 and typed V4."""

from __future__ import annotations

import pytest

from abel_edge.plugins.abel.graph_driver import describe_v4_node
from abel_edge.plugins.abel.graph_release import GraphReleaseConfig
from abel_invest.narrative_core.contracts.branch_spec import (
    branch_dependencies_payload,
    branch_selected_graph_nodes,
    branch_selected_input_entries,
    branch_selected_inputs,
    build_data_manifest_payload,
    build_default_branch_spec,
)
from abel_invest.narrative_core.evidence.graph_frontier import (
    graph_frontier_from_discovery_payload,
    graph_frontier_to_discovery,
)


def _release(graph_version: str, **graph_ref: str) -> GraphReleaseConfig:
    return GraphReleaseConfig.from_mapping(
        {
            "contract": "abel-edge.graph-release/v1",
            "provider": "abel",
            "graph_ref": {
                "graph_id": "abel-main",
                "graph_version": graph_version,
                **graph_ref,
            },
        }
    )


def _v4_payload(
    *,
    target_node: str = "BRK.B.price",
    parents: list[dict] | None = None,
    release: GraphReleaseConfig | None = None,
) -> dict:
    release = release or _release("CausalNodeV4")
    target_ref = describe_v4_node(target_node)
    return {
        "contract": "abel-edge.graph-discovery/v2",
        "ticker": target_ref["ticker"],
        "target_asset": target_ref["ticker"],
        "target_node": target_node,
        "target_ref": target_ref,
        "source": "abel_live",
        "created_at": "2026-08-28T00:00:00+00:00",
        "graph_release": release.payload,
        "graph_release_sha256": release.sha256,
        "parents": parents or [],
        "blanket_new": [],
        "children": [],
    }


def _frontier(payload: dict, *, expected_graph_release: dict | None = None) -> dict:
    return graph_frontier_from_discovery_payload(
        payload,
        backtest_start="2020-01-01",
        expansion_mode="all",
        expansion_limit=10,
        expected_graph_release=expected_graph_release,
    )


def test_explicit_v3_release_retains_provenance_but_stays_schema_v1(tmp_path):
    release = _release("CausalNodeV3", release_id="v3-frozen")
    payload = {
        "contract": "abel-edge.graph-discovery/v2",
        "ticker": "AAPL",
        "target_asset": "AAPL",
        "target_node": "AAPL.price",
        "source": "abel_live",
        "created_at": "2026-08-28T00:00:00+00:00",
        "graph_release": release.payload,
        "graph_release_sha256": release.sha256,
        "parents": [
            {
                "node_id": "MSFT.price",
                "ticker": "MSFT",
                "field": "price",
                "driver_ref": {"kind": "symbol", "symbol": "MSFT", "field": "close"},
            }
        ],
        "blanket_new": [],
        "children": [],
    }

    frontier = _frontier(payload, expected_graph_release=release.payload)
    assert frontier["schema_version"] == 1
    assert frontier["graph_release"] == release.payload
    assert frontier["graph_release_sha256"] == release.sha256
    assert "target_ref" not in frontier

    branch = tmp_path / "branches" / "v3"
    branch.mkdir(parents=True)
    spec = build_default_branch_spec(
        branch=branch,
        discovery=graph_frontier_to_discovery(frontier),
        readiness={},
        graph_frontier=frontier,
    )
    dependencies = branch_dependencies_payload(
        branch=branch,
        branch_spec=spec,
        target="AAPL",
        selected_inputs=branch_selected_inputs(spec),
        requested_start="2020-01-01",
    )

    assert dependencies["version"] == 1
    assert "selected_drivers" not in dependencies
    assert "graph_release" not in dependencies


def test_market_only_v4_uses_v2_artifacts_and_exact_dotted_symbol(tmp_path):
    release = _release("CausalNodeV4")
    market_parent = {**describe_v4_node("000858.SZ.volume"), "source_rank": 1}
    frontier = _frontier(
        _v4_payload(parents=[market_parent], release=release),
        expected_graph_release=release.payload,
    )
    branch = tmp_path / "branches" / "market-v4"
    branch.mkdir(parents=True)
    spec = build_default_branch_spec(
        branch=branch,
        discovery=graph_frontier_to_discovery(frontier),
        readiness={"results": [{"ticker": "000858.SZ", "status": "ready"}]},
        graph_frontier=frontier,
    )

    entries = branch_selected_input_entries(spec)
    assert spec["target_ref"]["node_id"] == "BRK.B.price"
    assert branch_selected_graph_nodes(spec) == ["000858.SZ.volume"]
    assert branch_selected_inputs(spec) == ["000858.SZ"]
    assert entries[0]["driver_ref"]["kind"] == "symbol"

    dependencies = branch_dependencies_payload(
        branch=branch,
        branch_spec=spec,
        target="BRK.B",
        selected_inputs=["000858.SZ"],
        requested_start="2020-01-01",
    )
    assert dependencies["version"] == 2
    assert dependencies["target_node"] == "BRK.B.price"
    assert dependencies["target_ref"] == spec["target_ref"]
    assert dependencies["selected_graph_nodes"] == ["000858.SZ.volume"]
    assert dependencies["selected_drivers"] == entries

    manifest = build_data_manifest_payload(
        target="BRK.B",
        target_node=dependencies["target_node"],
        selected_inputs=["000858.SZ"],
        selected_graph_nodes=dependencies["selected_graph_nodes"],
        selected_driver_entries=entries,
        graph_release=dependencies["graph_release"],
        graph_release_sha256=dependencies["graph_release_sha256"],
        target_ref=dependencies["target_ref"],
        cache_payload={
            "adapter": "abel",
            "timeframe": "1d",
            "profile": "daily",
            "results": [
                {"symbol": "BRK.B", "ok": True},
                {"symbol": "000858.SZ", "ok": True},
            ],
        },
        readiness={},
    )
    assert manifest["version"] == 2
    assert manifest["target_node"] == "BRK.B.price"
    assert manifest["target_ref"] == spec["target_ref"]
    assert manifest["selected_graph_nodes"] == ["000858.SZ.volume"]
    assert manifest["selected_drivers"] == entries
    assert [feed["graph_node_id"] for feed in manifest["feeds"]] == [
        "BRK.B.price",
        "000858.SZ.volume",
    ]
    assert all(feed["kind"] == "bars" for feed in manifest["feeds"])


def test_v4_target_projection_conflict_fails_closed():
    payload = _v4_payload()
    payload["target_node"] = "BRK.B"

    with pytest.raises(ValueError, match="target_node conflicts"):
        _frontier(payload)


def test_v4_session_target_rejects_canonical_node_identity():
    release = _release("CausalNodeV4")
    canonical_target = "macro.fred:GDP#quarterly"
    payload = {
        **_v4_payload(release=release),
        "ticker": "",
        "target_asset": "",
        "target_node": canonical_target,
        "target_ref": describe_v4_node(canonical_target),
    }

    with pytest.raises(ValueError, match="session targets must use a symbol"):
        _frontier(payload)


def test_v4_release_digest_drift_fails_closed():
    payload = _v4_payload()
    payload["graph_release_sha256"] = "f" * 64

    with pytest.raises(ValueError, match="digest does not match"):
        _frontier(payload)


def test_requested_and_returned_release_drift_fails_closed():
    returned = _release("CausalNodeV4", release_id="returned")
    requested = _release("CausalNodeV4", release_id="requested")

    with pytest.raises(ValueError, match="different graph release"):
        _frontier(
            _v4_payload(release=returned),
            expected_graph_release=requested.payload,
        )


def test_unknown_graph_version_fails_closed():
    payload = _v4_payload()
    payload["graph_release"] = {
        "contract": "abel-edge.graph-release/v1",
        "provider": "abel",
        "graph_ref": {
            "graph_id": "abel-main",
            "graph_version": "CausalNodeV5",
        },
    }

    with pytest.raises(ValueError, match="supported graph_version"):
        _frontier(payload)


def test_edge_to_invest_uses_one_dotted_v4_target_identity(monkeypatch):
    from abel_edge.plugins.abel import discover as edge_discover

    release = _release("CausalNodeV4")

    class StubClient:
        def discover_parents(self, *, node_id, limit, api_key, graph_ref):
            assert node_id == "BRK.B.price"
            assert graph_ref == release.graph_ref
            return [{"node_id": "000858.SZ.volume"}]

        def graph_provenance(self):
            return release.graph_ref

    monkeypatch.setattr(edge_discover, "require_api_key", lambda **_: "test")
    payload = edge_discover.discover_graph_payload(
        "BRK.B",
        mode="parents",
        graph_release=release,
        client=StubClient(),
    )
    frontier = _frontier(payload, expected_graph_release=release.payload)

    assert frontier["target_asset"] == "BRK.B"
    assert frontier["target_node"] == "BRK.B.price"
    assert frontier["target_ref"]["node_id"] == "BRK.B.price"
    assert {node["node_id"] for node in frontier["nodes"]} == {
        "BRK.B.price",
        "000858.SZ.volume",
    }
