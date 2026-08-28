"""Branch declaration and prepared-input contract helpers."""

from __future__ import annotations

import yaml
import hashlib
import json
import pandas as pd
from pathlib import Path
from typing import Any

from abel_invest.narrative_core.contracts.constants import (
    COMPLEXITY_CLASSES,
    DECLARATION_PLACEHOLDER_VALUES,
    DEFAULT_BACKTEST_START,
    EVIDENCE_INTENTS,
    EXPLORATION_ROLES,
    GRAPH_INPUT_CLAIMS,
    INPUT_CLAIMS,
    MODEL_FAMILIES,
)
from abel_invest.narrative_core.contracts.graph_release import (
    GraphContract,
    resolve_graph_contract,
    validate_v4_selected_entries,
    validate_v4_target_identity,
)
from abel_invest.narrative_core.io import _now
from abel_invest.narrative_core.contracts.paths import branch_spec_path
from abel_invest.narrative_core.readiness import readiness_usable_tickers


def normalize_hypothesis_text(value: str) -> str:
    text = str(value or "").strip()
    if text:
        return text
    return (
        "Candidate note missing. Before the next round, state the search "
        "objective, selected input universe, search width when applicable, "
        "and graph-use claim when claiming graph-derived contribution."
    )


def has_explicit_hypothesis(value: str) -> bool:
    text = str(value or "").strip()
    return bool(
        text
        and text != "No hypothesis supplied."
        and not text.startswith("Hypothesis missing.")
        and not text.startswith("Candidate note missing.")
    )


def _get_backtest_start(discovery: dict) -> str:
    backtest = discovery.get("backtest") or {}
    if isinstance(backtest, dict):
        start = backtest.get("start")
        if start:
            return str(start)
    return DEFAULT_BACKTEST_START


def branch_requested_start(branch: Path, discovery: dict) -> str:
    branch_spec = load_branch_spec(branch)
    requested = str(branch_spec.get("requested_start") or "").strip()
    if requested:
        return requested
    return _get_backtest_start(discovery)


def normalize_evidence_intent(branch_spec: dict) -> str:
    configured = str(branch_spec.get("evidence_intent") or "").strip().lower()
    if configured in EVIDENCE_INTENTS:
        return configured
    return ""


def normalize_input_claim(branch_spec: dict) -> str:
    configured = str(branch_spec.get("input_claim") or "").strip().lower()
    if configured in INPUT_CLAIMS:
        return configured
    return ""


def normalize_model_family(branch_spec: dict) -> str:
    configured = str(branch_spec.get("model_family") or "").strip().lower()
    if configured in MODEL_FAMILIES:
        return configured
    return "unspecified"


def normalize_complexity_class(branch_spec: dict) -> str:
    configured = str(branch_spec.get("complexity_class") or "").strip().lower()
    if configured in COMPLEXITY_CLASSES:
        return configured
    model_family = normalize_model_family(branch_spec)
    if model_family in {"tree_model", "learned_model", "ensemble"}:
        return "learned_model"
    if model_family == "hybrid":
        return "hybrid"
    return "unspecified"


def normalize_exploration_role(branch_spec: dict) -> str:
    configured = str(branch_spec.get("exploration_role") or "").strip().lower()
    if configured in EXPLORATION_ROLES:
        return configured
    evidence_intent = normalize_evidence_intent(branch_spec)
    if evidence_intent == "control":
        return "control"
    if evidence_intent == "diagnostic":
        return "diagnostic"
    if evidence_intent == "candidate":
        return "candidate"
    return "unspecified"


def split_graph_node_id(node_id: str) -> tuple[str, str]:
    value = str(node_id or "").strip()
    if "." not in value:
        return value.upper(), "price"
    asset, field = value.split(".", 1)
    return asset.strip().upper(), field.strip().lower() or "price"


def normalize_graph_node_ref(value: str) -> str:
    asset, field = split_graph_node_id(value)
    if not asset:
        return ""
    return f"{asset}.{field}"


def default_graph_node_id(asset: str) -> str:
    return f"{str(asset or '').strip().upper()}.price"


def branch_graph_contract(branch_spec: dict) -> GraphContract:
    graph_release = branch_spec.get("graph_release")
    if graph_release is not None and not isinstance(graph_release, dict):
        raise ValueError("branch graph_release must be a mapping")
    return resolve_graph_contract(
        graph_release,
        graph_release_sha256=str(branch_spec.get("graph_release_sha256") or ""),
        require_sha256=graph_release is not None,
    )


