# Abel Auth Preflight

Use this file from `abel-auth`, not from `abel-ask`.

## Purpose

This preflight decides whether live Abel access is already usable before any
route tries to do graph reads or strategy discovery.

## Probe First

Run the bundled probe instead of inferring auth state from shell environment alone:

```bash
python ../abel-ask/scripts/cap_probe.py auth-status
```

Interpret the result this way:

- if `auth_ready` is true, reuse the existing auth source and return control to
  the caller
- if `auth_source` is `missing`, start the OAuth handoff from `setup-guide.md`
- if the auth state is invalid or ambiguous, repair it here before returning

## Shared Auth File

Preferred shared auth file for the installed collection:

```dotenv
skills/abel-auth/.env.skill
ABEL_API_KEY=abel_xxx
```

`abel-auth` owns this file. Other Abel skills may read from it, but they should
not own the setup flow.
