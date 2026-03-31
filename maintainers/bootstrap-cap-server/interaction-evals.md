# Bootstrap CAP Server Interaction Evals

Maintainer-only RED/GREEN notes for the `bootstrap-cap-server` skill.

Do not reference this file from the public skill. It exists to document interaction failures and later regressions without teaching agents the exact examples.

## What These Evals Cover

- whether the agent asks the setup questions together instead of one at a time
- whether runtime source is inferred when the user already made it obvious
- whether user-facing replies avoid internal protocol labels
- whether the agent gives a short honesty/capability checkpoint before jumping into implementation

## RED: Baseline Without Skill

### Scenario A: User already gave placement, local-file source, and "no jargon"

User setup:

- project parent directory already specified
- project name already specified
- `git init` choice already specified
- source is clearly local node/edge files
- graph has only structure plus weights/lags
- no existing prediction or intervention runtime
- user explicitly asks to avoid jargon

Observed baseline behavior:

- agent jumped straight into implementation framing
- agent skipped the grouped intake entirely
- agent assumed future placeholder behavior without asking
- agent still leaked implementation terms in the first reply

### Scenario B: User already gave enough information for an honest capability checkpoint

User setup:

- project placement already specified
- no `git init`
- runtime can do graph queries and observational prediction
- runtime cannot do intervention
- user asks the agent to decide what should be mounted

Observed baseline behavior:

- agent jumped straight into implementation instead of pausing for a short public-contract checkpoint
- agent did not state non-claims clearly enough
- agent did not ask only for the remaining wiring detail

## GREEN: With Skill

### Scenario A: Grouped intake improved

Observed green behavior:

- agent stopped re-asking placement details the user had already provided
- agent inferred the local-file source instead of asking for a category label
- agent grouped the remaining open questions into one compact checklist

Residual risk:

- user-facing wording can still leak terms like `backend` or `adapter`

### Scenario B: Capability checkpoint improved

Observed green behavior:

- agent gave a short honesty checkpoint before implementation
- agent stated that intervention would not be mounted
- agent asked only for the remaining source/wiring inputs

Residual risk:

- the checkpoint can still drift back into protocol-heavy phrases like level labels or verb ids

## Current Rule Of Thumb

- keep evals generic
- avoid real user project names in eval text
- keep these notes in `maintainers/`, not under the public skill path
- if a new failure pattern appears, add the pattern here in abstract form instead of copying a user conversation literally
