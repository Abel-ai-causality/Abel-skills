# Developer Builds

This page is for maintainers who need to build local Abel skill artifacts from repository source.

## Build A Local Ask-Skill Version

Use this when you want a local rendered `abel-ask` tree for testing endpoint config, smoke probes, or prompt changes without touching the published release path.

Public-safe render:

```bash
python3 maintainers/abel-ask/render_skill.py --profile prod --output-dir skills/abel-ask
```

Local SIT-style render:

```bash
python3 maintainers/abel-ask/render_skill.py --include-local --profile sit --output-dir dist/local/abel-ask
```

Expected output:

- public source ask skill: `skills/abel-ask/`
- local rendered ask skill: `dist/local/abel-ask/`

## Verify The Local Ask-Skill Version

Run the maintainer smoke probe against the local rendered tree:

```bash
python3 maintainers/abel-ask/smoke_cap_probe.py
```

To point at a different skill root:

```bash
python3 maintainers/abel-ask/smoke_cap_probe.py --skill-root skills/abel-ask
```

## Build A ClawHub Release Version

Use this when you want the publishable ClawHub artifact for the main `abel` entry skill.

```bash
python3 scripts/build_clawhub_release.py
```

Expected output:

- publishable artifact: `dist/clawhub/abel/`

You can also choose a different output root:

```bash
python3 scripts/build_clawhub_release.py --output-root dist/test-clawhub
```

Expected output in that case:

- publishable artifact: `dist/test-clawhub/abel/`

## Dry-Run A ClawHub Publish

Before a real release, verify the publish command and computed version:

```bash
python3 scripts/publish_clawhub_release.py --dry-run
```

Or with a custom build root:

```bash
python3 scripts/publish_clawhub_release.py --output-root dist/test-clawhub --dry-run
```

The dry-run should print a `clawhub publish ...` command for:

- `--slug abel`
- `--name Abel`
- the current source version from `skills/abel/SKILL.md`

## Real ClawHub Publish

When the artifact and version look correct:

```bash
python3 scripts/publish_clawhub_release.py
```

This publishes from built output. Do not commit generated ClawHub artifacts back into the repository.
