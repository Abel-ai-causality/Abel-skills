"""Graph frontier CLI command handlers."""

from __future__ import annotations

import argparse

from abel_invest.narrative_core.contracts.constants import EVENTS_HEADER, GRAPH_FRONTIER_FILENAME
from abel_invest.narrative_core.evidence import graph_frontier
from abel_invest.narrative_core.io import SessionLock, _now, append_tsv_row
from abel_invest.narrative_core.rendering.session_rendering import render_session
from abel_invest.narrative_core.session_lifecycle import resolve_workspace_arg_path


def handle_frontier_command(args: argparse.Namespace) -> int:
    session = resolve_workspace_arg_path(args.session).resolve()
    if args.frontier_command == "status":
        graph_frontier.print_graph_frontier_status(session)
        return 0
    if args.frontier_command == "expand":
        current = graph_frontier.load_graph_frontier(session)
        graph_release = current.get("graph_release")
        typed_release = isinstance(graph_release, dict)
        anchor = (
            str(args.node or "").strip()
            if typed_release
            else graph_frontier.normalize_graph_node_ref(args.node)
        )
        if not anchor:
            raise RuntimeError("frontier expand requires a graph node such as AAPL.price")
        if typed_release and anchor not in {
            str(node.get("node_id") or "").strip()
            for node in current.get("nodes") or []
            if isinstance(node, dict)
        }:
            raise RuntimeError(
                "V4 frontier expansion requires the exact canonical node ID already "
                f"present in the frontier: {anchor}"
            )
        expansion_kwargs = {"mode": args.mode, "limit": args.limit}
        if typed_release:
            expansion_kwargs["graph_release"] = graph_release
        payload = graph_frontier.fetch_live_graph_expansion(anchor, **expansion_kwargs)
        with SessionLock(session):
            current = graph_frontier.load_graph_frontier(session)
            updated, expansion = graph_frontier.merge_graph_frontier_expansion(
                current,
                payload,
                anchor_node=anchor,
                mode=args.mode,
                limit=args.limit,
            )
            graph_frontier.write_graph_frontier(session, updated)
            append_tsv_row(
                session / "events.tsv",
                EVENTS_HEADER,
                {
                    "timestamp": _now(),
                    "event": "frontier_expanded",
                    "branch_id": "",
                    "round_id": "",
                    "mode": args.mode,
                    "verdict": "",
                    "decision": "",
                    "description": (
                        f"Expanded graph frontier at {anchor}: "
                        f"{len(expansion.get('new_nodes') or [])} new nodes, "
                        f"{len(expansion.get('updated_nodes') or [])} updated nodes"
                    ),
                    "artifact_path": GRAPH_FRONTIER_FILENAME,
                },
            )
            render_session(session)
        print(
            f"Expanded {anchor}: new_nodes: {len(expansion.get('new_nodes') or [])}, "
            f"updated_nodes: {len(expansion.get('updated_nodes') or [])}"
        )
        graph_frontier.print_graph_frontier_status(session)
        print("")
        print("From here:")
        print(f"  review graph_frontier.json under {session}")
        print("  update exploration_path.md if this expansion changes the next candidate or search axis")
        print("  create or revise branch.yaml only after naming the candidate question this expansion answered")
        return 0
    raise RuntimeError(f"Unknown frontier command: {args.frontier_command}")
