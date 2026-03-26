This `AGENTS.md` applies to everything under `Abel-skills/`.

`Abel-skills` is the source repo for the `causal-abel` skill. Treat generated outputs and source-of-truth files differently.

Rules:

- Source of truth is under `causal-abel/` and the build/publish scripts under `scripts/` and `maintainers/`.
- The ClawHub artifact version is automatically built from the source skill version in `causal-abel/SKILL.md`. Do not manually edit the version under `clawhub/`.
- Everything under `dist/` is build output. Do not manually update files in `dist/` unless the user explicitly asks for generated artifacts to be refreshed.
- `clawhub/causal-abel/` is also a generated import path. Prefer changing source files first, then regenerate when needed.
- If user-facing skill content changes, update the source skill and supporting sources first; only rebuild generated outputs after that.
