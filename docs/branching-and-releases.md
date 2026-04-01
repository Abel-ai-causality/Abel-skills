# Branching And Releases

This repository uses a lightweight `develop`-first workflow.

## Branch Roles

- `main`
  - release branch
  - source of truth for user installs and publish
  - only release and hotfix PRs should target this branch
- `develop`
  - integration branch for day-to-day work
  - normal feature PRs should target this branch
- `feature/*`
  - short-lived branch cut from `develop`
  - merged back into `develop`
- `hotfix/*`
  - short-lived branch cut from `main`
  - merged into `main`, then back-merged into `develop`
- `release/*`
  - optional staging branch cut from `develop`
  - useful when maintainers want a dedicated release-prep PR before `main`

## Feature Flow

Use this flow for normal skill and maintainer work.

1. Update local branches:
   - `git checkout develop`
   - `git pull`
2. Create a feature branch:
   - `git checkout -b feature/<topic>`
3. Make source changes under `skills/`, maintainer helpers, tests, and docs as needed.
4. Open a PR to `develop`.

Default feature PR rule:

- do not bump `skills/causal-abel/SKILL.md` version
- do not add a new release section to `CHANGELOG.md`
- do not commit regenerated `clawhub/causal-abel/` output

## Release Flow

Use this flow when a batch of already-reviewed changes in `develop` is ready to ship.

Two acceptable shapes:

- direct `develop -> main` release PR
- `release/* -> main` release PR when a dedicated staging branch is useful

Release PR checklist:

- bump source version in `skills/causal-abel/SKILL.md`
- add the matching release entry in `CHANGELOG.md`
- regenerate committed `clawhub/causal-abel/`
- verify the artifact still builds from source
- run `python3 scripts/publish_clawhub_release.py --dry-run`

## Hotfix Flow

Use this only for urgent fixes that must ship before the next normal release.

1. Cut the branch from `main`:
   - `git checkout main`
   - `git pull`
   - `git checkout -b hotfix/<topic>`
2. Fix the issue and open a PR to `main`.
3. After the hotfix lands on `main`, back-merge the same change into `develop`.

If the hotfix is externally visible, include normal release bookkeeping on the `main` side.

## Why This Workflow Exists

The goal is to keep `main` clean as the release branch while allowing multiple feature changes to accumulate in `develop` without bumping the public version on every PR.

That means:

- integration happens in `develop`
- publishing happens from `main`
- version, changelog, and committed artifact updates happen once per release, not once per feature
