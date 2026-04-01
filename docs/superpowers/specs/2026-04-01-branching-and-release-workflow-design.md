# Abel-skills Branching And Release Workflow Design

## Goal

Move `Abel-skills` from a `main`-first day-to-day workflow to a `develop`-first integration workflow, while keeping `main` as the only release branch for user installs and ClawHub publishing.

The operational target is:

- day-to-day feature work lands in `develop`
- `main` only receives release or hotfix changes
- source `version`, `CHANGELOG.md`, and committed `clawhub/` artifact updates happen only during release flow

## Current State

Today the repository behaves like a `main`-first release repo:

- users install from `main`
- `.github/workflows/sync-clawhub-artifact.yml` runs on `main`
- the source version in `skills/causal-abel/SKILL.md` drives the committed ClawHub artifact and publish script
- feature PRs can easily drift into "functional change + release bookkeeping" in a single step

That model works for small isolated edits, but it makes versioning noisy when maintainers want to batch multiple skill changes into one release.

## Desired State

The repository should follow a lightweight `GitFlow-lite` model:

- `main`
  - release-only branch
  - user installation and publish source of truth
  - target for release PRs and hotfix PRs only
- `develop`
  - integration branch for normal skill work
  - target for feature PRs
- `feature/*`
  - short-lived topic branches cut from `develop`
  - merged back into `develop`
- `hotfix/*`
  - cut from `main` for urgent production-facing fixes
  - merged into `main`, then back-merged into `develop`
- `release/*`
  - optional short-lived staging branch cut from `develop`
  - used only when maintainers want a dedicated release-prep PR before `main`

This is intentionally lighter than full GitFlow. The point is not process theater. The point is to separate integration from release.

## Rules

### Feature PRs To `develop`

Feature PRs should contain source behavior changes, tests, and supporting docs, but should not perform release bookkeeping.

Default rule for PRs with base `develop`:

- do not bump `skills/causal-abel/SKILL.md` version
- do not add a new top-level release section to `CHANGELOG.md`
- do not commit regenerated `clawhub/causal-abel/` artifact content

Allowed exception:

- if a change is purely documentation about the workflow itself, it may modify maintainer docs without implying a release

### Release PRs To `main`

Release PRs aggregate already-reviewed work from `develop` and perform the release bookkeeping in one place.

Required contents for a release PR to `main`:

- version bump in `skills/causal-abel/SKILL.md`
- matching release entry in `CHANGELOG.md`
- regenerated committed artifact in `clawhub/causal-abel/`
- any release-facing maintainer notes needed for publish

The release PR is the only place where version and changelog changes are expected by default.

### Hotfix PRs

Hotfixes are for urgent corrections that must land on `main` before the next planned release.

Hotfix rule:

- cut `hotfix/*` from `main`
- merge hotfix into `main`
- back-merge the same change into `develop`

If the hotfix is externally visible, it should carry normal release bookkeeping on the `main` side.

## Documentation Changes

The workflow needs to be visible in three places, each with a different role.

### 1. `AGENTS.md`

`AGENTS.md` should carry the hard operating rules for agents:

- default development target is `develop`
- do not bump version or changelog in normal feature work
- only release PRs to `main` should include version/changelog/artifact sync
- `clawhub/` remains generated output

This file is the shortest and most normative version.

### 2. `README.md`

`README.md` should gain a `Branching And Releases` maintainer section that explains:

- what `main` and `develop` mean
- where feature PRs go
- when release bookkeeping happens
- where to find the detailed workflow document

This is the maintainer entrypoint.

### 3. `docs/branching-and-releases.md`

Add a dedicated maintainer workflow document that contains:

- branch roles
- feature flow
- release flow
- hotfix flow
- checklist for a release PR
- checklist for back-merging hotfixes into `develop`

This file should be procedural and explicit.

## CI / Automation Changes

Keep automation minimal at first.

### Keep

Keep `.github/workflows/sync-clawhub-artifact.yml` scoped to `main`. That still matches the desired model because `main` remains the release branch.

### Add

Add one lightweight guard workflow for pull requests with logic roughly equivalent to:

- if PR base is `develop`
  - fail if `skills/causal-abel/SKILL.md` version changed
  - fail if a new release section was added to `CHANGELOG.md`
  - fail if committed `clawhub/causal-abel/` artifact changed
- if PR base is `main`
  - if source skill content changed in a release-relevant way, require both version and changelog updates

This should stay simple. It is a policy guard, not a release orchestration engine.

## Migration Plan

Do not rewrite history. Migrate forward from the current `main`.

### Step 1

Treat current `main` as the new release baseline.

### Step 2

Create `develop` from current `main`, so both branches are identical at migration start.

### Step 3

Update maintainer docs and agent instructions to make `develop` the default feature target.

### Step 4

Add the lightweight PR guard workflow.

### Step 5

From that point onward:

- feature work goes to `develop`
- release prep goes from `develop` to `main`
- hotfixes go from `main` back into `develop`

## Release Checklist Shape

Every release PR to `main` should verify:

- source version bumped once
- changelog entry matches that version
- committed `clawhub/causal-abel/` refreshed from source
- `scripts/build_clawhub_release.py` still produces an artifact whose version matches source
- `scripts/publish_clawhub_release.py --dry-run` remains valid

## Non-Goals

This design does not attempt to:

- automate semantic version selection
- add a full GitFlow release manager process
- change user install URLs away from `main`
- publish from `develop`
- force every release to use a dedicated `release/*` branch

## Recommendation

Adopt the lightweight model first:

- document the new flow
- create `develop`
- add one small policy-check workflow

Do not add heavier release orchestration until the team actually feels pain from the lightweight version.
