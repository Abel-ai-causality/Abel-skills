---
name: bootstrap-cap-server
description: Bootstrap or scaffold a CAP-compatible server from a user-provided causal graph or runtime. Use when Codex needs to generate a new CAP server project, wrap an existing graph or causal API behind `/.well-known/cap.json` and `POST /cap`, choose an honest CAP conformance level, build a capability card, register core verbs, or create a FastAPI CAP skeleton with tests and example requests. Default to the published Python package `cap-protocol[server]` rather than local repo imports.
---

# Bootstrap CAP Server

Bootstrap a generic CAP server over a user-provided graph or causal runtime. Prefer the smallest honest public surface first, then expand only if the user's graph actually supports stronger semantics.

## Workflow

Read `references/workflow.md` first. Use it as the active loop.

## Rules

- Treat the user's graph or runtime as the primary source of truth.
- Treat the CAP docs and Python SDK as the public contract and implementation baseline.
- Treat graph-computer only as an architecture reference for generic patterns such as registry wiring, adapter boundaries, and capability-card derivation.
- Default to `pip install "cap-protocol[server]"`. Do not generate code that imports from a local checkout of `python-sdk/`.
- Default to CAP core verbs only. Do not introduce vendor extensions unless the user explicitly asks for them.
- Default to CAP-layer scaffolding only. Do not treat auth, gatewaying, tenancy, rate limits, or product access control as part of the main bootstrap workflow.
- Before generating files, explicitly resolve where the new project should live and whether the user wants a fresh git repository initialized there.
- Before generating files, ask the required bootstrap questions explicitly. Do not replace unanswered user choices with silent defaults.
- Start from Level 1 unless the user's graph and runtime clearly justify Level 2.
- Never claim Level 3.
- Be proactive. When key runtime details are missing, ask short concrete questions and propose the next viable options instead of waiting for the user to infer the protocol gap alone.
- If the user has graph structure but no SCM or intervention backend, explicitly ask how they want to enable `observe.predict` and `intervene.do`, then generate the scaffold around the option they choose.
- Keep server-specific execution choices out of CAP core params unless the protocol already standardizes them.
- Prefer using `scripts/bootstrap_cap_server.py` plus the bundled templates when the user wants a brand-new project scaffold.

## Bootstrap Loop

### 1. Ask The Required Bootstrap Questions

Before you generate anything, ask these questions directly if the user has not already answered them:

- Where should the new CAP server project be created?
- What should the project folder be called?
- Should the generated folder also run `git init`?
- Does the existing graph already support `observe.predict`?
- Does the existing graph or runtime already support `intervene.do`?

If prediction or intervention support does not already exist, ask one more explicit follow-up:

- Do you want the scaffold to stay structural-only?
- Do you want an `observe.predict` adapter stub for a model you will add later?
- Do you want an `intervene.do` adapter stub for an SCM, simulator, or internal service you will add later?

Do not skip these questions by inferring answers from nearby files unless the user has already stated the choice clearly.

### 2. Classify The User Runtime

Identify which input the user actually has. If unclear, read `references/user-graph-shapes.md`.

Classify into one of:

- topology only
- weighted or lagged graph
- graph plus observational predictor
- graph plus executable structural mechanisms
- existing causal API that should be wrapped as CAP

### 3. Choose The Honest Surface

Read `references/conformance-matrix.md`.

Pick the smallest public surface that the runtime can support honestly:

- topology-first structural server
- Level 1 observational server
- Level 2 intervention server

If the runtime is ambiguous, choose the lower level and say what is missing for the higher one.

If the user only has a graph and wants stronger verbs, do not stop at a refusal. Proactively offer upgrade paths such as:

- add an observational predictor now and mount `observe.predict`
- expose `intervene.do` as a stub around a future simulator or SCM adapter
- keep the public surface structural today and mark the missing backend clearly

Confirm which path they want before generating files.

### 4. Resolve Project Placement

Use the user's explicit answer for:

- target parent directory
- project folder name
- whether to run `git init`

Do not silently assume the current working directory is correct, and do not implicitly initialize a repository.

### 5. Generate The Server Shape

Read `references/python-sdk-patterns.md`.

If the user wants a fresh scaffold, start from the bundled templates:

- `assets/templates/level1-fastapi`
- `assets/templates/level2-fastapi`

Generate them with:

```bash
python3 scripts/bootstrap_cap_server.py my-cap-server --output-dir /target/path --level 1
```

Useful scaffold flags:

- `--graph-ref-mode none|optional|required`
- `--graph-id <id>`
- `--graph-version <version>`
- `--with-paths` for Level 1 structural path support
- `--predictor-mode mounted|stub|none`
- `--intervention-mode mounted|stub|none`
- `--git-init` if the user wants the generated project folder initialized as a new git repo

Keep auth out of the default path. If the user explicitly wants a placeholder auth scaffold, `scripts/bootstrap_cap_server.py` also supports advanced overrides such as `--auth api-key`, but that is not the main job of this skill.

Generate a small FastAPI server with:

- `GET /.well-known/cap.json`
- `POST /cap`
- `CAPVerbRegistry`
- explicit handler registration
- a capability card derived from the mounted surface
- a runtime adapter layer that isolates the user's graph operations from CAP handlers
- smoke tests and example `curl` or Python client calls

### 6. Keep The Runtime Adapter Explicit

Read `references/implementation-patterns.md` when deciding project layout.

Define a thin adapter interface around the user's runtime before filling handlers. At minimum, decide:

- node id format
- whether multiple graphs exist
- whether `context.graph_ref` is required or optional
- how neighbors, blanket membership, paths, predictions, and interventions are computed
- what provenance fields can be stated honestly

If prediction or intervention support does not exist yet, still make the missing adapter boundary explicit so the generated scaffold shows exactly where the user will plug in:

- an observational predictor
- an SCM or simulator
- a product-specific causal API wrapper

### 7. State The Non-Claims

Before finalizing, list what the generated server does not claim. Typical examples:

- no executable mechanisms, so no `intervene.do`
- no multi-graph selection yet, so `graph_ref` is accepted only as future-facing or omitted entirely
- no identified causal effect claim, only observational or structural semantics
- no Level 3 counterfactual support

### 8. Deliver Concrete Output

Produce code, not only advice. For non-trivial requests, prefer:

- project tree
- main server module
- runtime adapter interface
- capability-card builder
- tests
- install and run commands
- one or two example requests

## References

- `references/workflow.md` — primary decision loop
- `references/user-graph-shapes.md` — classify the user's graph or runtime
- `references/conformance-matrix.md` — map graph capability to public verbs and CAP level
- `references/python-sdk-patterns.md` — published SDK imports, registry, dispatcher, and capability-card patterns
- `references/implementation-patterns.md` — generic server architecture patterns distilled from graph-computer without Abel-specific public details

## Bundled Resources

- `scripts/bootstrap_cap_server.py` — copy and render the Level 1 or Level 2 project template
- `assets/templates/level1-fastapi` — minimal runnable CAP Level 1 FastAPI scaffold
- `assets/templates/level2-fastapi` — minimal runnable CAP Level 2 FastAPI scaffold
