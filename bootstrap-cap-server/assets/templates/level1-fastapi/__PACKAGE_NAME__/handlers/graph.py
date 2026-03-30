from __future__ import annotations

from fastapi import Request

from cap.core import IDENTIFICATION_STATUS_NOT_APPLICABLE, REASONING_MODE_STRUCTURAL_SEMANTICS
[[IF_INCLUDE_PATHS]]
from cap.core.contracts import GraphPathsRequest
[[END_IF_INCLUDE_PATHS]]
from cap.server import (
    CAPHandlerSuccessSpec,
    CAPProvenanceHint,
    CAPVerbRegistry,
    GRAPH_MARKOV_BLANKET_CONTRACT,
    GRAPH_NEIGHBORS_CONTRACT,
[[IF_INCLUDE_PATHS]]
    GRAPH_PATHS_CONTRACT,
[[END_IF_INCLUDE_PATHS]]
)

from .common import get_graph_adapter, validate_graph_ref


def register_graph_handlers(registry: CAPVerbRegistry) -> None:
    @registry.core(GRAPH_NEIGHBORS_CONTRACT)
    def graph_neighbors(payload, request: Request) -> CAPHandlerSuccessSpec:
        validate_graph_ref(payload)
        graph_adapter = get_graph_adapter(request)
        neighbors, total = graph_adapter.neighbors(
            node_id=payload.params.node_id,
            scope=payload.params.scope,
            max_neighbors=payload.params.max_neighbors,
        )
        return CAPHandlerSuccessSpec(
            result={
                "node_id": payload.params.node_id,
                "scope": payload.params.scope,
                "neighbors": [
                    {"node_id": item.node_id, "roles": item.roles}
                    for item in neighbors
                ],
                "total_candidate_count": total,
                "truncated": total > len(neighbors),
                "edge_semantics": "direct_structural_neighbor",
                "reasoning_mode": REASONING_MODE_STRUCTURAL_SEMANTICS,
                "identification_status": IDENTIFICATION_STATUS_NOT_APPLICABLE,
                "assumptions": [],
            },
            provenance_hint=CAPProvenanceHint(algorithm="__RUNTIME_ALGORITHM__"),
        )

    @registry.core(GRAPH_MARKOV_BLANKET_CONTRACT)
    def graph_markov_blanket(payload, request: Request) -> CAPHandlerSuccessSpec:
        validate_graph_ref(payload)
        graph_adapter = get_graph_adapter(request)
        neighbors, total = graph_adapter.markov_blanket(
            node_id=payload.params.node_id,
            max_neighbors=payload.params.max_neighbors,
        )
        return CAPHandlerSuccessSpec(
            result={
                "node_id": payload.params.node_id,
                "neighbors": [
                    {"node_id": item.node_id, "roles": item.roles}
                    for item in neighbors
                ],
                "total_candidate_count": total,
                "truncated": total > len(neighbors),
                "edge_semantics": "markov_blanket_membership",
                "reasoning_mode": REASONING_MODE_STRUCTURAL_SEMANTICS,
                "identification_status": IDENTIFICATION_STATUS_NOT_APPLICABLE,
                "assumptions": [],
            },
            provenance_hint=CAPProvenanceHint(algorithm="__RUNTIME_ALGORITHM__"),
        )

[[IF_INCLUDE_PATHS]]
    @registry.core(GRAPH_PATHS_CONTRACT)
    def graph_paths(payload: GraphPathsRequest, request: Request) -> CAPHandlerSuccessSpec:
        validate_graph_ref(payload)
        graph_adapter = get_graph_adapter(request)
        paths, total = graph_adapter.paths(
            source_node_id=payload.params.source_node_id,
            target_node_id=payload.params.target_node_id,
            max_paths=payload.params.max_paths,
        )
        return CAPHandlerSuccessSpec(
            result={
                "source_node_id": payload.params.source_node_id,
                "target_node_id": payload.params.target_node_id,
                "connected": total > 0,
                "path_count": total,
                "paths": paths,
                "reasoning_mode": REASONING_MODE_STRUCTURAL_SEMANTICS,
                "identification_status": IDENTIFICATION_STATUS_NOT_APPLICABLE,
                "assumptions": [],
            },
            provenance_hint=CAPProvenanceHint(algorithm="__RUNTIME_ALGORITHM__"),
        )
[[END_IF_INCLUDE_PATHS]]
