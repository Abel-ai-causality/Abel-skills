from __future__ import annotations

from fastapi import Request

from cap.core import (
    ASSUMPTION_ACYCLICITY,
    ASSUMPTION_LINEARITY,
    ASSUMPTION_MECHANISM_INVARIANCE_UNDER_INTERVENTION,
    IDENTIFICATION_STATUS_NOT_FORMALLY_IDENTIFIED,
)
from cap.core.canonical import REASONING_MODE_SCM_SIMULATION
from cap.server import (
    CAPHandlerSuccessSpec,
    CAPProvenanceHint,
    CAPVerbRegistry,
    INTERVENE_DO_CONTRACT,
)

from .common import get_graph_adapter, validate_graph_ref


def register_intervene_handlers(registry: CAPVerbRegistry) -> None:
[[IF_INCLUDE_INTERVENTION]]
    @registry.core(INTERVENE_DO_CONTRACT)
    def intervene_do(payload, request: Request) -> CAPHandlerSuccessSpec:
        validate_graph_ref(payload)
        graph_adapter = get_graph_adapter(request)
        effect = graph_adapter.intervene(
            treatment_node=payload.params.treatment_node,
            treatment_value=payload.params.treatment_value,
            outcome_node=payload.params.outcome_node,
        )
        return CAPHandlerSuccessSpec(
            result={
                "outcome_node": payload.params.outcome_node,
                "effect": effect,
                "reasoning_mode": REASONING_MODE_SCM_SIMULATION,
                "identification_status": IDENTIFICATION_STATUS_NOT_FORMALLY_IDENTIFIED,
                "assumptions": [
                    ASSUMPTION_ACYCLICITY,
                    ASSUMPTION_LINEARITY,
                    ASSUMPTION_MECHANISM_INVARIANCE_UNDER_INTERVENTION,
                ],
            },
            provenance_hint=CAPProvenanceHint(
                algorithm="__RUNTIME_ALGORITHM__",
                mechanism_family_used="__MECHANISM_FAMILY__",
            ),
        )
[[END_IF_INCLUDE_INTERVENTION]]
    return None