def _artifact_graph_contract(payload: dict, *, name: str) -> GraphContract:
    graph_release = payload.get("graph_release")
    if not isinstance(graph_release, dict):
        raise ValueError(f"{name} is missing its V4 graph release")
    return resolve_graph_contract(
        graph_release,
        graph_release_sha256=str(payload.get("graph_release_sha256") or ""),
        require_sha256=True,
    )


def _validate_v4_target(
    *,
    target: str,
    target_node: str,
    target_ref: object,
) -> dict[str, Any]:
    _asset, _node_id, normalized_ref = validate_v4_target_identity(
        target_asset=target,
        target_node=target_node,
        target_ref=target_ref,
    )
    return normalized_ref


def branch_selected_input_entries(branch_spec: dict) -> list[dict[str, Any]]:
    raw = branch_spec.get("selected_inputs")
    if not isinstance(raw, list):
        return []
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    contract = branch_graph_contract(branch_spec)
    for item in raw:
        if isinstance(item, dict):
            driver_ref = item.get("driver_ref")
            canonical = (
                isinstance(driver_ref, dict)
                and driver_ref.get("kind") == "canonical_node"
            )
            raw_node_id = str(item.get("node_id") or item.get("node") or "").strip()
            node_id = (
                raw_node_id
                if contract.is_v4 or canonical
                else normalize_graph_node_ref(raw_node_id)
            )
            if not node_id:
                asset = str(item.get("asset") or item.get("ticker") or "").strip()
                field = str(item.get("field") or "price").strip()
                node_id = normalize_graph_node_ref(f"{asset}.{field}") if asset else ""
            role = str(item.get("role") or "graph_input").strip() or "graph_input"
            source = str(item.get("source") or "frontier").strip() or "frontier"
            source_reason = str(item.get("source_reason") or "").strip()
        else:
            raw_node_id = str(item or "").strip()
            node_id = raw_node_id if contract.is_v4 else normalize_graph_node_ref(raw_node_id)
            role = "graph_input"
            source = "frontier"
            source_reason = ""
        if not node_id or node_id in seen:
            continue
        entry: dict[str, Any] = {"node_id": node_id, "role": role, "source": source}
        if source_reason:
            entry["source_reason"] = source_reason
        if isinstance(item, dict):
            for key in (
                "driver_ref",
                "driver_ref_sha256",
                "family",
                "source_rank",
                "feed_alias",
                "series_spec",
            ):
                if item.get(key) not in (None, ""):
                    entry[key] = item[key]
        entries.append(entry)
        seen.add(node_id)
    return entries


def branch_selected_inputs(branch_spec: dict) -> list[str]:
    assets = []
    for entry in branch_selected_input_entries(branch_spec):
        driver_ref = entry.get("driver_ref")
        if isinstance(driver_ref, dict) and driver_ref.get("kind") == "canonical_node":
            continue
        if isinstance(driver_ref, dict) and driver_ref.get("kind") == "symbol":
            asset = str(driver_ref.get("symbol") or "").strip().upper()
        else:
            asset, _field = split_graph_node_id(str(entry.get("node_id") or ""))
        if asset:
            assets.append(asset)
    return ordered_unique_upper(assets)


def branch_selected_graph_nodes(branch_spec: dict) -> list[str]:
    return ordered_unique_strings(
        entry["node_id"]
        for entry in branch_selected_input_entries(branch_spec)
        if entry.get("node_id")
    )


def normalize_graph_node_list(values: object) -> list[str]:
    raw = values if isinstance(values, list) else []
    return ordered_unique_strings(
        node_id
        for node_id in (normalize_graph_node_ref(str(item or "")) for item in raw)
        if node_id
    )


def graph_nodes_by_asset(entries: list[dict[str, str]]) -> dict[str, list[str]]:
    mapped: dict[str, list[str]] = {}
    for entry in entries:
        node_id = normalize_graph_node_ref(str(entry.get("node_id") or ""))
        if not node_id:
            continue
        asset, _field = split_graph_node_id(node_id)
        mapped.setdefault(asset, []).append(node_id)
    return {asset: ordered_unique_strings(nodes) for asset, nodes in mapped.items()}


def graph_nodes_for_assets(assets: object, entries: list[dict[str, str]]) -> list[str]:
    mapped = graph_nodes_by_asset(entries)
    selected: list[str] = []
    for asset in ordered_unique_upper(assets if isinstance(assets, list) else []):
        selected.extend(mapped.get(asset, []))
    return ordered_unique_strings(selected)


def ordered_unique_upper(values) -> list[str]:
    return ordered_unique_strings(str(item or "").strip().upper() for item in values)


