from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_render_skill_renders_current_public_skill(tmp_path) -> None:
    output_dir = tmp_path / "rendered-causal-abel"
    command = [
        "python3",
        "maintainers/causal-abel/render_skill.py",
        "--profile",
        "prod",
        "--source-dir",
        "skills/causal-abel",
        "--output-dir",
        str(output_dir),
    ]

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (output_dir / "SKILL.md").exists()
