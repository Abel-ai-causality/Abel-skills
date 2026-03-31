This `AGENTS.md` applies to everything under `Abel-skills/`.

Rules:

- Source skills live under `skills/`.
- The ClawHub artifact version is automatically built from the source skill version in `skills/causal-abel/SKILL.md`. Do not manually edit the version under `clawhub/`.
- Everything under `dist/` is build output. Do not manually update files in `dist/` unless the user explicitly asks for generated artifacts to be refreshed.
- `clawhub/causal-abel/` is also a generated import path. Prefer changing source files first, then regenerate when needed.
- If user-facing skill content changes, update the source skill and supporting sources first; only rebuild generated outputs after that.
- Refer to $skill-creator for writing proper skill prompt
