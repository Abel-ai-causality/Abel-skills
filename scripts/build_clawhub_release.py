#!/usr/bin/env python3
"""Assemble a ClawHub-ready skill artifact from the source skill."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


SKILL_NAME = "causal-abel"
SOURCE_ROOT = Path(__file__).resolve().parents[1] / SKILL_NAME
DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "dist" / "clawhub"
REMOVE_FRONTMATTER_KEYS = {
    "update_repo",
    "update_branch",
    "update_skill_path",
    "update_changelog_path",
}

NEW_INSTALL_SECTION = """## Install And Authorization

If the user installs this skill, asks to connect Abel, or the workflow is missing an Abel API key, follow `references/setup-guide.md` exactly.

- Start the Abel agent OAuth handoff immediately instead of asking for manual credentials.
- Return `data.authUrl` to the user, not the `/authorize/agent` API URL.
- Store `data.resultUrl` or `data.pollToken`, ask the user to reply once Google authorization is complete, and only then poll until the result is `authorized`, `failed`, or expired.
- Persist the resulting `data.apiKey` in session state and `.env.skill` when local storage is available.
- Do not continue to live CAP probing until that key is present.
- Never ask the user to paste an email address or Google OAuth code.
"""

UPDATE_REFERENCE_LINE = (
    "- First-use soft update detection and changelog summary flow: `references/update-flow.md`\n"
)

CLAWHUB_OPENAI_YAML = """interface:
  display_name: "Causal Abel"
  short_description: "Causal reads through the Abel CAP surface."
  default_prompt: >
    Use $causal-abel to answer direct CAP graph questions, capability audits,
    or proxy-routed decision questions through the live Abel CAP server, and
    if `ABEL_API_KEY` is missing start the Abel OAuth handoff from
    `references/setup-guide.md` before any live API call.
"""


def ignore_copy_patterns(_directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if (
            name == "__pycache__"
            or name.endswith(".pyc")
            or name
            in {
                ".env.skill",
                ".env.skill.example",
                ".env.skills",
                ".env.skills.example",
            }
        ):
            ignored.add(name)
    return ignored


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a ClawHub-ready release artifact for causal-abel."
    )
    parser.add_argument(
        "--source",
        default=str(SOURCE_ROOT),
        help="Path to the source skill directory.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="Directory that will contain the built skill folder.",
    )
    parser.add_argument(
        "--version",
        default="",
        help="Optional version override written into the built SKILL.md.",
    )
    return parser.parse_args()


def split_frontmatter(text: str) -> tuple[list[str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md is missing YAML frontmatter.")

    frontmatter: list[str] = []
    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
        frontmatter.append(line)

    if end_index is None:
        raise ValueError("SKILL.md frontmatter is not terminated.")

    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    return frontmatter, body


def build_frontmatter(lines: list[str], version_override: str) -> str:
    out: list[str] = []
    version_written = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            out.append(line)
            continue
        if not line[0].isspace() and ":" in line:
            key = line.split(":", 1)[0].strip()
            if key in REMOVE_FRONTMATTER_KEYS:
                continue
            if key == "version" and version_override:
                out.append(f"version: {version_override}")
                version_written = True
                continue
        out.append(line)

    if version_override and not version_written:
        out.insert(1, f"version: {version_override}")

    return "---\n" + "\n".join(out).rstrip() + "\n---\n\n"


def remove_section_if_present(body: str, heading: str) -> str:
    section_range = find_section_range(body, heading)
    if section_range is None:
        return body
    start, end = section_range
    if end == len(body):
        return body[:start].rstrip() + "\n"
    return body[:start].rstrip() + "\n\n" + body[end:].lstrip()


def find_section_range(body: str, heading: str) -> tuple[int, int] | None:
    marker = f"## {heading}\n\n"
    start = body.find(marker)
    if start == -1:
        return None
    next_heading = body.find("\n## ", start + len(marker))
    if next_heading == -1:
        return start, len(body)
    return start, next_heading + 1


def replace_section(body: str, heading: str, new_section: str) -> str:
    section_range = find_section_range(body, heading)
    if section_range is None:
        raise ValueError(f"Could not find section `{heading}` in SKILL.md.")
    start, end = section_range
    replacement = new_section.rstrip() + "\n\n"
    return body[:start] + replacement + body[end:]


def replace_or_insert_section(
    body: str,
    headings: tuple[str, ...],
    new_section: str,
) -> str:
    for heading in headings:
        section_range = find_section_range(body, heading)
        if section_range is None:
            continue
        start, end = section_range
        replacement = new_section.rstrip() + "\n\n"
        return body[:start] + replacement + body[end:]

    first_heading = body.find("\n## ")
    replacement = new_section.rstrip() + "\n\n"
    if first_heading == -1:
        return body.rstrip() + "\n\n" + new_section.rstrip() + "\n"
    return (
        body[:first_heading].rstrip()
        + "\n\n"
        + replacement
        + body[first_heading + 1 :].lstrip()
    )


def remove_line(body: str, line: str, description: str) -> str:
    target = line.rstrip("\n")
    replacement = target + "\n"
    if replacement not in body:
        raise ValueError(f"Expected to find {description}, but it was missing.")
    return body.replace(replacement, "", 1)


def remove_line_if_present(body: str, line: str) -> str:
    target = line.rstrip("\n") + "\n"
    if target not in body:
        return body
    return body.replace(target, "", 1)


def transform_skill_md(source_text: str, version_override: str) -> str:
    frontmatter_lines, body = split_frontmatter(source_text)
    frontmatter = build_frontmatter(frontmatter_lines, version_override)
    body = remove_section_if_present(body, "First-Use Update Check")
    body = remove_line_if_present(
        body,
        "- On first session use, attempt the soft update check from `references/update-flow.md`.",
    )
    body = replace_or_insert_section(
        body,
        ("Install And Authorization", "Authorization Gate"),
        NEW_INSTALL_SECTION,
    )
    body = remove_line_if_present(body, UPDATE_REFERENCE_LINE)
    return frontmatter + body.rstrip() + "\n"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def remove_if_exists(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    output_dir = output_root / SKILL_NAME

    if not source_dir.exists():
        raise SystemExit(f"Source skill directory not found: {source_dir}")

    remove_if_exists(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, output_dir, ignore=ignore_copy_patterns)

    skill_text = (output_dir / "SKILL.md").read_text(encoding="utf-8")
    write_text(
        output_dir / "SKILL.md", transform_skill_md(skill_text, args.version.strip())
    )
    write_text(output_dir / "agents" / "openai.yaml", CLAWHUB_OPENAI_YAML)

    remove_if_exists(output_dir / "CHANGELOG.md")
    remove_if_exists(output_dir / ".env.skill")
    remove_if_exists(output_dir / ".env.skill.example")
    remove_if_exists(output_dir / ".env.skills")
    remove_if_exists(output_dir / ".env.skills.example")
    remove_if_exists(output_dir / "scripts" / "check_skill_update.py")
    remove_if_exists(output_dir / "references" / "update-flow.md")

    print(f"Built ClawHub artifact at {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
