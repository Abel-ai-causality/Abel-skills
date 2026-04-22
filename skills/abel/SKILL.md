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

Before routing, run the bundled Abel auth preflight (`auth-status`) instead of
guessing from shell environment alone.

Route in this order:

1. Run the auth preflight from the bundled CAP probe.
2. If the preflight reports missing or invalid live auth, use `abel-auth`
   first, then continue routing the user's original request.
3. If the user wants strategy search, candidate discovery, a research workspace,
   session continuation, branch preparation, branch debugging, or branch runs,
   use `abel-strategy-discovery`.
4. For other graph-native or decision-oriented Abel reads, use `abel-ask`.

Keep this skill thin. Choose the destination skill and hand off. Do not repeat
the downstream workflow here.
