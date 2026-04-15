#!/usr/bin/env python3
"""Maintainer smoke runner for the rendered causal-abel narrative CAP probe."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from endpoint_config import get_profiles


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SKILL_ROOT = REPO_ROOT / "dist" / "local" / "causal-abel"
DEFAULT_QUERY = "AI datacenter demand and NVDA"


def build_narrative_cap_probe_command(
    skill_root: Path,
    probe_args: Sequence[str],
) -> list[str]:
    return [
        "python3",
        str(skill_root / "scripts" / "narrative_cap_probe.py"),
        "--compact",
        *probe_args,
    ]


def _run_probe(skill_root: Path, probe_args: Sequence[str]) -> dict[str, Any]:
    command = build_narrative_cap_probe_command(skill_root, probe_args)
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    raw_output = (completed.stdout or completed.stderr).strip()
    try:
        payload = json.loads(raw_output) if raw_output else {}
    except json.JSONDecodeError:
        payload = {
            "ok": False,
            "status_code": -1,
            "message": "narrative_cap_probe.py returned non-JSON output",
            "raw_output": raw_output,
        }
    return {
        "command": command,
        "exit_code": completed.returncode,
        "payload": payload,
        "stderr": (completed.stderr or "").strip(),
    }


def _profile_base_url(profile_name: str, include_local: bool) -> str:
    profiles = get_profiles(include_local=include_local)
    profile = profiles[profile_name]
    narrative_base_url = str(profile.get("narrative_cap_base_url") or "").strip()
    if not narrative_base_url:
        raise SystemExit(
            f"Profile {profile_name!r} does not define narrative_cap_base_url. "
            "Set it in maintainers/causal-abel/endpoints.local.json."
        )
    return narrative_base_url


def _run_checks(skill_root: Path, base_url: str) -> list[dict[str, Any]]:
    cases = [
        ("card", ["--base-url", base_url, "card"]),
        ("methods", ["--base-url", base_url, "methods", "--verbs", "narrate"]),
        ("narrate", ["--base-url", base_url, "narrate", "--query", DEFAULT_QUERY]),
        ("search-prepare", ["--base-url", base_url, "search-prepare", "--query", DEFAULT_QUERY]),
    ]
    checks: list[dict[str, Any]] = []
    for name, probe_args in cases:
        execution = _run_probe(skill_root, probe_args)
        payload = execution["payload"]
        failures: list[str] = []
        if execution["exit_code"] != 0 or payload.get("ok") is not True:
            failures.append(payload.get("message") or "probe failed")
        checks.append(
            {
                "name": name,
                "command": execution["command"],
                "exit_code": execution["exit_code"],
                "ok": payload.get("ok"),
                "status_code": payload.get("status_code"),
                "failures": failures,
            }
        )
    return checks


def _summarize(checks: Sequence[dict[str, Any]]) -> dict[str, Any]:
    failures = [check for check in checks if check["failures"]]
    return {
        "ok": not failures,
        "checks": list(checks),
        "failure_count": len(failures),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run smoke checks against the rendered narrative CAP probe."
    )
    parser.add_argument(
        "--skill-root",
        default=str(DEFAULT_SKILL_ROOT),
        help="Rendered skill root to probe. Defaults to dist/local/causal-abel.",
    )
    parser.add_argument(
        "--profile",
        default="sit",
        help="Maintainer endpoint profile to read the narrative CAP base URL from.",
    )
    parser.add_argument(
        "--include-local",
        action="store_true",
        default=True,
        help="Read maintainer local endpoint overrides when resolving the profile.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON instead of a short text summary.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skill_root = Path(args.skill_root).expanduser().resolve()
    base_url = _profile_base_url(args.profile, args.include_local)
    checks = _run_checks(skill_root, base_url)
    summary = _summarize(checks)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for check in checks:
            status = "ok" if not check["failures"] else "fail"
            print(f"[{status}] {check['name']} :: exit={check['exit_code']} status_code={check['status_code']}")
            if check["failures"]:
                for failure in check["failures"]:
                    print(f"  - {failure}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
