# Implementation Patterns

This file distills generic server-architecture patterns from the CAP docs and the graph-computer implementation style. Do not copy Abel-specific public details into generated servers.

## Keep Public Surface Wiring Central

Prefer one place that shows:

- mounted verbs
- request and response models
- capability-card derivation
- extension namespaces, if any

This makes it easier to audit whether the public surface matches the capability card.

## Separate CAP Boundary From Runtime Logic

Use layers with clear roles:

- CAP handlers: FastAPI boundary
- CAP registry and capability-card builder: public surface definition
- runtime adapter or service: calls into the user's graph or causal engine

This keeps CAP semantics stable even if the underlying runtime changes.

## Derive Disclosure From Reality

Build:

- capability card from the mounted registry
- `meta.methods` from the same mounted registry
- assumptions and reasoning-mode claims from actual runtime behavior

Avoid hand-maintained marketing lists of verbs or capabilities.

## Keep Vendor-Specific Features Out Of Core By Default

If the user has custom operations such as:

- graph import
- domain-specific search
- product-specific rollout knobs

keep them out of CAP core unless the user explicitly wants a vendor extension layer.

Apply the same rule to product perimeter concerns such as auth or tenancy. Those can matter operationally, but they are not part of the CAP semantics this skill is meant to bootstrap by default.

## Hide Unstable Engine Internals By Default

Do not expose raw engine internals just because the runtime has them.

Common examples:

- internal score tensors
- raw fitting diagnostics
- engine-specific conditioning state
- unstable edge metadata with no public semantics

Expose only what the server can explain and support as a public contract.
