# Workflow

Use this file as the main working loop.

## Goal

Turn a user-provided graph or causal runtime into a small, honest CAP server that exposes only the verbs the runtime can support truthfully.

This workflow is about the CAP layer, not the product perimeter. Default to no auth, no gateway, and no tenancy work unless the user explicitly asks for those.

The skill should be proactive. When the graph is missing predictive or interventional machinery, ask concise follow-up questions and propose concrete implementation options rather than only stating the limitation.

## Step 1: Ask The Required Bootstrap Questions

Before generating a new scaffold, ask these questions explicitly unless the user has already answered them:

- Which parent directory should contain the project?
- What should the project folder be called?
- Should the generated folder also run `git init`?
- What runtime shape already exists: local graph files, Python runtime, internal API, or deployed graph service?
- Does the runtime already support `observe.predict`?
- Does the runtime already support `intervene.do`?

If the answer to prediction or intervention is no or unclear, ask one direct follow-up:

- Should the scaffold stay structural-only?
- Should it include an `observe.predict` adapter stub for a future model?
- Should it include an `intervene.do` adapter stub for a future SCM, simulator, or internal service?

Do not silently write into the current directory, do not assume the user wants a new repository, and do not convert missing backend choices into inferred defaults.

## Step 2: Resolve Project Placement

Use the user's explicit answer for project location, folder name, and `git init`.

## Step 3: Identify The Input Runtime

Ask or infer:

- What runtime shape already exists?
- If it is file-backed, what concrete node and edge files already exist?
- Is it just topology, or does it include weights, lags, predictors, or structural mechanisms?
- Does the user want a new project scaffold, or to wrap an existing API or service?
- What graph version should the scaffold disclose in provenance and capability metadata?

If the shape is unclear, read `user-graph-shapes.md`.

## Step 4: Set The Honesty Boundary

Choose the smallest surface first.

Default progression:

- structural only: `meta.capabilities`, `meta.methods`, `graph.neighbors`, `graph.markov_blanket`, optional `graph.paths`
- observational: structural surface plus `observe.predict`
- interventional: observational surface plus `intervene.do`

Do not add `intervene.do` just because the user wants it. Add it only if the runtime actually supports intervention semantics honestly.

If the user does not yet have the runtime needed for `observe.predict` or `intervene.do`, explicitly ask what they want to do next. Good follow-up patterns:

- "Do you want the scaffold to stay structural-only for now?"
- "Do you want me to generate an `observe.predict` adapter stub for a model you will plug in?"
- "Do you want me to generate an `intervene.do` adapter boundary for an SCM or simulator you will add later?"

Do not wait passively for the user to infer these options.

Before moving on, give the user a short checkpoint that states:

- planned `conformance_level`
- mounted verbs and any stub-only upgrade paths
- capability-card fields that materially change, especially `supported_verbs`, `reasoning_modes_supported`, `graph`, and `authentication`
- explicit non-claims such as omitted `observe.predict`, omitted `intervene.do`, or no `context.graph_ref` requirement

## Step 5: Define The Runtime Adapter

Before generating handlers, define a thin adapter contract such as:

- `get_neighbors(node_id, scope, max_neighbors)`
- `get_markov_blanket(node_id, max_neighbors)`
- `get_paths(source_node_id, target_node_id, max_paths)`
- `predict_observational(target_node)`
- `intervene(treatment_node, treatment_value, outcome_node)`

Default the adapter to one deployed graph. If a specific deployment later needs explicit graph selection or graph-version pinning, add `context.graph_ref` intentionally as server-specific request context instead of treating it as a bootstrap default.

When the user has no SCM, ask what should back stronger verbs:

- an observational model over the existing graph
- a future SCM or simulator
- an existing internal API that estimates interventions

Generate adapter stubs and TODO markers for the chosen path, but keep the capability card honest about what is actually mounted today.

## Step 6: Generate The CAP Server Skeleton

Use the published Python SDK:

```bash
uv add "cap-protocol[server]"
```

Generate:

- FastAPI app
- explicit registry setup
- `/.well-known/cap.json`
- `POST /cap`
- verb handlers
- capability-card builder
- provenance context provider
- tests

Default the generated scaffold to `authentication.type = "none"`. If the user later wants auth, that can be added as a follow-up coding change rather than as part of the core bootstrap loop.

If the user wants a clean repo for the new scaffold, run the generator with `--git-init`. Otherwise leave repository setup alone.

If the user chose a future-facing prediction or intervention path, generate the missing adapter interface and TODOs in the project so the upgrade path is visible in code, not only in prose.

Prefer expressing those choices explicitly in the generator invocation, for example:

- `--predictor-mode mounted|stub|none`
- `--intervention-mode mounted|stub|none`

## Step 7: Keep Capability Disclosure Derived

Build the capability card from the real mounted registry. Do not hand-maintain one list of verbs in code and another in docs.

At minimum disclose:

- `endpoint`
- `conformance_level`
- `supported_verbs`
- `assumptions`
- `reasoning_modes_supported`
- `graph`
- `authentication`

For default bootstrap scaffolds, disclose that the server targets one deployed graph and does not require `context.graph_ref`.

This should be surfaced to the user proactively as part of the bootstrap conversation, not only encoded in generated code.

## Step 8: Verify The Output

Verify:

- the server starts
- `GET /.well-known/cap.json` works
- `POST /cap` works for at least one discovery verb
- the claimed conformance level matches the mounted verbs
- the generated examples use package imports, not local source-tree imports

## Step 9: Finalize With Explicit Non-Claims

End with a short section that states the current limits and the upgrade path, for example:

- Level 1 only until an intervention backend exists
- one deployed graph by default; add `context.graph_ref` later only if a deployment needs explicit graph selection or version pinning
- `graph.paths` omitted until path enumeration is implemented
- no counterfactual support
- `observe.predict` or `intervene.do` scaffolded behind adapter TODOs but not mounted until the backend is real
