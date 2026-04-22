# Installing Abel Skills for OpenCode

Add Abel to the `plugin` array in your `opencode.json`:

```json
{
  "plugin": ["abel@git+https://github.com/Abel-ai-causality/Abel-skills.git"]
}
```

If you already have an Abel API key, store it before restart in the installed
plugin checkout's canonical shared auth file:

```text
skills/abel-auth/.env.skill
```

If you do not have a key yet, restart OpenCode first, then make `abel-auth`
your first action.

To pin a specific release tag, branch, or ref, add it after `#`:

```json
{
  "plugin": ["abel@git+https://github.com/Abel-ai-causality/Abel-skills.git#v1.2.0"]
}
```

Restart OpenCode after editing `opencode.json`.

After restart:

1. Run `abel-auth` if auth is not already configured.
2. Bootstrap the default strategy workspace:

```bash
abel-strategy-discovery workspace bootstrap --path ./abel-strategy-discovery-workspace
```
