# Abel Skills

Mono-repo for Abel AI agent skills. Currently ships `causal-abel`.

## Structure

```
causal-abel/          → public skill (installed by users)
  SKILL.md            → entry point (187 lines, progressive disclosure)
  scripts/            → cap_probe.py (CAP API probe), check_skill_update.py
  references/         → 12 modular docs loaded on-demand
  assets/             → report-guide.md
  agents/             → openai.yaml config
clawhub/causal-abel/  → auto-synced ClawHub artifact (do NOT edit directly)
maintainers/          → render pipeline, endpoint config, dev guide
scripts/              → build + publish tooling
```

## Dev Commands

```bash
make lint              # ruff check on all Python
make test              # pytest on cap_probe + render scripts
make render            # render public skill from endpoints.json
make verify            # ensure no private endpoints leaked into public skill
make build-clawhub     # build ClawHub artifact locally
```

## Rules

- `causal-abel/` is rendered output. Edit `maintainers/` inputs, then `make render`.
- `clawhub/` is CI-generated. Never edit directly.
- Private endpoints go in `maintainers/causal-abel/endpoints.local.json` (gitignored).
- Run `make verify` before every commit.
