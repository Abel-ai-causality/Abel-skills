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

### Build The ClawHub Artifact

This repository keeps the source skill in `causal-abel/SKILL.md` and generates a ClawHub-safe artifact into `dist/clawhub/causal-abel`.

```bash
python3 scripts/build_clawhub_release.py
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
