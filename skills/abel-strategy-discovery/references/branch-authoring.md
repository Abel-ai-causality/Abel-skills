# Branch Authoring

Use this reference after the workspace is ready and you are moving from
workspace setup into session and branch work.

## Branch Model

- `discovery.json` is only the session candidate snapshot
- `readiness.json` is only the session coverage/advisory report
- `branch.yaml` defines the branch runtime intent
- `prepare-branch` resolves inputs, writes the branch contract, and warms edge
  cache before a recorded round
- `debug-branch` is the semantic preflight step
- `run-branch` should consume prepared branch inputs, not invent them at runtime
- session `backtest_start` is the default research target; `branch.yaml.requested_start` may override it explicitly

Discovery gives leads, not answers. Readiness gives coverage clues, not
permission. A branch is where the research becomes a falsifiable bet.

## What `prepare-branch` Produces

The branch contract is materialized under `inputs/`:

- `runtime_profile.json`
- `execution_constraints.json`
- `data_manifest.json`
- `context_guide.md`
- `probe_samples.json`
- `dependencies.json`

Those files are the system-owned description of the runtime world. The agent
should inspect them before changing strategy logic.

## What To Do

- state a branch thesis clearly
- prepare the branch inputs
- inspect the prepared inputs
- write `engine.py`
- read semantic preflight before recording a round
- interpret the result honestly
- decide the next branch move

Alpha owns the bookkeeping so the branch can focus on mechanism, not file
management theater.

## Writing `engine.py`

Write against the branch-default contract:

- implement `compute_decisions(self, ctx)`
- inspect `ctx.target.series("close")` for the tradeable target
- inspect `ctx.feed(name).native_series(...)` for native feed cadence
- inspect `ctx.feed(name).asof_series(...)` when you need target-calendar as-of values
- inspect `ctx.points()` when you need point-level reasoning or debugging
- return `ctx.decisions(next_position)`

Prefer prepared branch inputs over discovery-side inference:

- inspect `inputs/context_guide.md`
- inspect `inputs/data_manifest.json`
- inspect `inputs/probe_samples.json`
- treat `runtime_profile.json` and `execution_constraints.json` as system-owned
  runtime facts, not something the strategy should guess or re-declare

Do not parse relative workspace files manually when the injected context already
contains the prepared branch payload.

Do not reach for raw loaders or ad hoc alignment helpers from inside
`compute_decisions()`. If you cannot express a read through `DecisionContext`,
surface that mismatch and fix the framework or branch inputs instead of writing
around the contract.

## Recommended Loop

1. State the branch thesis in `branch.yaml`.
2. Run `prepare-branch`.
3. Inspect `inputs/context_guide.md`, `probe_samples.json`, and `data_manifest.json`.
4. Implement or revise `compute_decisions(self, ctx)`.
5. Run `abel-alpha debug-branch --branch ...`.
6. Read the semantic verdict and traces.
7. Only then decide whether `run-branch` is justified.

## Readiness

Keep readiness advisory:

- use it to understand coverage
- do not treat it as a hard permission system
- do not force all drivers to share the latest common start unless the branch thesis truly requires strict overlap
- do not confuse session start guidance with the branch's explicit requested start

## Research Judgment

- start causal-first; correlation-derived signals may help, but do not replace Abel discovery as the main search prior
- explore means new information, a new transmission path, or a genuinely different mechanism
- weird low-attention parents are not automatically noise; explain them before discarding them
- treat semantic failure as a signal about visibility or timing assumptions
- treat metric failure as direction, not as a prompt to hack metrics
- serial compounding beats pre-declaring a large experiment grid
- stop honestly when recent rounds are no longer improving and no high-quality new direction remains
