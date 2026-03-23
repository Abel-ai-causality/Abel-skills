#!/usr/bin/env python3
"""Soft, single-skill update checker for the causal-abel skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

VERSION_HEADING_PATTERN = re.compile(
    r"^##\s+\[(?P<version>[^\]]+)\](?:\s+-\s+(?P<date>.+))?$"
)
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_SUMMARY_ITEMS = 6
LOCK_FILE_NAME = ".skill-lock.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check only the installed `causal-abel` skill for updates, "
            "then fetch remote SKILL.md and CHANGELOG.md to summarize "
            "what changed."
        )
    )
    parser.add_argument(
        "--skill-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Path to the skill root directory containing SKILL.md.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Timeout in seconds for subprocess and HTTP calls.",
    )
    parser.add_argument(
        "--max-summary-items",
        type=int,
        default=DEFAULT_MAX_SUMMARY_ITEMS,
        help="Maximum number of changelog bullets to include in the summary.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of pretty-printed JSON.",
    )
    parser.add_argument(
        "--lock-file",
        default="",
        help="Optional path to a specific .skill-lock.json file.",
    )
    return parser.parse_args()


def _parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    frontmatter_lines: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        frontmatter_lines.append(line)

    data: dict[str, str] = {}
    for raw_line in frontmatter_lines:
        if not raw_line or raw_line[0].isspace() or ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _load_skill_metadata(skill_root: Path) -> dict[str, str]:
    skill_md = skill_root / "SKILL.md"
    return _parse_frontmatter(skill_md.read_text(encoding="utf-8"))


def _build_raw_url(repo: str, branch: str, path: str) -> str:
    normalized_path = path.strip("/")
    return (
        f"https://raw.githubusercontent.com/{repo}/{branch}/{normalized_path}"
    )


def _fetch_text(url: str, timeout: float) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "causal-abel-update-checker"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def _fetch_json(url: str, timeout: float, token: str | None = None) -> dict[str, Any]:
    headers = {"User-Agent": "causal-abel-update-checker"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _candidate_lock_paths(skill_root: Path, lock_file: str) -> list[Path]:
    candidates: list[Path] = []
    if lock_file:
        candidates.append(Path(lock_file).expanduser())

    cwd = Path.cwd()
    home = Path.home()
    candidates.extend(
        [
            skill_root / ".agents" / LOCK_FILE_NAME,
            skill_root.parent / ".agents" / LOCK_FILE_NAME,
            cwd / ".agents" / LOCK_FILE_NAME,
            home / ".agents" / LOCK_FILE_NAME,
        ]
    )

    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path.resolve()) if path.exists() else str(path.expanduser())
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _load_lock_entry(
    skill_name: str, skill_root: Path, lock_file: str
) -> tuple[Path | None, dict[str, Any] | None]:
    for candidate in _candidate_lock_paths(skill_root, lock_file):
        if not candidate.exists():
            continue
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        skills = payload.get("skills")
        if not isinstance(skills, dict):
            continue
        entry = skills.get(skill_name)
        if isinstance(entry, dict):
            return candidate, entry
    return None, None


def _get_github_token() -> str | None:
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.getenv(name)
        if value:
            return value
    try:
        completed = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5.0,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    token = (completed.stdout or "").strip()
    return token or None


def _normalize_skill_folder(skill_path: str) -> str:
    normalized = skill_path.replace("\\", "/")
    if normalized.endswith("/SKILL.md"):
        normalized = normalized[: -len("/SKILL.md")]
    elif normalized.endswith("SKILL.md"):
        normalized = normalized[: -len("SKILL.md")]
    return normalized.rstrip("/")


def _fetch_skill_folder_hash(
    repo: str, skill_path: str, timeout: float, token: str | None
) -> str | None:
    folder_path = _normalize_skill_folder(skill_path)
    branches = ["main", "master"]
    for branch in branches:
        api_url = (
            f"https://api.github.com/repos/{repo}/git/trees/"
            f"{urllib.parse.quote(branch)}?recursive=1"
        )
        try:
            payload = _fetch_json(api_url, timeout, token)
        except urllib.error.HTTPError:
            continue
        tree = payload.get("tree")
        if not isinstance(tree, list):
            continue
        for entry in tree:
            if not isinstance(entry, dict):
                continue
            if entry.get("type") == "tree" and entry.get("path") == folder_path:
                sha = entry.get("sha")
                if isinstance(sha, str):
                    return sha
    return None


def _run_skills_list(global_scope: bool, timeout: float) -> list[dict[str, Any]]:
    command = ["npx", "--yes", "skills", "ls"]
    if global_scope:
        command.append("-g")
    command.append("--json")
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        return []
    try:
        payload = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def _detect_install_scope(skill_name: str, timeout: float) -> str | None:
    global_skills = _run_skills_list(True, timeout)
    if any(item.get("name") == skill_name for item in global_skills if isinstance(item, dict)):
        return "global"
    project_skills = _run_skills_list(False, timeout)
    if any(item.get("name") == skill_name for item in project_skills if isinstance(item, dict)):
        return "project"
    return None


def _source_url_from_repo(repo: str) -> str:
    return f"https://github.com/{repo}"


def _build_update_command(source_url: str, skill_name: str, scope: str | None) -> str:
    parts = ["npx", "--yes", "skills", "add", source_url, "--skill", skill_name]
    if scope == "global":
        parts.append("-g")
    parts.append("-y")
    return " ".join(parts)


def _parse_changelog_sections(text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for line in text.splitlines():
        match = VERSION_HEADING_PATTERN.match(line.strip())
        if match:
            if current is not None:
                sections.append(current)
            current = {
                "version": match.group("version").strip(),
                "date": (match.group("date") or "").strip(),
                "lines": [],
            }
            continue
        if current is not None:
            current["lines"].append(line.rstrip())

    if current is not None:
        sections.append(current)
    return sections


def _summarize_sections(
    sections: list[dict[str, Any]], local_version: str | None, max_items: int
) -> list[str]:
    if not sections or max_items <= 0:
        return []

    selected_sections: list[dict[str, Any]] = []
    if local_version:
        for section in sections:
            if section["version"] == local_version:
                break
            selected_sections.append(section)
    else:
        selected_sections = sections[:1]

    if not selected_sections:
        selected_sections = sections[:1]

    summary: list[str] = []
    for section in selected_sections:
        version = section["version"]
        for line in section["lines"]:
            bullet = line.strip()
            if not bullet.startswith("- "):
                continue
            summary.append(f"{version}: {bullet[2:]}")
            if len(summary) >= max_items:
                return summary
    return summary


def main() -> int:
    args = _parse_args()
    skill_root = Path(args.skill_root).expanduser().resolve()

    result: dict[str, Any] = {
        "ok": False,
        "checked": False,
        "skill_name": None,
        "current_version": None,
        "remote_version": None,
        "update_available": False,
        "summary": [],
        "scope": None,
        "warning": "This refresh command targets only `causal-abel`.",
        "next_command": None,
        "error": None,
    }

    try:
        metadata = _load_skill_metadata(skill_root)
        skill_name = metadata.get("name") or skill_root.name
        current_version = metadata.get("version") or None
        repo = metadata.get("update_repo")
        branch = metadata.get("update_branch", "main")
        skill_path = metadata.get("update_skill_path")
        changelog_path = metadata.get("update_changelog_path", "CHANGELOG.md")
        token = _get_github_token()

        result["skill_name"] = skill_name
        result["current_version"] = current_version

        if not repo or not skill_path:
            result["error"] = (
                "Missing update metadata in SKILL.md. "
                "Expected update_repo and update_skill_path."
            )
            _print_result(result, args.compact)
            return 0

        lock_path, lock_entry = _load_lock_entry(skill_name, skill_root, args.lock_file)
        if lock_entry is None:
            result["error"] = (
                "No lock entry was found for `causal-abel`. "
                "The skill may need to be installed with the public skills CLI."
            )
            _print_result(result, args.compact)
            return 0

        scope = _detect_install_scope(skill_name, args.timeout)
        result["scope"] = scope

        source_url = lock_entry.get("sourceUrl")
        if not isinstance(source_url, str) or not source_url.strip():
            source_url = _source_url_from_repo(repo)
        else:
            source_url = source_url.removesuffix(".git")
        result["next_command"] = _build_update_command(source_url, skill_name, scope)

        tracked_repo = lock_entry.get("source")
        tracked_skill_path = lock_entry.get("skillPath")
        local_hash = lock_entry.get("skillFolderHash")

        if not isinstance(tracked_repo, str) or not tracked_repo.strip():
            tracked_repo = repo
        if not isinstance(tracked_skill_path, str) or not tracked_skill_path.strip():
            tracked_skill_path = f"{skill_path}/SKILL.md"
        if not isinstance(local_hash, str) or not local_hash.strip():
            result["error"] = (
                "The lock entry for `causal-abel` does not contain a recorded "
                "folder hash, so the installed version cannot be compared."
            )
            _print_result(result, args.compact)
            return 0

        remote_hash = _fetch_skill_folder_hash(
            tracked_repo,
            tracked_skill_path,
            args.timeout,
            token,
        )
        result["checked"] = remote_hash is not None
        if remote_hash is None:
            result["error"] = "GitHub folder metadata for `causal-abel` could not be read."
            _print_result(result, args.compact)
            return 0

        if remote_hash == local_hash:
            result["ok"] = True
            _print_result(result, args.compact)
            return 0

        result["update_available"] = True
        remote_skill_url = _build_raw_url(repo, branch, f"{skill_path}/SKILL.md")
        remote_skill_text = _fetch_text(remote_skill_url, args.timeout)
        remote_metadata = _parse_frontmatter(remote_skill_text)
        result["remote_version"] = remote_metadata.get("version") or None

        try:
            remote_changelog_url = _build_raw_url(
                repo,
                branch,
                f"{skill_path}/{changelog_path}",
            )
            remote_changelog_text = _fetch_text(remote_changelog_url, args.timeout)
            sections = _parse_changelog_sections(remote_changelog_text)
            result["summary"] = _summarize_sections(
                sections,
                current_version,
                args.max_summary_items,
            )
        except urllib.error.HTTPError as exc:
            result["error"] = (
                "An update exists, but the remote CHANGELOG.md could not be read: "
                f"HTTP {exc.code}."
            )
        except urllib.error.URLError as exc:
            result["error"] = (
                "An update exists, but the remote CHANGELOG.md could not be read: "
                f"{exc.reason}."
            )

        result["ok"] = True
        _print_result(result, args.compact)
        return 0
    except subprocess.TimeoutExpired:
        result["error"] = "The update check timed out."
        _print_result(result, args.compact)
        return 0
    except FileNotFoundError as exc:
        result["error"] = f"Required command or file not found: {exc}."
        _print_result(result, args.compact)
        return 0
    except urllib.error.HTTPError as exc:
        result["error"] = f"Remote update metadata could not be read: HTTP {exc.code}."
        _print_result(result, args.compact)
        return 0
    except urllib.error.URLError as exc:
        result["error"] = f"Remote update metadata could not be read: {exc.reason}."
        _print_result(result, args.compact)
        return 0
    except Exception as exc:
        result["error"] = str(exc)
        _print_result(result, args.compact)
        return 0


def _print_result(result: dict[str, Any], compact: bool) -> None:
    if compact:
        json.dump(result, sys.stdout, ensure_ascii=True, separators=(",", ":"))
    else:
        json.dump(result, sys.stdout, ensure_ascii=True, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
