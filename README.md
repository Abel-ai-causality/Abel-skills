# Abel Skills

This repository is moving from flat top-level skill directories to a `skills/` layout.

During the compatibility phase:

- existing install and publish paths continue to work from the legacy locations
- new source copies are also present under `skills/`
- the legacy locations will be removed only after downstream docs and websites are updated

## For Users

Install `causal-abel` with `npx skills`:

```bash
npx --yes skills add Abel-ai-causality/Abel-skills --skill causal-abel -y
```

Install globally instead of project-local:

```bash
npx --yes skills add Abel-ai-causality/Abel-skills --skill causal-abel -g -y
```

List installed skills:

```bash
npx --yes skills ls --json
```

Current source locations:

- Legacy compatibility path: `causal-abel/`
- New layout path: `skills/causal-abel/`
- New layout path: `skills/bootstrap-cap-server/`

Until the cleanup migration lands, keep the legacy and `skills/` copies aligned.

## For Maintainers

Maintainer workflow for endpoint rendering, local SIT testing, and artifact builds:

- `maintainers/causal-abel/README.md`

### Endpoint Defaults

Endpoint and OAuth defaults for `causal-abel` are maintained in `maintainers/causal-abel/endpoints.json`.

- Keep `maintainers/causal-abel/endpoints.json` public-safe. Anything rendered from it can be copied into agent-facing skill files and release artifacts.
- Use `maintainers/causal-abel/endpoints.local.json` only for local render overrides. Do not rely on it for any value that must appear in committed docs or published skill builds.
- `.env.skill` and legacy `.env.skills` are local auth files for API keys. Endpoint defaults no longer come from env files.
- Re-render the public skill in place after changing endpoint defaults:

```bash
python3 maintainers/causal-abel/render_skill.py --profile prod --output-dir causal-abel
```

- Render a local SIT-flavored skill for testing without touching the public install path:

```bash
python3 maintainers/causal-abel/render_skill.py --include-local --profile sit --output-dir dist/local/causal-abel
```

### Build The ClawHub Artifact

This repository still builds and publishes from the legacy `causal-abel/SKILL.md` path during the compatibility phase.

- Local throwaway build output: `dist/clawhub/causal-abel`
- Repository-committed ClawHub import path: `clawhub/causal-abel`
- `main` automatically refreshes `clawhub/causal-abel` through `.github/workflows/sync-clawhub-artifact.yml`
- The build copies the public `causal-abel/` skill into an agent-facing artifact. Published or committed artifacts must therefore be built only after `causal-abel/` has been rendered with public-safe endpoints.

```bash
python3 scripts/build_clawhub_release.py
```

Build the committed import path locally:

```bash
python3 scripts/build_clawhub_release.py --output-root clawhub
```

Import into ClawHub from the repository tree path:

```text
Abel-ai-causality/Abel-skills/tree/main/clawhub/causal-abel
```

### Verify The Publish Command

```bash
python3 scripts/publish_clawhub_release.py --dry-run
```

### Publish To ClawHub

```bash
python3 scripts/publish_clawhub_release.py
```

The publish script guarantees that the ClawHub release version matches the source `version` in `causal-abel/SKILL.md`.
