# Capability Layers

Use this file when the user should see more than the protocol surface and you need a consistent depth model for explanation.

The goal is progressive disclosure. Expose the shallowest layer that answers the task, then move down only if needed.

## Layer 1: Public CAP Surface

Use this layer for users asking what the server can do at the protocol level.

Primary verbs:
- `meta.capabilities`
- `observe.predict`
- `intervene.do`
- `graph.neighbors`
- `graph.markov_blanket`
- `graph.paths`
- `traverse.parents`
- `traverse.children`

Primary files:
- `abel_cap_server/cap/catalog.py`
- `abel_cap_server/api/meta.py`
- `abel_cap_server/api/v1/endpoints/cap_dispatch.py`
- `tests/test_cap_graph.py`

What to show:
- Supported verbs
- Capability-card claims
- Request/response envelope shape
- Public reasoning modes and identification status

## Layer 2: Abel Extension Surface

Use this layer when the user wants richer Abel-only capability without changing CAP core.

Extension verbs:
- `extensions.abel.validate_connectivity`
- `extensions.abel.markov_blanket`
- `extensions.abel.counterfactual_preview`
- `extensions.abel.intervene_time_lag`

Primary files:
- `abel_cap_server/cap/contracts/extensions.py`
- `abel_cap_server/cap/adapters/extensions.py`
- `abel_cap_server/cap/catalog.py`
- `tests/test_cap_graph.py`

What to show:
- Extension-specific params and result shapes
- Abel-only semantic honesty notes such as `proxy_only`, `preview_only`, and approximate semantics
- Where Abel exposes richer summaries than CAP core
- Why a capability should stay in the extension namespace instead of CAP core

## Layer 3: Abel Implementation Surface

Use this layer when the user needs to modify, verify, or debug how the server behaves.

Primary files:
- `abel_cap_server/cap/service.py`
- `abel_cap_server/cap/handlers.py`
- `abel_cap_server/cap/adapters/common.py`
- `abel_cap_server/cap/provenance.py`
- `abel_cap_server/clients/abel_gateway_client.py`
- `abel_cap_server/cap/errors.py`

What to show:
- Service method to adapter mapping
- How request headers are forwarded
- Which upstream endpoint each verb uses
- Which fields are sanitized or reduced before public response
- Which provenance hints are attached
- Which adapter errors are translated into CAP errors

## Promotion Rule

When a capability is not suitable for CAP core but is still useful to users:
- Prefer exposing it as `extensions.abel.*`
- Add explicit semantic honesty fields
- Add capability-card extension notes
- Add route and adapter tests proving the behavior

## Explain More Without Leaking More

When exposing deeper capability to skill users:
- Prefer showing contract shape, assumptions, and mapping before raw internals
- Explain hidden-field stripping and summary-safe defaults
- Do not expose forbidden internal statistics just because the skill user asked for implementation detail
- Treat tests as the canonical statement of public behavior

## See Also

- `../SKILL.md` for the short agent-facing framework
- `question-routing.md` for when to stay on graph structure versus move into richer semantics
