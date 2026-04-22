# Abel Skills

Abel Skills is the collection repository for Abel agent skills. Users should install the collection and start from `Abel`, which routes to the right internal skill for causal reads, strategy discovery, or auth recovery.

## Main Skills

- `abel`: main entrypoint
- `abel-ask`: graph-native and proxy-routed causal reads
- `abel-auth`: connect or repair Abel auth
- `abel-strategy-discovery`: workspace-first strategy discovery
- `bootstrap-cap-server`: CAP server bootstrap helper

## Installation

GitHub direct install and ClawHub install are separate paths.

- Codex: follow [.codex/INSTALL.md](.codex/INSTALL.md)
- OpenCode: follow [docs/README.opencode.md](docs/README.opencode.md)
- ClawHub / OpenClaw: install from the published ClawHub package after release publication

After installation, run `abel-auth` before the first live Abel request.

## Try These Questions

- Help me search for a TSLA strategy.
- Find a few Abel-discovered candidates around semiconductor demand.
- Continue my TSLA strategy workspace.
- Give me an Abel read on what drives mortgage-rate-sensitive homebuilder stocks.

## For Maintainers

- Release documentation: [docs/releases.md](docs/releases.md)
- Branching and repository policy: `AGENTS.md`
- Maintainer endpoint rendering workflow: `maintainers/abel-ask/README.md`

Release builds publish from collection source into `dist/`. Do not commit generated ClawHub artifacts into the repository.
