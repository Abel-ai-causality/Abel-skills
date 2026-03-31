from __future__ import annotations

from cap.core import (
    CAPABILITY_CARD_SCHEMA_URL,
    CapabilityAuthentication,
    CapabilityCard,
    CapabilityCausalEngine,
    CapabilityDetailedCapabilities,
    CapabilityDisclosurePolicy,
    CapabilityProvider,
    CapabilityStructuralMechanisms,
    CapabilitySupportedVerbs,
)
from cap.core.canonical import (
    ASSUMPTION_ACYCLICITY,
    REASONING_MODE_OBSERVATIONAL_PREDICTION,
    REASONING_MODE_SCM_SIMULATION,
    REASONING_MODE_STRUCTURAL_SEMANTICS,
)
from cap.server import CAPVerbRegistry

from . import __version__
from .config import APP_NAME
from .graph_metadata import build_graph_metadata


def build_capability_card(
    registry: CAPVerbRegistry,
    *,
    public_base_url: str,
) -> CapabilityCard:
    return CapabilityCard(
        schema_url=CAPABILITY_CARD_SCHEMA_URL,
        name=APP_NAME,
        description="__DESCRIPTION__",
        version=__version__,
        provider=CapabilityProvider(
            name="__SERVER_TITLE__",
            url="https://example.com",
        ),
        endpoint=f"{public_base_url.rstrip('/')}/cap",
        conformance_level=__CONFORMANCE_LEVEL__,
        supported_verbs=CapabilitySupportedVerbs(
            core=registry.verbs_for_surface("core"),
            convenience=registry.verbs_for_surface("convenience"),
        ),
        causal_engine=CapabilityCausalEngine(
            family="user_runtime_adapter",
            algorithm="__RUNTIME_ALGORITHM__",
            supports_time_lag=False,
            supports_instantaneous=False,
            structural_mechanisms=CapabilityStructuralMechanisms(
                available=__STRUCTURAL_MECHANISMS_AVAILABLE__,
                families=__STRUCTURAL_MECHANISM_FAMILIES_EXPR__,
                mechanism_override_supported=False,
                counterfactual_ready=False,
            ),
        ),
        detailed_capabilities=CapabilityDetailedCapabilities(
            graph_discovery=False,
            graph_traversal=True,
            temporal_multi_lag=False,
            effect_estimation=__EFFECT_ESTIMATION__,
            intervention_simulation=__INTERVENTION_SIMULATION__,
            counterfactual_scm=False,
            latent_confounding_modeled=False,
            partial_identification=False,
            uncertainty_quantified=False,
        ),
        assumptions=__ASSUMPTIONS_EXPR__,
        reasoning_modes_supported=__REASONING_MODES_SUPPORTED_EXPR__,
        graph=build_graph_metadata(),
        authentication=CapabilityAuthentication(type="__AUTH_TYPE__", details=__AUTH_DETAILS_EXPR__),
        access_tiers=[],
        disclosure_policy=CapabilityDisclosurePolicy(
            hidden_fields=[],
            default_response_detail="full",
            notes=__DISCLOSURE_NOTES_EXPR__,
        ),
        extensions={},
    )
