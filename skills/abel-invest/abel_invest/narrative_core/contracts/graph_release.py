"""Freeze caller-supplied Edge graph-release configuration in a session."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from abel_invest.narrative_core.contracts.constants import GRAPH_RELEASE_FILENAME

LEGACY_V3 = "legacy_v3"
TYPED_V4 = "typed_v4"


@dataclass(frozen=True)
class GraphContract:
    """Validated release provenance and its consumer behavior mode."""

    mode: str
    release: dict | None
    sha256: str

    @property
    def has_release(self) -> bool:
        return self.release is not None

    @property
    def is_v4(self) -> bool:
        return self.mode == TYPED_V4


def resolve_graph_contract(
    graph_release: Mapping | None,
    *,
    graph_release_sha256: str | None = None,
    require_sha256: bool = False,
) -> GraphContract:
    """Classify no-release/V3/V4 without treating provenance as a V4 signal."""

    supplied_sha256 = str(graph_release_sha256 or "").strip()
    if graph_release is None:
        if supplied_sha256:
            raise ValueError("graph release digest is present without graph release provenance")
        return GraphContract(mode=LEGACY_V3, release=None, sha256="")
    if not isinstance(graph_release, Mapping):
        raise ValueError("graph release must be a mapping")
    try:
        from abel_edge.plugins.abel.graph_release import GraphReleaseConfig
    except ImportError as exc:
        raise RuntimeError(
            "Graph releases require the Abel-edge typed-release contract; "
            "install the Edge release containing abel_edge.plugins.abel.graph_release."
        ) from exc
    config = GraphReleaseConfig.from_mapping(graph_release)
    if require_sha256 and not supplied_sha256:
        raise ValueError("graph release provenance is missing graph_release_sha256")
    if supplied_sha256 and supplied_sha256 != config.sha256:
        raise ValueError(
            "graph release digest does not match the normalized graph release: "
            f"expected {config.sha256}, got {supplied_sha256}"
        )
    mode = TYPED_V4 if config.graph_version == "CausalNodeV4" else LEGACY_V3
    return GraphContract(mode=mode, release=config.payload, sha256=config.sha256)


def discovery_graph_contract(
    payload: Mapping,
    *,
    expected_release: Mapping | None = None,
) -> GraphContract:
    """Validate returned release provenance and an optional frozen request."""

    graph_release = payload.get("graph_release")
    if graph_release is not None and not isinstance(graph_release, Mapping):
        raise ValueError("discovery graph_release must be a mapping")
    returned = resolve_graph_contract(
        graph_release,
        graph_release_sha256=str(payload.get("graph_release_sha256") or ""),
        require_sha256=graph_release is not None,
    )
    if expected_release is None:
        return returned
    expected = resolve_graph_contract(expected_release)
    if not returned.has_release:
        raise ValueError("Edge discovery omitted the requested graph release provenance")
    if returned.sha256 != expected.sha256 or returned.release != expected.release:
        raise ValueError("Edge discovery returned a different graph release than requested")
    return returned


def validate_v4_node_descriptor(item: object, *, context: str) -> dict[str, Any]:
    """Validate one Edge-owned exact node and routing descriptor."""

    if not isinstance(item, dict):
        raise ValueError(f"{context} must be a typed node descriptor")
    descriptor = dict(item)
    node_id = str(descriptor.get("node_id") or "").strip()
    if not node_id:
        raise ValueError(f"{context} is missing node_id")
    driver_ref = descriptor.get("driver_ref")
    if not isinstance(driver_ref, dict):
        raise ValueError(f"{context} is missing driver_ref")
    kind = str(driver_ref.get("kind") or "").strip()
    if kind == "symbol":
        if str(driver_ref.get("graph_node_id") or "").strip() != node_id:
            raise ValueError(f"{context} symbol driver_ref conflicts with node_id")
        symbol = str(driver_ref.get("symbol") or "").strip()
        if not symbol:
            raise ValueError(f"{context} symbol driver_ref is missing symbol")
        if descriptor.get("ticker") is not None and str(
            descriptor.get("ticker") or ""
        ).strip() != symbol:
            raise ValueError(f"{context} ticker conflicts with symbol driver_ref")
    elif kind == "canonical_node":
        if str(driver_ref.get("node_id") or "").strip() != node_id:
            raise ValueError(f"{context} canonical driver_ref conflicts with node_id")
    else:
        raise ValueError(f"{context} has unsupported driver_ref kind '{kind}'")
    expected_digest = hashlib.sha256(
        json.dumps(
            driver_ref,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if str(descriptor.get("driver_ref_sha256") or "").strip() != expected_digest:
        raise ValueError(f"{context} driver_ref_sha256 does not match driver_ref")
    return descriptor


def validate_v4_target_identity(
    *,
    target_asset: str,
    target_node: str,
    target_ref: object,
    ticker: str | None = None,
    check_ticker: bool = False,
    require_symbol: bool = True,
) -> tuple[str, str, dict[str, Any]]:
    """Validate typed target identity and its one-way flat projections."""

    descriptor = validate_v4_node_descriptor(target_ref, context="V4 target_ref")
    driver_ref = descriptor["driver_ref"]
    kind = driver_ref.get("kind")
    if require_symbol and kind != "symbol":
        raise ValueError("Abel Invest V4 session targets must use a symbol driver_ref")
    asset = str(driver_ref.get("symbol") or "").strip() if kind == "symbol" else ""
    node_id = str(descriptor.get("node_id") or "").strip()
    if str(descriptor.get("ticker") or "").strip() != asset:
        raise ValueError("V4 target_ref ticker conflicts with its symbol driver_ref")
    if str(target_asset or "").strip() != asset:
        raise ValueError("V4 target asset conflicts with target_ref")
    if check_ticker and str(ticker or "").strip() != asset:
        raise ValueError("V4 ticker conflicts with target_ref")
    if str(target_node or "").strip() != node_id:
        raise ValueError("V4 target_node conflicts with target_ref")
    return asset, node_id, descriptor


def validate_v4_selected_entries(entries: list[dict[str, Any]]) -> None:
    """Validate exact routing identity for every selected V4 driver."""

    for entry in entries:
        validate_v4_node_descriptor(entry, context="V4 selected driver")


def load_graph_release(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("graph release must be a JSON mapping")
    return resolve_graph_contract(payload).release or {}


def freeze_graph_release(session: Path, payload: dict) -> Path:
    normalized = resolve_graph_contract(payload).release
    if normalized is None:
        raise ValueError("cannot freeze an empty graph release")
    path = session / GRAPH_RELEASE_FILENAME
    path.write_text(
        json.dumps(normalized, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
