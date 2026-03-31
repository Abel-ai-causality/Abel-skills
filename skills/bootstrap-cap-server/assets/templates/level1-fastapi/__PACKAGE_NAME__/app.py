from __future__ import annotations

from fastapi import FastAPI, Request

from cap.core import CapabilityCard
from cap.server import (
    CAPAdapterError,
    build_fastapi_cap_dispatcher,
    register_cap_exception_handlers,
)

from .adapters.graph_adapter import GraphAdapter
from .capability import build_capability_card
from .config import ServiceSettings
from .handlers import build_registry
from .provenance import provenance_context_provider


registry = build_registry()


__AUTH_HELPER__


def create_app() -> FastAPI:
    settings = ServiceSettings()
    graph_adapter = GraphAdapter()
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    app.state.settings = settings
    app.state.graph_adapter = graph_adapter

    dispatcher = build_fastapi_cap_dispatcher(
        registry=registry,
        provenance_context_provider=provenance_context_provider,
    )

    register_cap_exception_handlers(app)

    @app.get("/.well-known/cap.json", response_model=CapabilityCard)
    def capability_card(request: Request) -> CapabilityCard:
        return build_capability_card(registry, public_base_url=str(request.base_url))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "app_name": settings.app_name}

    @app.post("/cap")
    async def dispatch_cap(payload: dict, request: Request) -> dict:
__AUTH_ENFORCE_CALL__        return await dispatcher(payload, request)

    return app


app = create_app()
