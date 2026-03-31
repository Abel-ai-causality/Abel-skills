from __future__ import annotations

from typing import cast

from fastapi import Request

from ..adapters.graph_adapter import GraphAdapter


def get_graph_adapter(request: Request) -> GraphAdapter:
    return cast(GraphAdapter, request.app.state.graph_adapter)
