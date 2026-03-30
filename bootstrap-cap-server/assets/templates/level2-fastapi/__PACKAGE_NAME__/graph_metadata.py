from __future__ import annotations

from cap.core import CapabilityGraphMetadata


def build_graph_metadata() -> CapabilityGraphMetadata:
    return CapabilityGraphMetadata(
        domains=["replace-me"],
        node_count=4,
        edge_count=3,
        node_types=["generic_metric"],
        edge_types_supported=["directed_causal_link"],
        graph_representation="user_defined_graph",
        update_frequency="user_defined",
        temporal_resolution=None,
        coverage_description="Replace this metadata with the real graph or causal surface description.",
    )
