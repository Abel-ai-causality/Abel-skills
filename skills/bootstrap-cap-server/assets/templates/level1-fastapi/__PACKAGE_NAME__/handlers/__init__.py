from __future__ import annotations

from cap.server import CAPVerbRegistry

from .graph import register_graph_handlers
from .meta import register_meta_handlers
from .observe import register_observe_handlers


def build_registry() -> CAPVerbRegistry:
    registry = CAPVerbRegistry()
    register_meta_handlers(registry)
    register_graph_handlers(registry)
    register_observe_handlers(registry)
    return registry
