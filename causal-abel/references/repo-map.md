# Repository Map

Read this first when using the skill for implementation work inside the wrapper repo.

## Core Boundary

- `abel_cap_server/`: Abel-specific CAP wrapper assembly.
- `cap_protocol/`: reusable CAP protocol contracts, envelopes, registry, FastAPI dispatch glue.
- Upstream Abel compute layer is not implemented here. Do not add new causal computation in this repo.

## Files To Start With

- `abel_cap_server/main.py`: app assembly and shared wiring.
- `abel_cap_server/api/meta.py`: root metadata and `/.well-known/cap.json`.
- `abel_cap_server/api/v1/endpoints/cap_dispatch.py`: unified `POST /api/v1/cap` entrypoint.
- `abel_cap_server/cap/catalog.py`: registry wiring, supported verbs, capability-card assembly.
- `abel_cap_server/cap/service.py`: CAP service dispatch surface.
- `abel_cap_server/cap/handlers.py`: request-driven handlers pulling `CapService` from app state.
- `abel_cap_server/cap/adapters/`: request/response mapping plus disclosure shaping.
- `abel_cap_server/cap/errors.py`: Abel-specific upstream error translation policy.
- `abel_cap_server/clients/abel_gateway_client.py`: all upstream gateway HTTP calls.
- `tests/test_cap_graph.py`: primary contract, adapter, card, and gateway passthrough tests.

## Change Routing

- Change CAP-generic DTOs or envelopes: inspect `cap_protocol/core/`.
- Change dispatch mechanics or success/error response glue: inspect `cap_protocol/server/`.
- Change Abel-only response semantics or extension DTOs: inspect `abel_cap_server/cap/contracts/` and `abel_cap_server/cap/adapters/`.
- Change public capability metadata: inspect `abel_cap_server/cap/catalog.py`.
- Change disclosure rules: inspect `abel_cap_server/cap/disclosure.py` and adapter sanitization helpers.

## Current Public Surface

Core verbs:
- `meta.capabilities`
- `observe.predict`
- `intervene.do`
- `graph.neighbors`
- `graph.markov_blanket`
- `graph.paths`

Convenience verbs:
- `traverse.parents`
- `traverse.children`

Abel extension verbs:
- `extensions.abel.validate_connectivity`
- `extensions.abel.markov_blanket`
- `extensions.abel.counterfactual_preview`
- `extensions.abel.intervene_time_lag`

## See Also

- `../SKILL.md` for the short agent-facing framework
- `capability-layers.md` for how much of the stack to expose
- `verb-change-checklist.md` for edit order and gateway mapping checks
