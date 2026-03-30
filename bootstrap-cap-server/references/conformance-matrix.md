# Conformance Matrix

Use this file to choose the public CAP surface conservatively.

## Runtime Capability To Public Surface

| Runtime capability | Safe verbs | Safe CAP level | Notes |
| --- | --- | --- | --- |
| Topology only | `meta.capabilities`, `meta.methods`, `graph.neighbors`, `graph.markov_blanket` | none or Level 1 only if observational semantics are not implied | `graph.paths` is optional if path enumeration is available |
| Weighted or lagged graph without predictor | same as topology only, optional `graph.paths` | none | Do not turn edge weights into fake observational or interventional semantics |
| Graph plus observational predictor | topology verbs plus `observe.predict` | Level 1 | Prediction should stay observational |
| Graph plus executable intervention backend | Level 1 verbs plus `intervene.do` and `graph.paths` | Level 2 | Only if intervention responses can disclose reasoning mode, identification status, and assumptions honestly |
| Full SCM with counterfactual machinery | Level 2 surface | Level 2 | CAP Level 3 is not available in `v0.2.2` |

## Proactive Upgrade Guidance

If the user wants stronger verbs than the current runtime supports, ask them which implementation path they want and generate code accordingly.

### User has only graph structure but wants `observe.predict`

Offer:

- keep the server structural-only today
- generate an observational adapter stub that they will connect to a model later
- wrap an existing internal predictor behind `observe.predict`

Only mount `observe.predict` when there is a real predictor or when the user explicitly asks for a placeholder path and accepts that the capability card must stay lower until the backend exists.

### User has no SCM but wants `intervene.do`

Offer:

- stay at structural or observational surface for now
- generate an intervention adapter boundary for a future SCM or simulator
- wrap an internal intervention-estimation service if one already exists

Do not mount `intervene.do` unless the runtime can answer it honestly. It is fine to generate the code boundary and TODOs without claiming Level 2 yet.

## Practical Gates

### `graph.neighbors`

Safe when the runtime can enumerate direct structural parents or children.

### `graph.markov_blanket`

Safe when the runtime can compute blanket membership structurally. Do not describe blanket membership as an identified interventional effect.

### `graph.paths`

Safe when the runtime can enumerate causal or structural paths between nodes without inventing unsupported edge semantics.

### `observe.predict`

Safe when the runtime can produce an observational prediction and name its drivers or upstream evidence honestly.

Do not force extra params such as mechanism family or rollout controls into CAP core requests.

### `intervene.do`

Safe only when the runtime can compute or simulate an intervention result honestly and disclose:

- `reasoning_mode`
- `identification_status`
- `assumptions`

If the runtime only has a heuristic pressure test or a product-specific intervention helper, keep it outside CAP core unless the user explicitly wants a vendor extension.

## Default Recommendation

If uncertain, bootstrap:

- Level 1 with discovery and structural verbs first
- add `observe.predict` only if the runtime already predicts
- add `intervene.do` later after the intervention backend is real
- ask one proactive follow-up when the user wants stronger verbs than the runtime currently supports
