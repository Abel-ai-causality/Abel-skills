#!/usr/bin/env python
"""Sync host references in causal-abel docs from one config file."""

from __future__ import annotations

import re
from pathlib import Path

from endpoint_config import get_template_values

SKILL_ROOT = Path(__file__).resolve().parents[1]
VALUES = get_template_values()


def _replace(text: str, pattern: str, replacement: str, *, count: int = 0) -> str:
    updated, matched = re.subn(pattern, replacement, text, count=count, flags=re.MULTILINE)
    if matched == 0:
        raise RuntimeError(f"Pattern not found: {pattern}")
    return updated


def sync_skill_md() -> None:
    path = SKILL_ROOT / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    text = _replace(
        text,
        r"^- Default CAP target: `[^`]+`\.$",
        f"- Default CAP target: `{VALUES['ACTIVE_CAP_BASE_URL']}`.",
    )
    text = _replace(
        text,
        r"^- Treat `[^`]+` as the OAuth and business API host, not the CAP probe host\.$",
        f"- Treat `{VALUES['ACTIVE_OAUTH_BASE_URL']}` as the OAuth and business API host, not the CAP probe host.",
    )
    path.write_text(text, encoding="utf-8")


def sync_setup_guide() -> None:
    path = SKILL_ROOT / "references" / "setup-guide.md"
    text = path.read_text(encoding="utf-8")
    text = _replace(
        text,
        r"^Base URL: `[^`]+`$",
        f"Base URL: `{VALUES['ACTIVE_OAUTH_BASE_URL']}`",
    )
    text = re.sub(
        r"https://[A-Za-z0-9.-]+/echo/web/credentials/oauth/google/authorize/agent",
        VALUES["ACTIVE_AUTHORIZE_AGENT_URL"],
        text,
    )
    text = re.sub(
        r"https://[A-Za-z0-9.-]+/echo/web/credentials/oauth/google/result\?pollToken=POLL_TOKEN",
        VALUES["ACTIVE_RESULT_URL_TEMPLATE"],
        text,
    )
    text = re.sub(
        r"https://[A-Za-z0-9.-]+/echo/web/credentials/oauth/google/callback\?code=GOOGLE_CODE&format=json",
        VALUES["ACTIVE_CALLBACK_EXAMPLE_URL"],
        text,
    )
    text = re.sub(
        r"https://[A-Za-z0-9.-]+/echo/web/credentials/oauth/google/callback",
        VALUES["ACTIVE_CALLBACK_URL"],
        text,
    )
    text = _replace(
        text,
        r"^CAP_BASE_URL=.*$",
        f"CAP_BASE_URL={VALUES['ACTIVE_CAP_BASE_URL']}",
    )
    path.write_text(text, encoding="utf-8")


def sync_probe_usage() -> None:
    path = SKILL_ROOT / "references" / "probe-usage.md"
    text = path.read_text(encoding="utf-8")
    text = _replace(
        text,
        r'^BASE_URL="[^"]+"$',
        f'BASE_URL="{VALUES["ACTIVE_CAP_BASE_URL"]}"',
    )
    text = _replace(
        text,
        r"## Endpoint Notes\n\n(?:.*\n)*?(?=\n## |\Z)",
        (
            "## Endpoint Notes\n\n"
            f"- The current default CAP surface answers on `{VALUES['ACTIVE_CAP_ENDPOINT_URL']}`.\n"
            f"- Production CAP surface answers on `{VALUES['PROD_CAP_ENDPOINT_URL']}`.\n"
            f"- SIT CAP surface answers on `{VALUES['SIT_CAP_ENDPOINT_URL']}`.\n"
            f"- The probe accepts base URLs such as `{VALUES['ACTIVE_CAP_BASE_URL']}` "
            "and resolves them to `/cap`.\n"
            f"- `{VALUES['ACTIVE_OAUTH_BASE_URL']}` is used for OAuth and business API flows "
            "in `setup-guide.md`; it is not the default CAP probe base.\n"
        ),
    )
    path.write_text(text, encoding="utf-8")


def sync_env_file() -> None:
    primary = SKILL_ROOT / ".env.skill"
    fallback = SKILL_ROOT / ".env.skills"
    path = primary if primary.exists() or not fallback.exists() else fallback
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    replacement = f"CAP_BASE_URL='{VALUES['ACTIVE_CAP_BASE_URL']}'"
    if re.search(r"^CAP_BASE_URL=.*$", text, flags=re.MULTILINE):
        text = re.sub(r"^CAP_BASE_URL=.*$", replacement, text, flags=re.MULTILINE)
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += replacement + "\n"
    path.write_text(text, encoding="utf-8")


def main() -> None:
    sync_skill_md()
    sync_setup_guide()
    sync_probe_usage()
    sync_env_file()


if __name__ == "__main__":
    main()
