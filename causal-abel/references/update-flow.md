# Update Flow

Use this file for the first-use soft update check workflow after `SKILL.md` has already told you that `causal-abel` applies.

## Goal

Detect whether the installed `causal-abel` skill has a newer GitHub version, summarize the important release notes from `CHANGELOG.md`, and ask the user before running a refresh command that targets only `causal-abel`.

This flow is intentionally soft:

- If the check works, surface useful update information.
- If the check fails, times out, or returns incomplete data, continue the normal skill flow.

## When To Run

- Run this check on the first use of `causal-abel` in a session.
- Do not repeat it again in the same session once you have recorded that the attempt already happened.
- Prefer running it before live Abel API calls so the user can decide whether to refresh the skill first.

## Primary Script

Use the bundled script:

```bash
python scripts/check_skill_update.py
```

The script returns JSON with these important fields:

- `ok`: whether the check completed cleanly
- `update_available`: whether the installed `causal-abel` folder hash differs from the current GitHub folder hash
- `skill_name`: the current skill name
- `current_version`: local `SKILL.md` version when available
- `remote_version`: remote `SKILL.md` version when available
- `summary`: concise changelog bullets for versions newer than the current one
- `next_command`: the exact single-skill refresh command to run if the user says yes
- `warning`: reminder that the refresh command targets only `causal-abel`
- `error`: soft-failure message when the check could not complete

## Decision Rules

1. Run `python scripts/check_skill_update.py`.
2. If `ok` is `false`, do not block the user. Continue the normal workflow.
3. If `update_available` is `false`, continue the normal workflow.
4. If `update_available` is `true`:
   - Tell the user there is a newer version.
   - Mention `current_version` and `remote_version` when available.
   - Summarize the key items from `summary`.
   - Tell the user the refresh command only targets `causal-abel`.
   - Keep the tone warm and lightly playful instead of mechanical.
   - End with a short `Y/N` so the user can answer in one character.
5. Only run `next_command` after the user agrees.
6. After updating, continue carefully. Do not assume the current turn has already reloaded the new skill instructions. Treat the next invocation as the safe point where the updated files are guaranteed to apply.

## Suggested User-Facing Wording

When an update exists:

```text
Tiny tune-up available for `causal-abel`: you have `{current_version}` and GitHub has `{remote_version}`.

What changed:
- {summary}

I can refresh just this skill with `{next_command}` and then keep going. Refresh `causal-abel` now? (Y/N)
```

When the check fails:

```text
I could not verify skill updates right now, so I will continue with the current installed version.
```

## Notes

- The script checks only the installed `causal-abel` skill by reading the public skills lock entry and comparing its recorded folder hash against GitHub.
- The script uses remote `SKILL.md` and `CHANGELOG.md` only to explain what changed.
- The script is allowed to fail quietly because update detection is a convenience layer, not a hard dependency for causal analysis.
