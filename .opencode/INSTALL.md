# Installing Abel Skills for OpenCode

Add Abel to the `plugin` array in your `opencode.json`:

```json
{
  "plugin": ["abel@git+https://github.com/Abel-ai-causality/Abel-skills.git"]
}
```

Restart OpenCode, then run `abel-auth`.

To pin a specific release tag, branch, or ref, add it after `#`:

```json
{
  "plugin": ["abel@git+https://github.com/Abel-ai-causality/Abel-skills.git#v1.2.0"]
}
```