def ordered_unique_strings(values) -> list[str]:
    selected: list[str] = []
    for item in values:
        value = str(item or "").strip()
        if value and value not in selected:
            selected.append(value)
    return selected


def canonicalize_branch_spec_inputs(payload: dict) -> dict:
    branch_spec = dict(payload)
    entries = branch_selected_input_entries(branch_spec)
    if entries or "selected_inputs" in branch_spec:
        raw = branch_spec.get("selected_inputs")
        if isinstance(raw, list) and any(isinstance(item, dict) for item in raw):
            branch_spec["selected_inputs"] = entries
        else:
            branch_spec["selected_inputs"] = [
                split_graph_node_id(entry["node_id"])[0] for entry in entries
            ]
    branch_spec.pop("selected_drivers", None)
    return branch_spec


def branch_declaration_status(branch_spec: dict) -> dict[str, object]:
    hypothesis = str(branch_spec.get("hypothesis") or "").strip()
    evidence_intent = normalize_evidence_intent(branch_spec)
    input_claim = normalize_input_claim(branch_spec)
    mechanism_family = str(branch_spec.get("mechanism_family") or "").strip().lower()
    invalidation_condition = str(branch_spec.get("invalidation_condition") or "").strip()
    requested_start = str(branch_spec.get("requested_start") or "").strip()
    selected_inputs = branch_selected_inputs(branch_spec)
    selected_graph_nodes = branch_selected_graph_nodes(branch_spec)

    gaps: list[str] = []
    if not has_explicit_hypothesis(hypothesis):
        gaps.append("hypothesis")
    if evidence_intent not in EVIDENCE_INTENTS:
        gaps.append("evidence_intent")
    if input_claim not in INPUT_CLAIMS:
        gaps.append("input_claim")
    if mechanism_family in DECLARATION_PLACEHOLDER_VALUES:
        gaps.append("mechanism_family")
    if not invalidation_condition:
        gaps.append("invalidation_condition")
    if not requested_start:
        gaps.append("requested_start")
    if input_claim in GRAPH_INPUT_CLAIMS and not (selected_inputs or selected_graph_nodes):
        gaps.append("selected_inputs")
    if evidence_intent == "draft":
        gaps.append("evidence_intent:draft")

    return {
        "protocol_complete": not gaps,
        "protocol_gaps": gaps,
        "hypothesis": hypothesis,
        "evidence_intent": evidence_intent,
        "input_claim": input_claim,
        "mechanism_family": mechanism_family,
        "model_family": normalize_model_family(branch_spec),
        "complexity_class": normalize_complexity_class(branch_spec),
        "exploration_role": normalize_exploration_role(branch_spec),
        "invalidation_condition": invalidation_condition,
        "requested_start": requested_start,
        "selected_inputs": selected_inputs,
        "selected_graph_nodes": selected_graph_nodes,
    }


def branch_declaration_status_for_branch(branch: Path) -> dict[str, object]:
    return branch_declaration_status(load_branch_spec(branch))


def load_branch_spec(branch: Path) -> dict:
    path = branch_spec_path(branch)
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return canonicalize_branch_spec_inputs(payload) if isinstance(payload, dict) else {}


def write_branch_spec(branch: Path, payload: dict) -> None:
    payload = canonicalize_branch_spec_inputs(payload)
    branch_spec_path(branch).write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def graph_frontier_candidate_node_ids(
    frontier: dict,
    readiness: dict,
    *,
    limit: int,
) -> list[str]:
    target_node = str(frontier.get("target_node") or "").strip()
    usable_assets = set(readiness_usable_tickers(readiness))
    candidates: list[tuple[int, int, str]] = []
    for node in frontier.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("node_id") or "").strip()
        if not node_id or node_id == target_node:
            continue
        roles = {str(role) for role in node.get("discovery_roles") or []}
        if "target" in roles:
            continue
        asset = str(node.get("asset") or "").upper()
        driver_ref = node.get("driver_ref")
        canonical = (
            isinstance(driver_ref, dict)
            and driver_ref.get("kind") == "canonical_node"
        )
        readiness_rank = 0 if canonical or asset in usable_assets else 1
        depth = int(node.get("depth") or 0)
        candidates.append((readiness_rank, depth, node_id))
    return [node_id for _ready, _depth, node_id in sorted(candidates)[:limit]]


