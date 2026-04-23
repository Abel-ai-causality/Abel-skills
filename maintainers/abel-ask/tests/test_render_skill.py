from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_render_skill_renders_current_public_skill(tmp_path) -> None:
    output_dir = tmp_path / "rendered-abel-ask"
    command = [
        "python3",
        "maintainers/abel-ask/render_skill.py",
        "--profile",
        "prod",
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
    assert (output_dir / "references" / "routes" / "proxy-routed.md").exists()
    assert (output_dir / "references" / "probe-usage.md").exists()
    assert (output_dir / "scripts" / "cap_probe.py").exists()

    rendered_route = (output_dir / "references" / "routes" / "proxy-routed.md").read_text(encoding="utf-8")
    rendered_probe_usage = (output_dir / "references" / "probe-usage.md").read_text(encoding="utf-8")

    assert "inspect `node_kind`" in rendered_route
    assert "typed results" in rendered_probe_usage
