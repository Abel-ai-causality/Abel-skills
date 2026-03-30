from __future__ import annotations

from typing import cast

from fastapi import Request

from cap.server import CAPProvenanceContext

from .config import GRAPH_VERSION, ServiceSettings


async def provenance_context_provider(payload, request: Request) -> CAPProvenanceContext:
    del payload
    settings = cast(ServiceSettings, request.app.state.settings)
    return CAPProvenanceContext(
        graph_version=GRAPH_VERSION,
        server_name=settings.app_name,
        server_version=settings.app_version,
    )