def graph_input_entry(
    node_id: str,
    *,
    source: str = "frontier",
    role: str = "graph_input",
    frontier_node: dict | None = None,
    typed_v4: bool = False,
) -> dict[str, Any]:
    driver_ref = (frontier_node or {}).get("driver_ref")
    canonical = (
        isinstance(driver_ref, dict) and driver_ref.get("kind") == "canonical_node"
    )
    entry: dict[str, Any] = {
        "node_id": (
            str(node_id).strip()
            if typed_v4 or canonical
            else normalize_graph_node_ref(node_id)
        ),
        "role": role,
        "source": source,
    }
    for key in ("driver_ref", "driver_ref_sha256", "family", "source_rank"):
        if (frontier_node or {}).get(key) not in (None, ""):
            entry[key] = (frontier_node or {})[key]
    return entry


def discovery_candidate_tickers(discovery: dict) -> list[str]:
    target = str(discovery.get("ticker") or "").strip().upper()
    ordered: list[str] = []
    for section in ("parents", "blanket_new", "children"):
        for item in discovery.get(section) or []:
            if isinstance(item, dict):
                ticker = str(item.get("ticker") or "").strip().upper()
            else:
                ticker = str(item or "").strip().upper()
            if not ticker or ticker == target or ticker in ordered:
                continue
            ordered.append(ticker)
    return ordered


def suggest_branch_drivers(discovery: dict, readiness: dict, *, limit: int = 5) -> list[str]:
    discovered = discovery_candidate_tickers(discovery)
    usable = set(readiness_usable_tickers(readiness))
    prioritized = [ticker for ticker in discovered if ticker in usable]
    fallback = [ticker for ticker in discovered if ticker not in usable]
    return (prioritized + fallback)[:limit]


def build_default_branch_spec(
    *,
    branch: Path,
    discovery: dict,
    readiness: dict,
    graph_frontier: dict | None = None,
) -> dict:
    frontier = graph_frontier or {}
    graph_release = frontier.get("graph_release")
    if graph_release is not None and not isinstance(graph_release, dict):
        raise ValueError("frontier graph_release must be a mapping")
    contract = resolve_graph_contract(
        graph_release,
        graph_release_sha256=str(frontier.get("graph_release_sha256") or ""),
        require_sha256=graph_release is not None,
    )
    target = str(
        discovery.get("ticker") or branch.parent.parent.parent.name
    ).strip().upper()
    target_node = (
        str(frontier.get("target_node") or "").strip()
        if contract.is_v4
        else default_graph_node_id(target)
    )
    if contract.is_v4 and not target_node:
        raise ValueError("V4 frontier is missing target_node")
    target_ref = None
    if contract.is_v4:
        target_ref = _validate_v4_target(
            target=target,
            target_node=target_node,
            target_ref=frontier.get("target_ref"),
        )
    suggested_nodes = graph_frontier_candidate_node_ids(frontier, readiness, limit=5)
    selected_nodes = suggested_nodes[: min(3, len(suggested_nodes))]
    frontier_nodes = {
        str(item.get("node_id") or ""): item
        for item in frontier.get("nodes") or []
        if isinstance(item, dict)
    }
    graph_enriched = bool(selected_nodes)
    spec = {
        "version": 2,
        "branch_id": branch.name,
        "target": target,
        "target_node": target_node,
        "hypothesis": "",
        "evidence_intent": "draft",
        "input_claim": "graph_supported" if graph_enriched else "target_only",
        "mechanism_family": "unspecified",
        "invalidation_condition": "",
        "model_family": "unspecified",
        "complexity_class": "unspecified",
        "exploration_role": "candidate",
        "parent_branch_id": "",
        "requested_start": _get_backtest_start(discovery),
        "resolved_start_policy": "requested",
        "overlap_mode": "target_only",
        "selected_inputs": [
            graph_input_entry(
                node_id,
                frontier_node=frontier_nodes.get(node_id),
                typed_v4=contract.is_v4,
            )
            for node_id in selected_nodes
        ],
        "data_requirements": {
            "timeframe": "1d",
            "fields": ["close"],
        },
    }
    if contract.is_v4:
        spec["graph_release"] = contract.release
        spec["graph_release_sha256"] = contract.sha256
        spec["target_ref"] = target_ref
    return spec


