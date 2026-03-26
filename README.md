# Abel Skills

This repository currently publishes the `causal-abel` skill.

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

The source skill lives in `causal-abel/`.

## For Maintainers

### Endpoint Defaults

Endpoint and OAuth defaults for `causal-abel` are maintained in `causal-abel/config/endpoints.json`.

- Update `endpoints.json` when the repository default CAP or OAuth host changes.
- `.env.skill` and legacy `.env.skills` are local runtime overrides for probing and auth; they do not automatically rewrite repository docs.
- Re-sync the generated skill docs after changing endpoint defaults:

```bash
python3 causal-abel/scripts/sync_endpoint_refs.py
```

### Build The ClawHub Artifact

This repository keeps the source skill in `causal-abel/SKILL.md`.

- Local throwaway build output: `dist/clawhub/causal-abel`
- Repository-committed ClawHub import path: `clawhub/causal-abel`
- `main` automatically refreshes `clawhub/causal-abel` through `.github/workflows/sync-clawhub-artifact.yml`

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
