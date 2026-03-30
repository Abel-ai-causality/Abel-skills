from __future__ import annotations

from fastapi import Request

from cap.core.contracts import MetaCapabilitiesRequest, MetaMethodsRequest
from cap.server import CAPVerbRegistry, META_CAPABILITIES_CONTRACT, META_METHODS_CONTRACT

from ..capability import build_capability_card


def register_meta_handlers(registry: CAPVerbRegistry) -> None:
    @registry.core(META_CAPABILITIES_CONTRACT)
    def meta_capabilities(payload: MetaCapabilitiesRequest, request: Request) -> dict:
        card = build_capability_card(registry, public_base_url=str(request.base_url))
        return {
            "cap_version": payload.cap_version,
            "request_id": payload.request_id or "meta-capabilities",
            "verb": payload.verb,
            "status": "success",
            "result": card.model_dump(exclude_none=True, by_alias=True),
        }

    @registry.core(META_METHODS_CONTRACT)
    def meta_methods(payload: MetaMethodsRequest, request: Request) -> dict:
        del request
        params = payload.params
        methods = registry.list_methods(
            verbs=params.verbs if params and params.verbs else None,
            detail=params.detail if params else "compact",
            include_examples=params.include_examples if params else False,
        )
        return {
            "cap_version": payload.cap_version,
            "request_id": payload.request_id or "meta-methods",
            "verb": payload.verb,
            "status": "success",
            "result": {"methods": [item.model_dump(exclude_none=True) for item in methods]},
        }