def branch_dependencies_payload(
    *,
    branch: Path,
    branch_spec: dict,
    target: str,
    selected_inputs: list[str],
    requested_start: str,
) -> dict:
    selected_inputs = ordered_unique_upper(selected_inputs)
    contract = branch_graph_contract(branch_spec)
    selected_entries = branch_selected_input_entries(branch_spec)
    selected_graph_nodes = branch_selected_graph_nodes(branch_spec)
    if contract.is_v4:
        validate_v4_selected_entries(selected_entries)
    target_node = (
        str(branch_spec.get("target_node") or "").strip()
        if contract.is_v4
        else default_graph_node_id(target)
    )
    if contract.is_v4 and not target_node:
        raise ValueError("V4 branch spec is missing target_node")
    target_ref = None
    if contract.is_v4:
        target_ref = _validate_v4_target(
            target=target,
            target_node=target_node,
            target_ref=branch_spec.get("target_ref"),
        )
        expected_inputs = branch_selected_inputs(branch_spec)
        if selected_inputs != expected_inputs:
            raise ValueError("V4 selected_inputs conflict with selected driver references")
    payload = {
        "version": 2 if contract.is_v4 else 1,
        "branch_id": branch.name,
        "target": target,
        "target_node": target_node,
        "selected_inputs": selected_inputs,
        "selected_graph_nodes": selected_graph_nodes,
        "requested_start": requested_start,
        "overlap_mode": branch_spec.get("overlap_mode") or "target_only",
        "data_requirements": branch_spec.get("data_requirements") or {"timeframe": "1d"},
        "prepared_at": _now(),
    }
    if contract.is_v4:
        payload["selected_drivers"] = selected_entries
        payload["graph_release"] = contract.release
        payload["graph_release_sha256"] = contract.sha256
        payload["target_ref"] = target_ref
    return payload


def canonicalize_dependencies_payload(payload: dict) -> dict:
    dependencies = dict(payload)
    version = int(dependencies.get("version") or 1)
    if version >= 2:
        contract = _artifact_graph_contract(dependencies, name="dependencies")
        if not contract.is_v4:
            raise ValueError("dependencies v2 requires a CausalNodeV4 graph release")
        _validate_v4_target(
            target=str(dependencies.get("target") or ""),
            target_node=str(dependencies.get("target_node") or ""),
            target_ref=dependencies.get("target_ref"),
        )
    raw = dependencies.get("selected_inputs")
    selected = ordered_unique_upper(raw if isinstance(raw, list) else [])
    selected_graph_nodes = (
        ordered_unique_strings(dependencies.get("selected_graph_nodes") or [])
        if version >= 2
        else normalize_graph_node_list(dependencies.get("selected_graph_nodes"))
    )
    if not selected_graph_nodes:
        selected_graph_nodes = [default_graph_node_id(asset) for asset in selected]
    if version >= 2:
        selected_drivers = dependencies.get("selected_drivers")
        if not isinstance(selected_drivers, list) or not all(
            isinstance(item, dict) for item in selected_drivers
        ):
            raise ValueError("dependencies v2 requires selected_drivers")
        validate_v4_selected_entries(selected_drivers)
        expected_nodes = ordered_unique_strings(
            str(item.get("node_id") or "") for item in selected_drivers
        )
        expected_inputs = ordered_unique_upper(
            str(item["driver_ref"].get("symbol") or "")
            for item in selected_drivers
            if item["driver_ref"].get("kind") == "symbol"
        )
        if selected_graph_nodes != expected_nodes or selected != expected_inputs:
            raise ValueError("dependencies v2 selected inputs conflict with selected_drivers")
    if selected or "selected_inputs" in dependencies:
        dependencies["selected_inputs"] = selected
    if selected_graph_nodes or "selected_graph_nodes" in dependencies:
        dependencies["selected_graph_nodes"] = selected_graph_nodes
    if version < 2:
        dependencies.pop("selected_drivers", None)
    return dependencies


def build_runtime_profile_payload(*, target: str, branch_spec: dict | None = None) -> dict:
    payload = {
        "profile": "daily",
        "target": target,
        "decision_event": "bar_close",
        "execution_delay_bars": 1,
        "return_basis": "close_to_close",
    }
    validation_profile = str((branch_spec or {}).get("validation_profile") or "").strip()
    if validation_profile:
        payload["validation_profile"] = validation_profile
    return payload


def build_execution_constraints_payload(branch_spec: dict) -> dict:
    payload = {"long_only": bool(branch_spec.get("long_only", False))}
    position_bounds = branch_spec.get("position_bounds")
    if isinstance(position_bounds, (list, tuple)) and len(position_bounds) == 2:
        payload["position_bounds"] = [float(position_bounds[0]), float(position_bounds[1])]
    return payload


