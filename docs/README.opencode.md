# Abel Skills for OpenCode

Install the whole Abel collection through the OpenCode plugin config:

```json
{
  "plugin": ["abel@git+https://github.com/Abel-ai-causality/Abel-skills.git"]
}
```

If you already have an Abel API key, persist it into the installed plugin's
`skills/abel-auth/.env.skill` before normal live use. Otherwise restart
OpenCode and make `abel-auth` your first action.

After auth is ready, bootstrap the default strategy workspace:

```bash
abel-strategy-discovery workspace bootstrap --path ./abel-strategy-discovery-workspace
```

To pin a specific version, branch, or tag, append it after `#`:

```json
{
  "plugin": ["abel@git+https://github.com/Abel-ai-causality/Abel-skills.git#v1.2.0"]
}
```

Release tags are the recommended stable pin target.
