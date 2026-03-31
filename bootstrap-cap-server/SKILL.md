---
name: bootstrap-cap-server
description: Use when Codex needs to turn an existing causal graph, causal runtime, or internal causal API into a CAP-compatible server, especially when the honest CAP surface, conformance level, or mounted verbs are unclear.
---

# Bootstrap CAP Server

Bootstrap a generic CAP server over a user-provided graph or causal runtime. Classify the runtime shape first, prefer the smallest honest public surface, then expand only if the user's graph actually supports stronger semantics.

## When to Use

- The user has an existing causal graph, runtime, or internal causal API that should expose `GET /.well-known/cap.json` and `POST /cap`.
- The user wants a fresh CAP server scaffold or wants to wrap an existing service behind CAP.
- It is unclear whether the runtime supports structural, observational, or interventional verbs honestly.
- The capability card should be derived from the mounted surface instead of maintained by hand.

## When NOT to Use

- The main task is auth, gatewaying, tenancy, rate limits, or other product-perimeter work.
- The main task is inventing vendor extensions instead of exposing CAP core verbs honestly.
- The user has no graph, runtime, or causal API yet and needs help building causal machinery from scratch first.
- The request depends on claiming Level 3 or counterfactual support.

## Workflow

Read `references/workflow.md` first. Use it as the only active bootstrap loop.

Use the supporting references only as needed:

- `references/user-graph-shapes.md` for runtime classification
- `references/conformance-matrix.md` for honest CAP surface and level selection
- `references/python-sdk-patterns.md` for published SDK imports, registry wiring, and capability disclosure
- `references/implementation-patterns.md` for adapter and project-layout patterns

## Rules

- Treat the user's graph or runtime as the primary source of truth.
- Treat the CAP docs and Python SDK as the public contract and implementation baseline.
- Treat graph-computer only as an architecture reference for generic patterns such as registry wiring, adapter boundaries, and capability-card derivation.
- Default to `uv sync --extra dev` in generated project docs and `uv run ...` for local workflow. Do not generate code that imports from a local checkout of `python-sdk/`.
- Default to CAP core verbs only. Do not introduce vendor extensions unless the user explicitly asks for them.
- Default to CAP-layer scaffolding only. Do not treat auth, gatewaying, tenancy, rate limits, or product access control as part of the main bootstrap workflow.
- Treat `context.graph_ref` as an optional CAP request-context field, not as a default multi-graph design requirement.
- Before generating files, explicitly resolve project placement and whether the generated folder should run `git init`.
- Ask the required intake questions in one grouped message by default. Do not drag the user through a long one-question-at-a-time intake unless earlier answers are missing or contradictory.
- Start from Level 1 unless the user's graph and runtime clearly justify Level 2.
- Never claim Level 3.
- Be proactive. When key runtime details are missing, ask short concrete questions and propose the next viable options instead of waiting for the user to infer the protocol gap alone.
- After setting the honesty boundary, proactively summarize the planned public CAP surface and capability-card impact before generating files.
- Infer runtime shape when the user has already described it clearly. Ask about it only when it remains ambiguous.
- In user-facing questions, avoid raw internal labels such as `observe.predict`, `intervene.do`, `none`, `stub`, and `mounted`. Ask in plain language, then map back to generator flags internally.
- In the first user-facing capability checkpoint, prefer plain-language summaries of what the server will and will not do. Mention protocol field names only when they add real value.
- Keep server-specific execution choices out of CAP core params unless the protocol already standardizes them.
- Prefer using `scripts/bootstrap_cap_server.py` plus the bundled templates when the user wants a brand-new project scaffold.

## Interaction Contract

Before scaffolding:

- resolve project parent directory, folder name, and `git init`
- infer the runtime source when possible, or ask in plain language whether the user is starting from local files, Python code, or an already-running service
- ask whether prediction or intervention already works today
- if not, ask in plain language whether those should be left out for now or scaffolded as placeholders for later
- recap the intended mounted verbs, conformance level, capability disclosure shape, and current non-claims before generating files

The exact intake wording and checkpoint format live in `references/workflow.md`.

## Quick Reference

| Need | Use |
| --- | --- |
| Full bootstrap loop | `references/workflow.md` |
| Runtime classification | `references/user-graph-shapes.md` |
| Honest CAP level and verb surface | `references/conformance-matrix.md` |
| Published SDK patterns | `references/python-sdk-patterns.md` |
| Generic adapter and layout patterns | `references/implementation-patterns.md` |
| Fresh runnable scaffold | `scripts/bootstrap_cap_server.py` plus `assets/templates/level1-fastapi` or `assets/templates/level2-fastapi` |

## Output Expectations

Produce code, not only advice. For non-trivial requests, prefer:

- project tree
- main server module
- runtime adapter interface
- capability-card builder derived from mounted verbs
- tests
- install and run commands
- one or two example requests

## Common Mistakes

- Inferring project location or `git init` instead of asking explicitly.
- Mounting `observe.predict` or `intervene.do` without a real backend or an explicit stub choice.
- Asking the user the bootstrap questions one by one when a single grouped intake would do.
- Repeating the user's runtime description back as protocol jargon instead of plain language.
- Importing from a local checkout of `python-sdk/` instead of the published package.
- Treating auth, gateway, or tenancy scaffolding as part of the default CAP bootstrap path.
- Treating `context.graph_ref` as a default multi-graph requirement instead of an optional server-specific selector.
- Hand-maintaining capability claims instead of deriving them from the mounted registry.
- Waiting for the user to ask about the capability card instead of proactively mapping mounted verbs into capability disclosure and non-claims.
- Advertising Level 2 or Level 3 semantics that the runtime cannot support honestly.

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
