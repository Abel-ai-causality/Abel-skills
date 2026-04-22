---
name: abel-auth
description: >
  Connect or repair Abel account access. Reuse existing auth when possible,
  otherwise complete the Abel OAuth handoff and persist the resulting API key.
---

Use this skill when Abel auth is missing, expired, or needs to be initialized.

1. Check whether usable Abel auth already exists.
2. Reuse existing auth if present.
3. If not, start the OAuth handoff.
4. Persist the resulting key to `skills/abel-auth/.env.skill` for this installed collection.
5. Report whether Abel is ready for live use.

Read `references/preflight.md` before deciding whether auth is already usable.
Read `references/setup-guide.md` only when you need to run or repair the OAuth handoff.
