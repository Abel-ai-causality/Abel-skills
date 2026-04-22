---
name: abel
version: 1.2.0
description: >
  Use when the user asks for Abel and you need to choose between strategy
  discovery, causal reads, or auth recovery.
metadata:
  openclaw:
    requires:
      bins:
        - python
    homepage: https://github.com/Abel-ai-causality/Abel-skills
---

Use `Abel` as the main entrypoint.

Route in this order:

1. If live Abel auth is missing or invalid, use `abel-auth`.
2. If the user wants strategy search, candidate discovery, a research workspace,
   session continuation, branch preparation, branch debugging, or branch runs,
   use `abel-strategy-discovery`.
3. For other graph-native or decision-oriented Abel reads, use `abel-ask`.

Keep this skill thin. Choose the destination skill and hand off. Do not repeat
the downstream workflow here.
