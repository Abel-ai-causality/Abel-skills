# Installing Abel Skills for Claude Code

Enable Abel Skills in Claude Code via personal skills symlinks.

## Prerequisites

- Git
- Claude Code with skills enabled

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Abel-ai-causality/Abel-skills.git ~/.claude/abel-skills
```

2. Register the Abel skill collection in Claude's personal skills directory:

```bash
mkdir -p ~/.claude/skills
ln -s ~/.claude/abel-skills/skills/abel ~/.claude/skills/abel
ln -s ~/.claude/abel-skills/skills/abel-ask ~/.claude/skills/abel-ask
ln -s ~/.claude/abel-skills/skills/abel-auth ~/.claude/skills/abel-auth
ln -s ~/.claude/abel-skills/skills/abel-strategy-discovery ~/.claude/skills/abel-strategy-discovery
```

3. Recommended before starting a new Claude Code session: persist Abel auth now if you already have a key.

Canonical shared auth file:

```text
~/.claude/skills/abel-auth/.env.skill
```

Example:

```dotenv
ABEL_API_KEY=abel_xxx
```

If you do not have a key yet, start a new session first, then make `abel-auth` your first action.

4. Start a new Claude Code session. If Claude Code was already open when you created `~/.claude/skills`, restart it once.

5. If you skipped step 3, run `abel-auth` before the first live Abel request.

6. Bootstrap the default strategy workspace before normal strategy use:

```bash
abel-strategy-discovery workspace bootstrap --path ./abel-strategy-discovery-workspace
```

## First Questions

- Help me search for a TSLA strategy.
- Find a few Abel-discovered candidates around semiconductor demand.
- Continue my TSLA strategy workspace.
