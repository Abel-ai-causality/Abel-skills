This `AGENTS.md` applies to everything under `Abel-skills/`.

Rules:

- Source skills live under `skills/`.
- Default day-to-day development target is `develop`, not `main`.
- Normal feature branches should be cut from `develop` and merged back into `develop`.
- Treat `main` as the release branch. Only release or hotfix PRs should target `main`.
- Do not bump source skill versions or add top-level release changelog entries in normal feature PRs to `develop`.
- Only release PRs to `main` should update the source `version`, `CHANGELOG.md`, and the committed `clawhub/` artifact together.
- The ClawHub artifact version is automatically built from the source skill version in `skills/causal-abel/SKILL.md`. Do not manually edit the version under `clawhub/`.
- Everything under `dist/` is build output. Do not manually update files in `dist/` unless the user explicitly asks for generated artifacts to be refreshed.
- `clawhub/causal-abel/` is also a generated import path. Prefer changing source files first, then regenerate when needed.
- If user-facing skill content changes, update the source skill and supporting sources first; only rebuild generated outputs after that.
- For the full maintainer workflow, see `docs/branching-and-releases.md`.
- Refer to $skill-creator for writing proper skill prompt
