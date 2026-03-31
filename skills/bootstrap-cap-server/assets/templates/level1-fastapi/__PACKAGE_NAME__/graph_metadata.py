from __future__ import annotations

from cap.core import CapabilityGraphMetadata


def build_graph_metadata() -> CapabilityGraphMetadata:
    return CapabilityGraphMetadata(
        domains=__GRAPH_DOMAINS_EXPR__,
        node_count=__GRAPH_NODE_COUNT__,
        edge_count=__GRAPH_EDGE_COUNT__,
        node_types=__GRAPH_NODE_TYPES_EXPR__,
        edge_types_supported=["directed_causal_link"],
        graph_representation="user_defined_graph",
        update_frequency="user_defined",
        temporal_resolution=None,
        coverage_description="__GRAPH_COVERAGE_DESCRIPTION__",
    )
