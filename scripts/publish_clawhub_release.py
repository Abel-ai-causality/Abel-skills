#!/usr/bin/env python3
"""Build and publish the ClawHub-ready skill artifact with the source version."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

import build_clawhub_release


VERSION_HEADING_PATTERN = re.compile(
    r"^##\s+\[(?P<version>[^\]]+)\](?:\s+-\s+(?P<date>.+))?$"
)
SECTION_HEADING_PATTERN = re.compile(r"^###\s+(?P<title>.+?)\s*$")
DISPLAY_NAME_PATTERN = re.compile(r'^\s*display_name:\s*"(?P<value>.+)"\s*$')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the ClawHub artifact and publish it with the exact version "
            "declared in the source SKILL.md."
        )
    )
    parser.add_argument(
        "--source",
        default=str(build_clawhub_release.SOURCE_ROOT),
        help="Path to the source skill directory.",
    )
    parser.add_argument(
        "--output-root",
        default=str(build_clawhub_release.DEFAULT_OUTPUT_ROOT),
        help="Directory where the ClawHub artifact will be built.",
    )
    parser.add_argument(
        "--changelog-file",
        default=str(Path(__file__).resolve().parents[1] / "CHANGELOG.md"),
        help="Repository changelog used to populate --changelog.",
    )
    parser.add_argument(
        "--slug",
        default="",
        help="Optional slug override. Defaults to the source skill name.",
    )
    parser.add_argument(
        "--name",
        default="",
        help="Optional display name override. Defaults to agents/openai.yaml display_name.",
    )
    parser.add_argument(
        "--tags",
        default="latest",
        help="Comma-separated tags passed to clawhub publish.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the publish command instead of executing it.",
    )
    parser.add_argument(
        "--skip-whoami-check",
        action="store_true",
        help="Skip `clawhub whoami` before publishing.",
    )
    return parser.parse_args()


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        raise ValueError("SKILL.md is missing YAML frontmatter.")

    lines = text.splitlines()
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


def load_skill_metadata(source_dir: Path) -> dict[str, str]:
    skill_md = source_dir / "SKILL.md"
    return parse_frontmatter(skill_md.read_text(encoding="utf-8"))


def load_display_name(source_dir: Path, fallback: str) -> str:
    openai_yaml = source_dir / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        return fallback
    for line in openai_yaml.read_text(encoding="utf-8").splitlines():
        match = DISPLAY_NAME_PATTERN.match(line)
        if match:
            value = match.group("value").strip()
            if value:
                return value
    return fallback


def parse_changelog_sections(text: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    current_subheading = ""

    for line in text.splitlines():
        version_match = VERSION_HEADING_PATTERN.match(line.strip())
        if version_match:
            if current is not None:
                sections.append(current)
            current = {
                "version": version_match.group("version").strip(),
                "groups": [],
            }
            current_subheading = ""
            continue

        if current is None:
            continue

        heading_match = SECTION_HEADING_PATTERN.match(line.strip())
        if heading_match:
            current_subheading = heading_match.group("title").strip()
            continue

        bullet = line.strip()
        if bullet.startswith("- "):
            groups = current["groups"]
            if isinstance(groups, list):
                groups.append((current_subheading, bullet[2:].strip()))

    if current is not None:
        sections.append(current)
    return sections


def build_changelog_text(changelog_path: Path, version: str) -> str:
    if not changelog_path.exists():
        return ""

    text = changelog_path.read_text(encoding="utf-8")
    sections = parse_changelog_sections(text)
    for section in sections:
        if section.get("version") != version:
            continue
        groups = section.get("groups")
        if not isinstance(groups, list) or not groups:
            return ""
        grouped: dict[str, list[str]] = {}
        ordered_titles: list[str] = []
        for title, item in groups:
            label = title or "Changes"
            if label not in grouped:
                grouped[label] = []
                ordered_titles.append(label)
            grouped[label].append(item)
        parts: list[str] = []
        for title in ordered_titles:
            items = grouped[title]
            parts.append(f"{title}: " + "; ".join(items))
        return " | ".join(parts)
    return ""


def build_artifact(source_dir: Path, output_root: Path) -> Path:
    command = [
        "python3",
        str(Path(__file__).resolve().parents[0] / "build_clawhub_release.py"),
        "--source",
        str(source_dir),
        "--output-root",
        str(output_root),
    ]
    subprocess.run(command, check=True)
    return output_root / build_clawhub_release.SKILL_NAME


def clawhub_command() -> list[str]:
    if shutil.which("clawhub"):
        return ["clawhub"]
    return ["npx", "--yes", "clawhub"]


def run_checked(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    changelog_path = Path(args.changelog_file).expanduser().resolve()

    metadata = load_skill_metadata(source_dir)
    slug = (args.slug or metadata.get("name") or source_dir.name).strip()
    version = (metadata.get("version") or "").strip()
    if not version:
        raise SystemExit("Source SKILL.md does not declare a version.")

    display_name = (args.name or load_display_name(source_dir, slug)).strip()
    if not display_name:
        raise SystemExit("Could not determine a display name for clawhub publish.")

    artifact_dir = build_artifact(source_dir, output_root)
    built_metadata = load_skill_metadata(artifact_dir)
    built_version = (built_metadata.get("version") or "").strip()
    if built_version != version:
        raise SystemExit(
            "Built artifact version does not match source SKILL.md: "
            f"source={version!r}, built={built_version!r}."
        )

    changelog_text = build_changelog_text(changelog_path, version)
    publish_command = [
        "clawhub",
        "publish",
        str(artifact_dir),
        "--slug",
        slug,
        "--name",
        display_name,
        "--version",
        version,
        "--changelog",
        changelog_text,
        "--tags",
        args.tags,
    ]

    if args.dry_run:
        print("Dry run: publish command")
        print(subprocess.list2cmdline(publish_command))
        return 0

    clawhub = clawhub_command()
    if not args.skip_whoami_check:
        run_checked([*clawhub, "whoami"])

    run_checked([*clawhub, *publish_command[1:]])
    print(f"Published {slug} version {version} from {artifact_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
