# Abel Skills for Claude Code

Guide for using Abel Skills with Claude Code via personal skills.

## Quick Install

Tell Claude Code:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/Abel-ai-causality/Abel-skills/refs/heads/main/.claude/INSTALL.md
```

## Manual Installation

### Prerequisites

- Claude Code
- Git

### Steps

1. Clone the repo:

   ```bash
   git clone https://github.com/Abel-ai-causality/Abel-skills.git ~/.claude/abel-skills
   ```

2. Create Claude personal skill symlinks:

   ```bash
   mkdir -p ~/.claude/skills
   ln -s ~/.claude/abel-skills/skills/abel ~/.claude/skills/abel
   ln -s ~/.claude/abel-skills/skills/abel-ask ~/.claude/skills/abel-ask
   ln -s ~/.claude/abel-skills/skills/abel-auth ~/.claude/skills/abel-auth
   ln -s ~/.claude/abel-skills/skills/abel-strategy-discovery ~/.claude/skills/abel-strategy-discovery
   ```

3. Before starting a new session, either:
   - store an existing API key in `~/.claude/skills/abel-auth/.env.skill`, or
   - plan to run `abel-auth` as the first action in the next Claude Code session

   Example:

   ```dotenv
   ABEL_API_KEY=abel_xxx
   ```

4. Start a new Claude Code session. If you created `~/.claude/skills` while Claude Code was already open, restart once so the new personal skills root is discovered cleanly.

5. Run `abel-auth` if auth is not already configured.

6. Bootstrap the default strategy workspace:

   ```bash
   abel-strategy-discovery workspace bootstrap --path ./abel-strategy-discovery-workspace
   ```

## How Auth Resolution Works

`abel-auth` is the canonical auth owner. Its local `.env.skill` file is the main
shared auth location for the collection:

```text
~/.claude/skills/abel-auth/.env.skill
```

`abel-ask` and `abel-strategy-discovery` also look for collection-level shared
auth in sibling skill directories, so one successful `abel-auth` setup is enough
for normal live use.

## Why This Uses Per-Skill Symlinks

Claude Code personal skills live under `~/.claude/skills/<skill-name>/`.
Using one symlink per skill matches that layout directly and keeps discovery
predictable.

## Usage

After installation, start from `Abel`, complete `abel-auth` if needed, then
bootstrap the default strategy workspace before normal strategy use.

Try:

- Help me search for a TSLA strategy.
- Continue my TSLA strategy workspace.
- Give me an Abel read on what drives mortgage-rate-sensitive homebuilder stocks.
