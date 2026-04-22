# Abel Ask Maintainer Guide

This directory owns ask-specific rendering inputs for the public ask-skill line now published as `abel-ask`.

Treat `../skills/` as the maintainer-owned source tree for the whole skills collection.
Treat `../../skills/abel-ask` as the rendered public install tree.

## Files

- `endpoints.json`: public-safe endpoint source for the public ask skill and published artifacts
- `endpoints.local.json`: gitignored local override file for SIT or other private environments
- `endpoints.local.example.json`: example local override shape
- `endpoint_config.py`: endpoint loading and profile resolution for maintainer renders
- `../skills/`: complete maintainer-owned copy of the full skills collection before endpoint-specific rendering
- `render_skill.py`: copies the full maintainer-owned ask skill, then applies endpoint-specific replacements into the rendered output

## Rules

- Keep `../skills/` as the canonical maintainer-owned source tree for skills.
- Keep `endpoints.json` public-safe. Anything rendered from it can end up in `skills/abel-ask/` or a published artifact.
- Keep private or test endpoints only in `endpoints.local.json`.
- Do not rely on `.env.skill` or `.env.skills` for endpoint injection. Those files are only for API keys.
- Treat `skills/abel-ask/` as a rendered public install root, not as the maintainer source tree.
- Local auth files already present in `dist/local/abel-ask/` are preserved across re-renders. They are not copied from `skills/abel-ask/`, so prod and SIT keys can stay separate.

## Development Flow

1. Update maintainer-side endpoint config.

Public defaults:

```bash
$EDITOR maintainers/abel-ask/endpoints.json
```

Local private overrides:

```bash
cp maintainers/abel-ask/endpoints.local.example.json maintainers/abel-ask/endpoints.local.json
$EDITOR maintainers/abel-ask/endpoints.local.json
```

2. Re-render the public ask skill from the maintainer template.

```bash
python3 maintainers/abel-ask/render_skill.py --profile prod
```

3. Render a local SIT-flavored skill for testing.

```bash
python3 maintainers/abel-ask/render_skill.py --include-local --profile sit --output-dir dist/local/abel-ask
```

If `dist/local/abel-ask/.env.skill` or `dist/local/abel-ask/.env.skills` already exists, the render keeps those files in place after rebuilding the rest of the tree.

4. Verify the public skill did not pick up private endpoints.

```bash
rg -n "cap-sit|api-sit" skills/abel-ask dist/clawhub
```

5. If you need a fresh ClawHub artifact locally, build it from the public skill.

```bash
python3 scripts/build_clawhub_release.py
```

## Smoke Probe

Use the maintainer smoke runner to verify the rendered local skill against the
live CAP surface. It defaults to `dist/local/abel-ask` and checks:

- query-node ranking regressions for the maintainer macro/asset cases
- `observe-dual` coverage across a small asset basket
- `paths`, `intervene-do`, and `intervene-time-lag` on connected asset pairs

```bash
python3 maintainers/abel-ask/smoke_cap_probe.py
```

For JSON output or a different rendered skill root:

```bash
python3 maintainers/abel-ask/smoke_cap_probe.py --json
python3 maintainers/abel-ask/smoke_cap_probe.py --skill-root skills/abel-ask
```

## Build Outputs

- `skills/abel-ask/`: public source ask skill
- `maintainers/skills/`: maintainer-owned source tree for the full skills collection
- `dist/local/abel-ask/`: local-only rendered skill for private endpoint testing
- `dist/clawhub/abel/`: throwaway local ClawHub build output for the main entry skill

## Release Notes

- The publish flow reads from collection source, so render `skills/abel-ask/` from `template/` first if endpoint-facing text changed.
- Dry-run the publish command before a release:

```bash
python3 scripts/publish_clawhub_release.py --dry-run
```

- Publish:

```bash
python3 scripts/publish_clawhub_release.py
```
