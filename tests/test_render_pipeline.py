"""Tests for the render and build pipeline — verify public skill integrity."""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "causal-abel"
CLAWHUB_DIR = ROOT / "clawhub" / "causal-abel"
MAINTAINERS_DIR = ROOT / "maintainers" / "causal-abel"


class TestSkillIntegrity:
    def test_skill_md_exists(self):
        assert (SKILL_DIR / "SKILL.md").is_file()

    def test_skill_md_under_200_lines(self):
        lines = (SKILL_DIR / "SKILL.md").read_text().splitlines()
        assert len(lines) <= 200, (
            f"SKILL.md is {len(lines)} lines (max 200). "
            f"Fix: move detail to references/ files."
        )

    def test_skill_md_has_frontmatter(self):
        text = (SKILL_DIR / "SKILL.md").read_text()
        assert text.startswith("---"), "SKILL.md must start with YAML frontmatter"
        assert text.count("---") >= 2, "SKILL.md frontmatter not closed"

    def test_skill_md_version_present(self):
        text = (SKILL_DIR / "SKILL.md").read_text()
        assert "version:" in text, "SKILL.md must have a version field"

    def test_all_referenced_files_exist(self):
        text = (SKILL_DIR / "SKILL.md").read_text()
        refs = re.findall(r'references/[a-z/\-]+\.md', text)
        missing = [r for r in refs if not (SKILL_DIR / r).is_file()]
        assert not missing, (
            f"SKILL.md references missing files: {missing}. "
            f"Fix: create them or remove from SKILL.md."
        )

    def test_all_reference_files_non_empty(self):
        ref_dir = SKILL_DIR / "references"
        if ref_dir.is_dir():
            for f in ref_dir.rglob("*.md"):
                content = f.read_text().strip()
                assert len(content) > 10, f"{f.name} is empty or near-empty"


class TestEndpointIsolation:
    PRIVATE_PATTERNS = [
        r'cap-sit', r'api-sit', r'localhost', r'127\.0\.0\.1',
        r'10\.\d+\.\d+\.\d+', r'192\.168\.',
    ]

    def _scan_dir(self, directory: Path):
        """Scan a directory for private endpoint patterns."""
        violations = []
        if not directory.is_dir():
            return violations
        for f in directory.rglob("*"):
            if f.is_file() and f.suffix in ('.md', '.py', '.yaml', '.json'):
                text = f.read_text()
                for pat in self.PRIVATE_PATTERNS:
                    if re.search(pat, text):
                        violations.append(f"{f.relative_to(directory)}: matches '{pat}'")
        return violations

    def test_public_skill_no_private_endpoints(self):
        violations = self._scan_dir(SKILL_DIR)
        assert not violations, (
            f"Private endpoints in public skill:\n"
            + "\n".join(f"  ❌ {v}" for v in violations)
            + "\nFix: remove private endpoints and re-render."
        )

    def test_clawhub_artifact_no_private_endpoints(self):
        violations = self._scan_dir(CLAWHUB_DIR)
        assert not violations, (
            f"Private endpoints in ClawHub artifact:\n"
            + "\n".join(f"  ❌ {v}" for v in violations)
            + "\nFix: re-run build_clawhub_release.py from clean public skill."
        )


class TestMaintainerConfig:
    def test_endpoints_json_exists(self):
        assert (MAINTAINERS_DIR / "endpoints.json").is_file()

    def test_endpoints_json_valid(self):
        data = json.loads((MAINTAINERS_DIR / "endpoints.json").read_text())
        assert isinstance(data, dict)

    def test_render_script_exists(self):
        assert (MAINTAINERS_DIR / "render_skill.py").is_file()

    def test_local_endpoints_not_committed(self):
        local_file = MAINTAINERS_DIR / "endpoints.local.json"
        assert not local_file.is_file(), (
            "endpoints.local.json should be gitignored, not committed. "
            "Fix: git rm maintainers/causal-abel/endpoints.local.json"
        )


class TestClaudemd:
    def test_claude_md_exists(self):
        assert (ROOT / "CLAUDE.md").is_file()

    def test_claude_md_under_60_lines(self):
        lines = (ROOT / "CLAUDE.md").read_text().splitlines()
        assert len(lines) <= 60, (
            f"CLAUDE.md is {len(lines)} lines (max 60). "
            f"Fix: it's a map, not a manual."
        )
