This `AGENTS.md` applies to everything under `Abel-skills/`.

`Abel-skills` is in a compatibility migration from flat top-level skill directories to `skills/`.

Rules:

- During the compatibility phase, source skill content exists in both the legacy top-level paths such as `causal-abel/` and `bootstrap-cap-server/`, and the new `skills/` paths.
- Until the later cleanup change deletes the legacy locations, keep the legacy and `skills/` copies aligned when editing source skill content.
- Existing build/publish scripts still target the legacy `causal-abel/` path during this phase unless the user explicitly asks to migrate them too.
- The ClawHub artifact version is automatically built from the source skill version in `causal-abel/SKILL.md`. Do not manually edit the version under `clawhub/`.
- Everything under `dist/` is build output. Do not manually update files in `dist/` unless the user explicitly asks for generated artifacts to be refreshed.
- `clawhub/causal-abel/` is also a generated import path. Prefer changing source files first, then regenerate when needed.
- If user-facing skill content changes, update the source skill and supporting sources first; only rebuild generated outputs after that.
- Refer to $skill-creator for writing proper skill prompt
