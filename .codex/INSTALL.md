# Installing Abel Skills for Codex

Install the full Abel skills collection, not a single sub-skill.

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

3. Prepare the shared runtime and default strategy workspace base from the repo instructions.

4. Restart Codex.

5. Start a new session and run `abel-auth` to connect Abel before the first live request.

## First Questions

- Help me search for a TSLA strategy.
- Find a few Abel-discovered candidates around semiconductor demand.
- Continue my TSLA strategy workspace.
