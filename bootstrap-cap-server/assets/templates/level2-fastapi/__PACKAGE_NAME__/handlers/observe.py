from __future__ import annotations

from fastapi import Request

from cap.core.contracts import ObservePredictRequest
from cap.server import (
    CAPHandlerSuccessSpec,
    CAPProvenanceHint,
    CAPVerbRegistry,
    OBSERVE_PREDICT_CONTRACT,
)

from .common import get_graph_adapter, validate_graph_ref


def register_observe_handlers(registry: CAPVerbRegistry) -> None:
[[IF_INCLUDE_PREDICTOR]]
    @registry.core(OBSERVE_PREDICT_CONTRACT)
    def observe_predict(payload: ObservePredictRequest, request: Request) -> CAPHandlerSuccessSpec:
        validate_graph_ref(payload)
        graph_adapter = get_graph_adapter(request)
        prediction = graph_adapter.predict(payload.params.target_node)
        return CAPHandlerSuccessSpec(
            result={
                "target_node": payload.params.target_node,
                "prediction": prediction["prediction"],
                "drivers": prediction["drivers"],
            },
            provenance_hint=CAPProvenanceHint(algorithm="__RUNTIME_ALGORITHM__"),
        )
[[END_IF_INCLUDE_PREDICTOR]]
    return None
