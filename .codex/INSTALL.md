# Installing Abel Skills for Codex

Enable Abel Skills in Codex via native skill discovery.

## Prerequisites

- Git

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Abel-ai-causality/Abel-skills.git ~/.codex/abel-skills
```

2. Register the full skills directory:

```bash
mkdir -p ~/.agents/skills
ln -s ~/.codex/abel-skills/skills ~/.agents/skills/abel
```

3. Recommended before restart: persist Abel auth now if you already have a key.

Canonical shared auth file:

```text
~/.codex/abel-skills/skills/abel-auth/.env.skill
```

Example:

```dotenv
ABEL_API_KEY=abel_xxx
```

If you do not have a key yet, restart first, then make `abel-auth` your first action.

4. Restart Codex.

5. Start a new session.

6. If you skipped step 3, run `abel-auth` before the first live Abel request.

7. Bootstrap the default strategy workspace before normal strategy use:

```bash
abel-strategy-discovery workspace bootstrap --path ./abel-strategy-discovery-workspace
```

This creates or reuses the default workspace, prepares its runtime, and runs doctor.

## First Questions

- Help me search for a TSLA strategy.
- Find a few Abel-discovered candidates around semiconductor demand.
- Continue my TSLA strategy workspace.
