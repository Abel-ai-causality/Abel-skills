from __future__ import annotations

from typing import cast

from fastapi import Request

from cap.server import CAPAdapterError

from ..adapters.graph_adapter import GraphAdapter
from ..config import GRAPH_ID, GRAPH_VERSION


def get_graph_adapter(request: Request) -> GraphAdapter:
    return cast(GraphAdapter, request.app.state.graph_adapter)


__GRAPH_REF_HELPER__
