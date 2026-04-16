# Causal Abel Maintainer Guide

This directory owns maintainer-only rendering inputs for the public `causal-abel` skill.

Treat `../../skills/causal-abel` as the checked-in public product, not as the place to keep local-only endpoint state.

## Files

- `endpoints.json`: public-safe endpoint source for the checked-in skill and published artifacts
- `endpoints.local.json`: gitignored local override file for SIT or other private environments
- `endpoints.local.example.json`: example local override shape
- `endpoint_config.py`: endpoint loading and profile resolution for maintainer renders
- `render_skill.py`: renders a public or local skill artifact from the current endpoint profile to `dist/`
- `smoke_narrative_cap_probe.py`: smoke runner for the narrative CAP helper in rendered local builds

## Rules

- Keep `endpoints.json` public-safe. Anything rendered from it can end up in `skills/causal-abel/`, `clawhub/causal-abel/`, or a published artifact.
- Keep private or test endpoints only in `endpoints.local.json`.
- Keep non-production narrative CAP endpoints only in `endpoints.local.json`. The production narrative base in `endpoints.json` is public-safe.
- Do not rely on `.env.skill` or `.env.skills` for endpoint injection. Those files are only for API keys.
- Treat `skills/causal-abel/` as a rendered public install root.
- Local auth files already present in `dist/local/causal-abel/` are preserved across re-renders. They are not copied from `skills/causal-abel/`, so prod and SIT keys can stay separate.

## Development Flow

1. Update maintainer-side endpoint config.

Public defaults:

```bash
$EDITOR maintainers/causal-abel/endpoints.json
```

Local private overrides:

```bash
cp maintainers/causal-abel/endpoints.local.example.json maintainers/causal-abel/endpoints.local.json
$EDITOR maintainers/causal-abel/endpoints.local.json
```

The public prod profile now points narrative CAP at `https://cap.abel.ai/narrative/cap`
through `narrative_cap_base_url = https://cap.abel.ai/narrative`.
The local `sit` example mirrors graph CAP and points narrative CAP at
`https://cap-sit.abel.ai/narrative/cap` through
`narrative_cap_base_url = https://cap-sit.abel.ai/narrative`.
If you are testing a different non-production narrative CAP helper locally, override
`narrative_cap_base_url` in the selected local profile. The rendered
`dist/local/causal-abel/scripts/narrative_cap_probe.py` and
`references/narrative-probe-usage.md` will inherit that base URL as their default target.

2. Re-render the checked-in public skill.

```bash
python3 maintainers/causal-abel/render_skill.py --profile prod --output-dir skills/causal-abel
```

3. Render a local SIT-flavored skill for testing.

```bash
python3 maintainers/causal-abel/render_skill.py --include-local --profile sit --output-dir dist/local/causal-abel
```

If `dist/local/causal-abel/.env.skill` or `dist/local/causal-abel/.env.skills` already exists, the render keeps those files in place after rebuilding the rest of the tree.

4. Verify the public skill did not pick up private endpoints.

```bash
rg -n "cap-sit|api-sit" skills/causal-abel clawhub/causal-abel
```

5. If you need a fresh ClawHub artifact locally, build it from the public skill.

```bash
python3 scripts/build_clawhub_release.py
```

Build the committed import path instead of `dist/clawhub`:

```bash
python3 scripts/build_clawhub_release.py --output-root clawhub
```

## Smoke Probe

Use the maintainer smoke runner to verify the rendered local skill against the
live CAP surface. It defaults to `dist/local/causal-abel` and checks:

- query-node ranking regressions for the maintainer macro/asset cases
- `observe-dual` coverage across a small asset basket
- `paths`, `intervene-do`, and `intervene-time-lag` on connected asset pairs

```bash
python3 maintainers/causal-abel/smoke_cap_probe.py
```

For JSON output or a different rendered skill root:

```bash
python3 maintainers/causal-abel/smoke_cap_probe.py --json
python3 maintainers/causal-abel/smoke_cap_probe.py --skill-root skills/causal-abel
```

Use the narrative smoke runner to verify the rendered local skill against the
narrative CAP surface configured in `endpoints.local.json`. It checks:

- capability card reachability
- `meta.methods` access
- `narrate`
- `search-prepare`

```bash
python3 maintainers/causal-abel/smoke_narrative_cap_probe.py
```

For JSON output or a different rendered skill root:

```bash
python3 maintainers/causal-abel/smoke_narrative_cap_probe.py --json
python3 maintainers/causal-abel/smoke_narrative_cap_probe.py --skill-root skills/causal-abel
```

## Build Outputs

- `skills/causal-abel/`: checked-in public install root used by the normal skill installer
- `dist/local/causal-abel/`: local-only rendered skill for private endpoint testing
- `dist/clawhub/causal-abel/`: throwaway local ClawHub build output
- `clawhub/causal-abel/`: checked-in ClawHub import path

## Release Notes

- `main` automatically refreshes `clawhub/causal-abel/` through `.github/workflows/sync-clawhub-artifact.yml`.
- The publish flow reads from the public skill, so render `skills/causal-abel/` first if endpoint-facing text changed.
- Dry-run the publish command before a release:

```bash
python3 scripts/publish_clawhub_release.py --dry-run
```

- Publish:

```bash
python3 scripts/publish_clawhub_release.py
```
