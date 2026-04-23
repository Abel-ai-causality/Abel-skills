# Runtime Legality And Safety

The branch-default safety story is no longer "remember every possible
`.shift(1)` rule by hand".

The safety story is:

- the system materializes the runtime world in `inputs/`
- strategy code reads market data only through `DecisionContext`
- strategy code emits next-position intent, not already-effective exposure
- semantic preflight explains visibility or timing violations before a recorded round

Any strategy that uses information it could not have seen at decision time is
still invalid. What changes is where we place the burden: on the runtime
contract first, not on a giant folklore checklist.

## Authoring Contract

1. Implement `compute_decisions(self, ctx)`.
2. Read the target through `ctx.target.series(...)`.
3. Read auxiliary feeds through `ctx.feed(name)...`.
4. Return `ctx.decisions(next_position)`.

That is the legal authoring surface for branch-default strategies.

## System-Owned Inputs

Treat these files as runtime facts supplied by the system:

- `inputs/runtime_profile.json`
- `inputs/execution_constraints.json`
- `inputs/data_manifest.json`
- `inputs/context_guide.md`
- `inputs/probe_samples.json`

The strategy should not try to rediscover or override them in code. Inspect
them, then write against the world they describe.

## What Not To Do

- do not call raw data helpers from inside `compute_decisions()`
- do not hand-roll alignment by reaching around `DecisionContext`
- do not emit an already-effective `position[t]` series when the contract asks
  for `next_position`
- do not treat a suspiciously good backtest as valid before semantic preflight
  and execution semantics agree

## Why This Replaces The Old Rule Folklore

Sometimes the safe transformation really is a lag. Sometimes it is:

- an as-of read onto the target calendar
- a bounded point-in-time history window
- a native feed interval between two timestamps
- a walk-forward train/infer split

The framework should help the agent express those legal reads directly instead
of collapsing every situation into "add `.shift(1)` everywhere".

## How To Use The Feedback Loop

1. Run `abel-alpha prepare-branch --branch ...`.
2. Inspect `context_guide.md`, `data_manifest.json`, and `probe_samples.json`.
3. Edit `engine.py` against `DecisionContext`.
4. Run `abel-alpha debug-branch --branch ...`.
5. Read the semantic verdict, warnings, and sampled traces.
6. Only then decide whether `run-branch` is warranted.

## Static Checks

Static and regex-style look-ahead checks may still exist as diagnostics, but
they are not the main contract. Their job is to provide extra warning signals,
not to define strategy legality by themselves.

## Common Failure Meanings

- raw-helper error: the strategy tried to bypass `DecisionContext`
- shape mismatch: `ctx.decisions(next_position)` received the wrong length or type
- semantic blocker: the strategy assumptions about feed visibility or execution
  timing do not match the runtime
- clipped output: the strategy asked for positions outside declared execution
  constraints