def build_data_manifest_payload(
    *,
    target: str,
    selected_inputs: list[str],
    selected_graph_nodes: list[str] | None = None,
    cache_payload: dict,
    readiness: dict,
    selected_driver_entries: list[dict[str, Any]] | None = None,
    canonical_series_specs: dict[str, dict] | None = None,
    graph_release: dict | None = None,
    graph_release_sha256: str = "",
    target_node: str = "",
    target_ref: dict | None = None,
) -> dict:
    selected_inputs = ordered_unique_upper(selected_inputs)
    selected_driver_entries = selected_driver_entries or []
    contract = resolve_graph_contract(
        graph_release,
        graph_release_sha256=graph_release_sha256,
        require_sha256=graph_release is not None,
    )
    if contract.is_v4:
        validate_v4_selected_entries(selected_driver_entries)
        normalized_target_ref = _validate_v4_target(
            target=target,
            target_node=target_node,
            target_ref=target_ref,
        )
        expected_inputs = ordered_unique_upper(
            str(entry["driver_ref"].get("symbol") or "")
            for entry in selected_driver_entries
            if entry["driver_ref"].get("kind") == "symbol"
        )
        if selected_inputs != expected_inputs:
            raise ValueError("V4 selected_inputs conflict with selected driver references")
    else:
        normalized_target_ref = None
    canonical_entries = [
        entry
        for entry in selected_driver_entries
        if isinstance(entry.get("driver_ref"), dict)
        and entry["driver_ref"].get("kind") == "canonical_node"
    ]
    selected_graph_nodes = (
        ordered_unique_strings(selected_graph_nodes or [])
        if contract.is_v4
        else normalize_graph_node_list(selected_graph_nodes)
    )
    if not selected_graph_nodes:
        selected_graph_nodes = [default_graph_node_id(asset) for asset in selected_inputs]
    if contract.is_v4:
        expected_nodes = ordered_unique_strings(
            str(entry.get("node_id") or "") for entry in selected_driver_entries
        )
        if selected_graph_nodes != expected_nodes:
            raise ValueError("V4 selected_graph_nodes conflict with selected driver references")
    if contract.is_v4:
        graph_by_asset: dict[str, list[str]] = {}
        for entry in selected_driver_entries:
            driver_ref = entry.get("driver_ref")
            if not isinstance(driver_ref, dict) or driver_ref.get("kind") != "symbol":
                continue
            symbol = str(driver_ref.get("symbol") or "").strip().upper()
            node_id = str(entry.get("node_id") or "").strip()
            if symbol and node_id:
                graph_by_asset.setdefault(symbol, []).append(node_id)
    else:
        graph_by_asset = graph_nodes_by_asset(
            [graph_input_entry(node_id) for node_id in selected_graph_nodes]
        )
    cache_results = {
        str(item.get("symbol") or "").strip().upper(): item
        for item in (cache_payload.get("results") or [])
        if isinstance(item, dict) and str(item.get("symbol") or "").strip()
    }
    readiness_results = {
        str(item.get("ticker") or "").strip().upper(): item
        for item in (readiness.get("results") or [])
        if isinstance(item, dict) and str(item.get("ticker") or "").strip()
    }
    feeds: list[dict[str, object]] = []
    ordered_symbols = [target] + [ticker for ticker in selected_inputs if ticker != target]
    adapter = str(cache_payload.get("adapter") or "abel")
    path = cache_payload.get("path")
    timeframe = str(cache_payload.get("timeframe") or "1d")
    profile = str(cache_payload.get("profile") or "daily")
    cache_root = cache_payload.get("cache_root")
    for symbol in ordered_symbols:
        cache_item = cache_results.get(symbol, {})
        readiness_item = readiness_results.get(symbol, {})
        feed_entry = {
            "name": "primary" if symbol == target else symbol,
            "symbol": symbol,
            "role": "target" if symbol == target else "driver",
            "graph_node_id": (target_node or default_graph_node_id(symbol))
            if symbol == target
            else (graph_by_asset.get(symbol) or [default_graph_node_id(symbol)])[0],
            "adapter": adapter,
            "timeframe": timeframe,
            "profile": profile,
            "ok": bool(cache_item.get("ok", False)),
            "row_count": int(cache_item.get("row_count", 0) or 0),
            "available_range": cache_item.get("available_range") or {},
            "readiness_status": readiness_item.get("status", "unknown"),
            "covers_requested_start": bool(readiness_item.get("covers_requested_start", False)),
        }
        if contract.is_v4:
            feed_entry["kind"] = "bars"
        if cache_root:
            feed_entry["cache_root"] = cache_root
        if path:
            feed_entry["path"] = path
        feeds.append(feed_entry)
    canonical_series_specs = canonical_series_specs or {}
    for entry in canonical_entries:
        node_id = str(entry.get("node_id") or "").strip()
        series_spec = canonical_series_specs.get(node_id)
        if not isinstance(series_spec, dict):
            raise ValueError(f"Canonical graph node '{node_id}' has no prepared Edge series spec.")
        digest = hashlib.sha256(
            json.dumps(
                series_spec,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        receipt = str(
            ((series_spec.get("provenance") or {}).get("source_receipt_sha256"))
            or ""
        )
        alias = str(entry.get("feed_alias") or f"graph_node_{digest[:12]}")
        feeds.append(
            {
                "name": alias,
                "kind": "point_in_time_series",
                "adapter": "abel",
                "role": "driver",
                "graph_node_id": node_id,
                "family": str(entry.get("family") or "canonical_node"),
                "source_rank": entry.get("source_rank"),
                "driver_ref": entry["driver_ref"],
                "driver_ref_sha256": str(entry.get("driver_ref_sha256") or ""),
                "series_spec": series_spec,
                "series_spec_sha256": digest,
                "series_receipt_sha256": receipt,
                "ok": True,
            }
        )
    manifest = {
        "version": 2 if contract.is_v4 else 1,
        "target": target,
        "target_node": target_node or default_graph_node_id(target),
        "selected_inputs": selected_inputs,
        "selected_graph_nodes": selected_graph_nodes,
        "feeds": feeds,
    }
    if contract.is_v4:
        manifest["selected_drivers"] = selected_driver_entries
        manifest["graph_release"] = contract.release
        manifest["graph_release_sha256"] = contract.sha256
        manifest["target_ref"] = normalized_target_ref
    return manifest


def canonicalize_data_manifest_payload(payload: dict) -> dict:
    manifest = dict(payload)
    version = int(manifest.get("version") or 1)
    if version >= 2:
        contract = _artifact_graph_contract(manifest, name="data manifest")
        if not contract.is_v4:
            raise ValueError("data manifest v2 requires a CausalNodeV4 graph release")
        _validate_v4_target(
            target=str(manifest.get("target") or ""),
            target_node=str(manifest.get("target_node") or ""),
            target_ref=manifest.get("target_ref"),
        )
    raw_selected = manifest.get("selected_inputs")
    selected = ordered_unique_upper(raw_selected if isinstance(raw_selected, list) else [])
    selected_graph_nodes = (
        ordered_unique_strings(manifest.get("selected_graph_nodes") or [])
        if version >= 2
        else normalize_graph_node_list(manifest.get("selected_graph_nodes"))
    )
    if not selected_graph_nodes:
        selected_graph_nodes = [default_graph_node_id(asset) for asset in selected]
    if version >= 2:
        selected_drivers = manifest.get("selected_drivers")
        if not isinstance(selected_drivers, list) or not all(
            isinstance(item, dict) for item in selected_drivers
        ):
            raise ValueError("data manifest v2 requires selected_drivers")
        validate_v4_selected_entries(selected_drivers)
        expected_nodes = ordered_unique_strings(
            str(item.get("node_id") or "") for item in selected_drivers
        )
        expected_inputs = ordered_unique_upper(
            str(item["driver_ref"].get("symbol") or "")
            for item in selected_drivers
            if item["driver_ref"].get("kind") == "symbol"
        )
        if selected_graph_nodes != expected_nodes or selected != expected_inputs:
            raise ValueError("data manifest v2 inputs conflict with selected_drivers")
    feeds: list[dict[str, object]] = []
    seen_feeds: set[str] = set()
    for item in manifest.get("feeds") or []:
        if not isinstance(item, dict):
            continue
        feed = dict(item)
        symbol = str(feed.get("symbol") or "").strip().upper()
        name = str(feed.get("name") or symbol or "").strip()
        key = name or symbol
        if not key or key in seen_feeds:
            continue
        if symbol:
            feed["symbol"] = symbol
            feed.setdefault("graph_node_id", default_graph_node_id(symbol))
        if name:
            feed["name"] = name
        feeds.append(feed)
        seen_feeds.add(key)
    manifest["selected_inputs"] = selected
    raw_target_node = str(manifest.get("target_node") or "").strip()
    manifest["target_node"] = (
        raw_target_node if version >= 2 else normalize_graph_node_ref(raw_target_node)
    )
    manifest["selected_graph_nodes"] = selected_graph_nodes
    if version < 2:
        manifest.pop("selected_drivers", None)
    manifest["feeds"] = feeds
    return manifest


def build_probe_samples_payload(
    *,
    target: str,
    requested_start: str,
    data_manifest: dict,
) -> dict:
    feeds = data_manifest.get("feeds") or []
    target_feed = next(
        (item for item in feeds if item.get("role") == "target"),
        {},
    )
    available_range = (target_feed.get("available_range") or {}) if isinstance(target_feed, dict) else {}
    start = str(available_range.get("start") or requested_start or "").strip()
    end = str(available_range.get("end") or start or "").strip()
    samples: list[str] = []
    if start and end:
        try:
            dates = pd.date_range(start=start, end=end, periods=3, tz="UTC")
            samples = [str(ts.date()) for ts in dates]
        except Exception:
            samples = [item for item in [start, end] if item]
    return {
        "version": 1,
        "target": target,
        "requested_start": requested_start,
        "sample_decision_dates": samples,
    }


def build_context_guide_markdown(
    *,
    target: str,
    runtime_profile: dict,
    execution_constraints: dict,
    data_manifest: dict,
) -> str:
    feed_names = [
        str(item.get("name"))
        for item in (data_manifest.get("feeds") or [])
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    ]
    canonical_feed_names = [
        str(item.get("name"))
        for item in (data_manifest.get("feeds") or [])
        if isinstance(item, dict)
        and item.get("kind") == "point_in_time_series"
        and str(item.get("name") or "").strip()
    ]
    lines = [
        f"# {target} Branch Context Guide",
        "",
        "## Runtime",
        f"- profile: `{runtime_profile.get('profile', 'daily')}`",
        f"- validation_profile: `{runtime_profile.get('validation_profile', 'auto')}`",
        f"- decision_event: `{runtime_profile.get('decision_event', 'bar_close')}`",
        f"- execution_delay_bars: `{runtime_profile.get('execution_delay_bars', 1)}`",
        f"- return_basis: `{runtime_profile.get('return_basis', 'close_to_close')}`",
        "",
        "## Execution Constraints",
        f"- long_only: `{execution_constraints.get('long_only', False)}`",
        f"- position_bounds: `{execution_constraints.get('position_bounds', 'unbounded')}`",
        "",
        "## Available Feeds",
        f"- names: `{', '.join(feed_names) or 'primary only'}`",
        "- use `ctx.target.series(\"close\")` for target history",
        "- use `ctx.feed(\"<name>\").asof_series(\"close\"|\"volume\")` for market graph inputs",
        "- use `ctx.feed(\"<name>\").asof_series(\"value\")` for CAP canonical node inputs",
        f"- canonical node feed aliases: `{', '.join(canonical_feed_names) or 'none'}`",
        "- use `ctx.points()` when you need path-sensitive cross-calendar logic",
        "",
        "## Declaration Fields",
        "- `hypothesis`: legacy field name for compact candidate note or search objective",
        "- `evidence_intent`: candidate, control, diagnostic, or draft",
        "- `input_claim`: graph_supported, target_only, supplement, or mixed",
        "- graph-attribution claims should state selected nodes, construction, intended role, unresolved assumption, and falsification scope",
        "- `mechanism_family`: factual mechanism label when known",
        "- `invalidation_condition`: what would weaken the claim or candidate path",
        "",
        "## Disposable Search",
        "- temporary scripts, feature screens, model comparisons, and summaries may live in the session `scratch/` directory",
        "- for a fresh or unfamiliar ticker, the first serious recorded alpha candidate should normally be probe-informed",
        "- use this prepared branch's data/cache and `inputs/` for any first-look scout that needs market data",
        "- expect the first-look scout to take roughly 5 minutes: score plausible target, graph, and construction shapes, then rank what looks worth formal validation before broad recorded work",
        "- if the scout script is still making progress, let it finish naturally before deciding what to validate",
        "- a prepared scout branch can be prepare-only; do not run a flat/no-signal materialization round",
        "- IC/correlation/feature-importance tables are diagnostics; a first-look scout should rank scored candidate-shaped variants when graph/model construction is available",
        "- scratch/probe outputs are search workbench material, not validation evidence",
        "- if a probe materially selects this candidate, record the influence and effective search width before `run-branch`, including inline heredoc or notebook/query probes",
        "",
        "## Audit Checklist",
        "1. Inspect `probe_samples.json` and `data_manifest.json`.",
        "2. Edit `engine.py` against `DecisionContext`.",
        "3. Run debug-branch with the workspace command prefix first to read semantic preflight.",
        "4. Record a round after runtime inputs, objective, search width, and validation scope are clear.",
    ]
    return "\n".join(lines) + "\n"
