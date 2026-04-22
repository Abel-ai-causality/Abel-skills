# Abel Skills for Codex

Guide for using Abel Skills with OpenAI Codex via native skill discovery.

## Quick Install

Tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/Abel-ai-causality/Abel-skills/refs/heads/main/.codex/INSTALL.md
```

## Manual Installation

### Prerequisites

- OpenAI Codex
- Git

### Steps

1. Clone the repo:

   ```bash
   git clone https://github.com/Abel-ai-causality/Abel-skills.git ~/.codex/abel-skills
   ```

2. Create the skills symlink:

   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/abel-skills/skills ~/.agents/skills/abel
   ```

3. Before restart, either:
   - store an existing API key in `~/.codex/abel-skills/skills/abel-auth/.env.skill`, or
   - plan to run `abel-auth` as the first action after restart

   Example:

   ```dotenv
   ABEL_API_KEY=abel_xxx
   ```

4. Restart Codex.

5. Run `abel-auth` if auth is not already configured.

6. Bootstrap the default strategy workspace:

   ```bash
   abel-strategy-discovery workspace bootstrap --path ./abel-strategy-discovery-workspace
   ```

## How Auth Resolution Works

`abel-auth` is the canonical auth owner. Its local `.env.skill` file is the main
shared auth location for the collection:

```text
~/.codex/abel-skills/skills/abel-auth/.env.skill
```

`abel-ask` and `abel-strategy-discovery` also look for collection-level shared
auth in sibling skill directories, so one successful `abel-auth` setup is enough
for normal live use.

## Usage

After restart, start from `Abel`, complete `abel-auth` if needed, then bootstrap
the default strategy workspace before normal strategy use.

Try:

- Help me search for a TSLA strategy.
- Continue my TSLA strategy workspace.
- Give me an Abel read on what drives mortgage-rate-sensitive homebuilder stocks.
