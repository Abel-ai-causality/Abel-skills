# Abel Skills for OpenCode

Install the whole Abel collection through the OpenCode plugin config:

```json
{
  "plugin": ["abel@git+https://github.com/Abel-ai-causality/Abel-skills.git"]
}
```

Restart OpenCode and run `abel-auth` before the first live Abel request.

To pin a specific version, branch, or tag, append it after `#`:

```json
{
  "plugin": ["abel@git+https://github.com/Abel-ai-causality/Abel-skills.git#v1.2.0"]
}
```

Release tags are the recommended stable pin target.
