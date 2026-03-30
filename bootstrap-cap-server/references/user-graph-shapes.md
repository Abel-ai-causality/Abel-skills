# User Graph Shapes

Use this file to classify what the user already has before choosing verbs or conformance level.

## 1. Topology Only

The user has:

- nodes
- directed edges
- maybe node or edge labels

The user does not have:

- predictive model
- executable mechanisms
- intervention engine

Good fit:

- `graph.neighbors`
- `graph.markov_blanket`
- optional `graph.paths`

If the user still wants `observe.predict` or `intervene.do`, the skill should not just say no. It should ask whether to:

- keep the public surface structural-only
- scaffold a predictor adapter to fill later
- scaffold an intervention adapter or SCM boundary to fill later

## 2. Weighted Or Lagged Graph

The user has:

- topology
- edge weights, lags, or structural scores

This still does not imply:

- observational prediction support
- intervention support

Use the extra metadata as disclosure or path detail, not as permission to overclaim causality.

If the user wants stronger semantics, ask what extra runtime they already have or plan to add. Edge weights alone are not enough.

## 3. Graph Plus Observational Predictor

The user has:

- graph structure
- an observational model that predicts a target from graph-local context

Good fit:

- Level 1 surface
- `observe.predict`

Stay observational unless there is a real intervention backend.

## 4. Graph Plus Executable Structural Mechanisms

The user has:

- graph structure
- fitted or executable node mechanisms
- a real way to simulate or estimate interventions

Good fit:

- Level 2 surface
- `intervene.do`

Still keep Level 3 off the table.

## 5. Existing Causal API

The user may not have a graph object at all. Instead they already have:

- REST endpoints
- internal service methods
- model functions

In this case, the bootstrap job is to wrap the existing runtime behind CAP contracts rather than to rebuild the runtime.

## Classification Heuristics

Ask these questions:

- Can you list direct parents or children of a node?
- Can you enumerate paths between nodes?
- Can you predict a node observationally?
- Can you simulate or estimate an intervention?
- Can you choose among multiple named graphs?

If the answer to prediction or intervention is "not yet", ask one more proactive question:

- Do you want the generated scaffold to include a clear adapter stub for that future capability?

Map the answers to the smallest matching shape above.
