"""Graph frontier discovery and expansion helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path

from abel_invest.narrative_core.contracts.branch_spec import (
    default_graph_node_id,
    normalize_graph_node_ref,
    ordered_unique_strings,
    split_graph_node_id,
)
from abel_invest.narrative_core.contracts.constants import (
    DEFAULT_BACKTEST_START,
    GRAPH_FRONTIER_FILENAME,
)
from abel_invest.narrative_core.contracts.graph_release import (
    discovery_graph_contract,
    resolve_graph_contract,
    validate_v4_node_descriptor,
    validate_v4_target_identity,
)
from abel_invest.narrative_core.evidence.frontier import increment_count, render_inline_counts
from abel_invest.narrative_core.io import _now
from abel_invest.workspace_core.doctor import build_auth_recovery_instruction, workspace_command
from abel_invest.workspace_core.edge_runtime import apply_effective_abel_env
from abel_invest.workspace_core.workspace import resolve_workspace_entry


def fetch_live_graph_frontier(
    ticker: str,
    *,
    limit: int,
    backtest_start: str,
    graph_release: dict | None = None,
) -> dict:
    requested_ticker = ticker.upper()
    try:
        from abel_edge.plugins.abel.credentials import (
            MissingAbelApiKeyError,
            require_api_key,
        )
        from abel_edge.plugins.abel.discover import discover_graph_payload
    except ImportError as exc:
        workspace_root, _ = resolve_workspace_entry()
        command_prefix = workspace_command(workspace_root, None) if workspace_root else "abel-invest"
        raise RuntimeError(
            "Live Abel discovery requires abel-edge with the Abel plugin installed. "
            f"Rerun the active Abel Invest bootstrap shim for {workspace_root or Path.cwd()}, "
            f"then retry `{command_prefix} init-session --ticker {ticker.upper()} --exp-id <exp-id>`."
        ) from exc
    workspace_root, _ = resolve_workspace_entry()
    if workspace_root is not None:
        apply_effective_abel_env(workspace_root)

    try:
        require_api_key()
    except MissingAbelApiKeyError as exc:
        command_prefix = workspace_command(workspace_root, None) if workspace_root else "abel-invest"
        raise RuntimeError(
            "init-session live graph discovery is blocked on Abel auth. "
            "No reusable auth was found. "
            f"{build_auth_recovery_instruction(workspace_root or Path.cwd())}\n\n"
            f"After auth is ready, retry `{command_prefix} init-session --ticker "
            f"{ticker.upper()} --exp-id <exp-id>`."
        ) from exc

    if graph_release is None:
        payload = discover_graph_payload(requested_ticker, mode="all", limit=limit)
    else:
        payload = discover_graph_payload(
            requested_ticker,
            mode="all",
            limit=limit,
            graph_release=graph_release,
        )
    frontier = graph_frontier_from_discovery_payload(
        dict(payload),
        backtest_start=backtest_start,
        expansion_mode="all",
        expansion_limit=limit,
        expected_graph_release=graph_release,
    )
    if frontier.get("schema_version") == 2 and frontier.get("target_asset") != requested_ticker:
        raise ValueError("V4 discovery returned a different target asset than requested")
    return frontier


def fetch_live_graph_expansion(
    anchor_node: str,
    *,
    mode: str,
    limit: int,
    graph_release: dict | None = None,
) -> dict:
    try:
        from abel_edge.plugins.abel.credentials import (
            MissingAbelApiKeyError,
            require_api_key,
        )
        from abel_edge.plugins.abel.discover import discover_graph_payload
    except ImportError as exc:
        workspace_root, _ = resolve_workspace_entry()
        command_prefix = workspace_command(workspace_root, None) if workspace_root else "abel-invest"
        raise RuntimeError(
            "Live Abel frontier expansion requires abel-edge with the Abel plugin installed. "
            f"Rerun the active Abel Invest bootstrap shim for {workspace_root or Path.cwd()}, "
            f"then retry `{command_prefix} frontier expand --session <session> --node {anchor_node}`."
        ) from exc
    workspace_root, _ = resolve_workspace_entry()
    if workspace_root is not None:
        apply_effective_abel_env(workspace_root)

    try:
        require_api_key()
    except MissingAbelApiKeyError as exc:
        raise RuntimeError(
            "frontier expand is blocked on Abel auth. "
            "No reusable auth was found. "
            f"{build_auth_recovery_instruction(workspace_root or Path.cwd())}"
        ) from exc

    if graph_release is None:
        payload = discover_graph_payload(anchor_node, mode=mode, limit=limit)
    else:
        payload = discover_graph_payload(
            anchor_node,
            mode=mode,
            limit=limit,
            graph_release=graph_release,
        )
    contract = discovery_graph_contract(payload, expected_release=graph_release)
    if contract.is_v4:
        _target_asset, target_node, _target_ref = _v4_target_identity(
            payload,
            require_symbol=False,
        )
        if target_node != str(anchor_node or "").strip():
            raise ValueError("V4 expansion returned a different target node than requested")
    return payload


def write_graph_frontier_from_discovery_payload(session: Path, discovery_data: dict) -> None:
    write_graph_frontier(
        session,
        graph_frontier_from_discovery_payload(
            discovery_data,
            backtest_start=(discovery_data.get("backtest") or {}).get("start", DEFAULT_BACKTEST_START),
            expansion_mode=str(discovery_data.get("mode") or "all"),
            expansion_limit=int(discovery_data.get("K_discovery") or 10),
        ),
    )


def graph_frontier_path(session: Path) -> Path:
    return session / GRAPH_FRONTIER_FILENAME


def load_graph_frontier(session: Path) -> dict:
    path = graph_frontier_path(session)
    if not path.exists():
        return build_pending_graph_frontier(
            session.parent.name.upper(),
            backtest_start=DEFAULT_BACKTEST_START,
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_graph_frontier(session: Path, frontier: dict) -> None:
    graph_frontier_path(session).write_text(
        json.dumps(frontier, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def print_graph_frontier_status(session: Path) -> None:
    frontier = load_graph_frontier(session)
    facts = graph_frontier_facts(frontier)
    print(f"Session: {session.name}")
    print(f"Graph frontier: {session / GRAPH_FRONTIER_FILENAME}")
    print(f"Target node: {facts['target_node']}")
    print(f"Source: {facts['source']}")
    print(f"Nodes: {facts['node_count']}")
    print(f"Expansions: {facts['expansion_count']}")
    print(f"Expanded anchors: {facts['expanded_anchor_count']}")
    print(f"Unexpanded nodes: {facts['unexpanded_node_count']}")
    print(f"Fields: {render_inline_counts(facts['field_counts'])}")
    print(f"Roles: {render_inline_counts(facts['role_counts'])}")
    print(
        "Search boundary: frontier coverage is context, not exhaustion; "
        "before stopping below target, check whether higher-ceiling search axes remain."
    )


def graph_frontier_facts(frontier: dict) -> dict[str, object]:
    nodes = [node for node in frontier.get("nodes") or [] if isinstance(node, dict)]
    expansions = [item for item in frontier.get("expansions") or [] if isinstance(item, dict)]
    expanded_anchors = {
        str(item.get("anchor_node") or "").strip()
        for item in expansions
        if str(item.get("anchor_node") or "").strip()
    }
    field_counts: dict[str, int] = {}
    role_counts: dict[str, int] = {}
    for node in nodes:
        increment_count(field_counts, str(node.get("field") or "unknown"))
        roles = node.get("discovery_roles") or ["unknown"]
        for role in roles:
            increment_count(role_counts, str(role or "unknown"))
    unexpanded = [
        node
        for node in nodes
        if str(node.get("node_id") or "") not in expanded_anchors
        and "target" not in set(str(role) for role in node.get("discovery_roles") or [])
    ]
    return {
        "target_node": str(frontier.get("target_node") or "unknown"),
        "source": str(frontier.get("source") or "unknown"),
        "node_count": len(nodes),
        "expansion_count": len(expansions),
        "expanded_anchor_count": len(expanded_anchors),
        "unexpanded_node_count": len(unexpanded),
        "field_counts": dict(sorted(field_counts.items())),
        "role_counts": dict(sorted(role_counts.items())),
    }


def build_pending_graph_frontier(ticker: str, *, backtest_start: str) -> dict:
    now = _now()
    target_asset = str(ticker or "").strip().upper()
    target_node = default_graph_node_id(target_asset)
    return {
        "schema_version": 1,
        "target_asset": target_asset,
        "target_node": target_node,
        "requested_window": {"start": backtest_start, "end": None},
        "source": "pending",
        "created_at": now,
        "updated_at": now,
        "nodes": [
            build_frontier_node(
                node_id=target_node,
                roles=["target"],
                discovered_from="session",
                depth=0,
                seen_at=now,
            )
        ],
        "expansions": [],
    }


def merge_graph_frontier_expansion(
    frontier: dict,
    payload: dict,
    *,
    anchor_node: str,
    mode: str,
    limit: int,
) -> tuple[dict, dict]:
    now = str(payload.get("created_at") or _now())
    graph_release = frontier.get("graph_release")
    contract = resolve_graph_contract(
        graph_release,
        graph_release_sha256=str(frontier.get("graph_release_sha256") or ""),
        require_sha256=graph_release is not None,
    )
    returned_contract = discovery_graph_contract(
        payload,
        expected_release=contract.release,
    )
    anchor_node = (
        str(anchor_node or "").strip()
        if contract.is_v4
        else normalize_graph_node_ref(anchor_node)
    )
    returned_target_ref = None
    if returned_contract.is_v4:
        _target_asset, returned_target, returned_target_ref = _v4_target_identity(
            payload,
            require_symbol=False,
        )
        if returned_target != anchor_node:
            raise ValueError("V4 expansion target conflicts with its anchor node")
    updated = dict(frontier)
    expected_schema = 2 if contract.is_v4 else 1
    if int(updated.get("schema_version") or expected_schema) != expected_schema:
        raise ValueError("frontier schema version conflicts with its graph release")
    updated.setdefault("schema_version", expected_schema)
    if contract.is_v4:
        if not str(updated.get("target_asset") or "").strip() or not str(
            updated.get("target_node") or ""
        ).strip():
            raise ValueError("V4 frontier is missing its typed target identity")
    else:
        updated.setdefault("target_asset", split_graph_node_id(anchor_node)[0])
        updated.setdefault("target_node", anchor_node)
    updated.setdefault("requested_window", {"start": DEFAULT_BACKTEST_START, "end": None})
    updated["source"] = "abel_live" if updated.get("source") in {"", "pending", None} else updated.get("source")
    updated["updated_at"] = now

    node_map = {
        str(node.get("node_id") or ""): dict(node)
        for node in updated.get("nodes") or []
        if isinstance(node, dict) and str(node.get("node_id") or "")
    }
    anchor = node_map.get(anchor_node)
    if anchor is None:
        if contract.is_v4:
            raise ValueError("V4 expansion anchor is not present in the frontier")
        anchor = build_frontier_node(
            node_id=anchor_node,
            roles=["expansion_anchor"],
            discovered_from="agent",
            depth=0,
            seen_at=now,
        )
        node_map[anchor_node] = anchor
    elif contract.is_v4:
        _require_matching_v4_node_identity(
            anchor,
            returned_target_ref,
            context="V4 expansion anchor",
        )
    anchor["last_expanded_at"] = now
    anchor_depth = int(anchor.get("depth") or 0)

    new_nodes: list[str] = []
    updated_nodes: list[str] = []
    for section, role in (("parents", "parent"), ("blanket_new", "blanket"), ("children", "child")):
        for item in payload.get(section) or []:
            driver_ref = item.get("driver_ref") if isinstance(item, dict) else None
            if contract.is_v4:
                validate_v4_node_descriptor(item, context=f"expansion {section}")
            raw_node_id = graph_node_id_from_item(item)
            node_id = (
                str(raw_node_id or "").strip()
                if contract.is_v4
                else normalize_graph_node_ref(raw_node_id)
            )
            if not node_id:
                continue
            if node_id == anchor_node:
                if contract.is_v4:
                    _require_matching_v4_node_identity(
                        anchor,
                        item,
                        context=f"V4 expansion self-reference '{anchor_node}'",
                    )
                continue
            roles = graph_roles_from_item(item, fallback=role)
            if node_id not in node_map:
                node_map[node_id] = build_frontier_node(
                    node_id=node_id,
                    roles=roles,
                    discovered_from=anchor_node,
                    depth=anchor_depth + 1,
                    seen_at=now,
                    driver_ref=driver_ref,
                    driver_ref_sha256=(
                        str(item.get("driver_ref_sha256") or "")
                        if isinstance(item, dict)
                        else ""
                    ),
                    family=(
                        str(item.get("family") or "")
                        if isinstance(item, dict)
                        else ""
                    ),
                    source_rank=(
                        item.get("source_rank") if isinstance(item, dict) else None
                    ),
                )
                new_nodes.append(node_id)
                continue
            existing = node_map[node_id]
            if contract.is_v4:
                _require_matching_v4_node_identity(
                    existing,
                    item,
                    context=f"rediscovered V4 node '{node_id}'",
                )
            existing["discovery_roles"] = ordered_unique_strings(
                list(existing.get("discovery_roles") or []) + roles
            )
            existing["discovered_from"] = ordered_unique_strings(
                list(existing.get("discovered_from") or []) + [anchor_node]
            )
            existing["depth"] = min(int(existing.get("depth") or anchor_depth + 1), anchor_depth + 1)
            updated_nodes.append(node_id)

    expansion = {
        "expansion_id": frontier_expansion_id(anchor_node=anchor_node, mode=mode, timestamp=now),
        "anchor_node": anchor_node,
        "mode": mode,
        "limit": limit,
        "source": str(payload.get("source") or "abel_live"),
        "new_nodes": ordered_unique_strings(new_nodes),
        "updated_nodes": ordered_unique_strings(updated_nodes),
        "created_at": now,
    }
    expansions = [item for item in updated.get("expansions") or [] if isinstance(item, dict)]
    expansions.append(expansion)
    updated["nodes"] = sorted(node_map.values(), key=lambda item: str(item.get("node_id") or ""))
    updated["expansions"] = expansions
    return updated, expansion


def graph_frontier_from_discovery_payload(
    payload: dict,
    *,
    backtest_start: str,
    expansion_mode: str,
    expansion_limit: int,
    expected_graph_release: dict | None = None,
) -> dict:
    now = str(payload.get("created_at") or _now())
    contract = discovery_graph_contract(
        payload,
        expected_release=expected_graph_release,
    )
    if contract.is_v4:
        if payload.get("contract") != "abel-edge.graph-discovery/v2":
            raise ValueError("V4 discovery must use abel-edge.graph-discovery/v2")
        target_asset, target_node, target_ref = _v4_target_identity(payload)
    else:
        target_asset = str(
            payload.get("target_asset") or payload.get("ticker") or ""
        ).strip().upper()
        target_node = str(payload.get("target_node") or "").strip() or default_graph_node_id(
            target_asset
        )
        target_ref = None
    nodes: dict[str, dict] = {}

    def remember(node: dict) -> None:
        key = str(node.get("node_id") or "").strip()
        if not key:
            return
        if key not in nodes:
            nodes[key] = node
            return
        existing = nodes[key]
        if contract.is_v4:
            _require_matching_v4_node_identity(
                existing,
                node,
                context=f"duplicate V4 discovery node '{key}'",
            )
        existing["discovery_roles"] = ordered_unique_strings(
            list(existing.get("discovery_roles") or []) + list(node.get("discovery_roles") or [])
        )
        existing["discovered_from"] = ordered_unique_strings(
            list(existing.get("discovered_from") or []) + list(node.get("discovered_from") or [])
        )
        existing["depth"] = min(int(existing.get("depth") or 0), int(node.get("depth") or 0))

    remember(
        build_frontier_node(
            node_id=target_node,
            roles=["target"],
            discovered_from="session",
            depth=0,
            seen_at=now,
            driver_ref=(target_ref or {}).get("driver_ref"),
            driver_ref_sha256=str((target_ref or {}).get("driver_ref_sha256") or ""),
            family=str((target_ref or {}).get("family") or ""),
        )
    )
    for section, role in (("parents", "parent"), ("blanket_new", "blanket"), ("children", "child")):
        for item in payload.get(section) or []:
            if contract.is_v4:
                validate_v4_node_descriptor(item, context=f"discovery {section}")
            node_id = graph_node_id_from_item(item)
            if not node_id:
                continue
            if node_id == target_node:
                if contract.is_v4:
                    _require_matching_v4_node_identity(
                        nodes[target_node],
                        item,
                        context=f"duplicate V4 discovery target '{target_node}'",
                    )
                continue
            remember(
                build_frontier_node(
                    node_id=node_id,
                    roles=graph_roles_from_item(item, fallback=role),
                    discovered_from=target_node,
                    depth=1,
                    seen_at=now,
                    driver_ref=item.get("driver_ref") if isinstance(item, dict) else None,
                    driver_ref_sha256=(
                        str(item.get("driver_ref_sha256") or "")
                        if isinstance(item, dict)
                        else ""
                    ),
                    family=(
                        str(item.get("family") or "") if isinstance(item, dict) else ""
                    ),
                    source_rank=(
                        item.get("source_rank") if isinstance(item, dict) else None
                    ),
                )
            )
    expansion_nodes = [node_id for node_id in sorted(nodes) if node_id != target_node]
    frontier = {
        "schema_version": 2 if contract.is_v4 else 1,
        "target_asset": target_asset,
        "target_node": target_node,
        "requested_window": {"start": backtest_start, "end": None},
        "source": str(payload.get("source") or "abel_live"),
        "created_at": now,
        "updated_at": now,
        "nodes": list(nodes.values()),
        "expansions": [
            {
                "expansion_id": frontier_expansion_id(anchor_node=target_node, mode=expansion_mode, timestamp=now),
                "anchor_node": target_node,
                "mode": expansion_mode,
                "limit": expansion_limit,
                "source": str(payload.get("source") or "abel_live"),
                "new_nodes": expansion_nodes,
                "updated_nodes": [],
                "created_at": now,
            }
        ],
    }
    if target_ref is not None:
        frontier["target_ref"] = target_ref
    if contract.has_release:
        frontier["graph_release"] = contract.release
        frontier["graph_release_sha256"] = contract.sha256
    return frontier


def graph_frontier_to_discovery(frontier: dict) -> dict:
    graph_release = frontier.get("graph_release")
    contract = resolve_graph_contract(
        graph_release,
        graph_release_sha256=str(frontier.get("graph_release_sha256") or ""),
        require_sha256=graph_release is not None,
    )
    target_asset = str(frontier.get("target_asset") or "").strip()
    if not contract.is_v4:
        target_asset = target_asset.upper()
    target_node = str(frontier.get("target_node") or "").strip() or default_graph_node_id(target_asset)
    discovery = {
        "ticker": target_asset,
        "target_asset": target_asset,
        "target_node": target_node,
        "source": frontier.get("source", "unknown"),
        "parents": [],
        "blanket_new": [],
        "children": [],
        "K_discovery": 0,
        "backtest": {"start": (frontier.get("requested_window") or {}).get("start", DEFAULT_BACKTEST_START)},
        "created_at": frontier.get("created_at", "unknown"),
    }
    if contract.is_v4:
        _v4_target_identity(frontier, require_ticker=False)
        discovery["target_ref"] = frontier["target_ref"]
    for node in frontier.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("node_id") or "").strip()
        if not node_id or node_id == target_node:
            continue
        item = {
            "node_id": node_id,
            "ticker": str(node.get("asset") or "").strip().upper(),
            "field": str(node.get("field") or "price").strip(),
        }
        for key in ("driver_ref", "driver_ref_sha256", "family", "source_rank"):
            if node.get(key) not in (None, ""):
                item[key] = node[key]
        roles = [str(role) for role in node.get("discovery_roles") or []]
        if "parent" in roles:
            discovery["parents"].append(item)
        elif "child" in roles:
            discovery["children"].append(item)
        else:
            item["roles"] = roles or ["neighbor"]
            discovery["blanket_new"].append(item)
    discovery["K_discovery"] = (
        len(discovery["parents"]) + len(discovery["blanket_new"]) + len(discovery["children"])
    )
    if contract.has_release:
        discovery["graph_release"] = contract.release
        discovery["graph_release_sha256"] = contract.sha256
    return discovery


def build_frontier_node(
    *,
    node_id: str,
    roles: list[str],
    discovered_from: str,
    depth: int,
    seen_at: str,
    driver_ref: dict | None = None,
    driver_ref_sha256: str = "",
    family: str = "",
    source_rank: object = None,
) -> dict:
    typed_ref = dict(driver_ref) if isinstance(driver_ref, dict) else None
    if typed_ref and typed_ref.get("kind") == "canonical_node":
        asset, field = "", "value"
    elif typed_ref and typed_ref.get("kind") == "symbol":
        asset = str(typed_ref.get("symbol") or "").strip().upper()
        field = str(typed_ref.get("field") or "close").strip().lower()
    else:
        asset, field = split_graph_node_id(node_id)
    node = {
        "node_id": node_id,
        "asset": asset,
        "field": field,
        "discovery_roles": ordered_unique_strings(roles),
        "discovered_from": ordered_unique_strings([discovered_from]),
        "depth": depth,
        "first_seen_at": seen_at,
        "last_expanded_at": None,
        "availability_summary": None,
        "branch_usage": [],
    }
    if typed_ref:
        node["driver_ref"] = typed_ref
    if driver_ref_sha256:
        node["driver_ref_sha256"] = driver_ref_sha256
    if family:
        node["family"] = family
    if source_rank is not None:
        node["source_rank"] = int(source_rank)
    return node


def graph_node_id_from_item(item: object) -> str:
    if isinstance(item, dict):
        node_id = str(item.get("node_id") or "").strip()
        if node_id:
            return node_id
        asset = str(item.get("ticker") or item.get("symbol") or "").strip().upper()
        field = str(item.get("field") or "price").strip().lower()
        return f"{asset}.{field}" if asset else ""
    value = str(item or "").strip()
    if not value:
        return ""
    return value if "." in value else default_graph_node_id(value)


def _v4_target_identity(
    payload: dict,
    *,
    require_ticker: bool = True,
    require_symbol: bool = True,
) -> tuple[str, str, dict]:
    return validate_v4_target_identity(
        target_asset=str(payload.get("target_asset") or ""),
        target_node=str(payload.get("target_node") or ""),
        target_ref=payload.get("target_ref"),
        ticker=str(payload.get("ticker") or ""),
        check_ticker=require_ticker,
        require_symbol=require_symbol,
    )


def _require_matching_v4_node_identity(
    stored: dict,
    returned: object,
    *,
    context: str,
) -> None:
    returned_descriptor = validate_v4_node_descriptor(returned, context=context)
    for key in ("node_id", "driver_ref", "driver_ref_sha256", "family"):
        if stored.get(key) != returned_descriptor.get(key):
            raise ValueError(f"{context} conflicts on {key}")


def graph_roles_from_item(item: object, *, fallback: str) -> list[str]:
    roles: list[str] = []
    if isinstance(item, dict):
        roles = [str(role).strip() for role in item.get("roles") or [] if str(role).strip()]
    return ordered_unique_strings([fallback, *roles])


def frontier_expansion_id(*, anchor_node: str, mode: str, timestamp: str) -> str:
    safe_anchor = re.sub(r"[^A-Za-z0-9]+", "-", anchor_node).strip("-").lower()
    safe_mode = re.sub(r"[^A-Za-z0-9]+", "-", mode).strip("-").lower()
    safe_time = re.sub(r"[^0-9A-Za-z]+", "", timestamp)[:15]
    return f"{safe_time}-{safe_anchor}-{safe_mode}".strip("-")
