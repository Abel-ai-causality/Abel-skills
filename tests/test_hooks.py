"""Tests for plugin hooks — verify they fire correctly and produce valid JSON."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent / "causal-abel" / "hooks"


def run_hook(script_name: str, stdin_data: str, timeout=5):
    """Run a hook script with JSON stdin and return parsed output."""
    script = HOOKS_DIR / script_name
    result = subprocess.run(
        ["bash", str(script)],
        capture_output=True, text=True, timeout=timeout, input=stdin_data
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class TestHooksJson:
    def test_hooks_json_exists(self):
        assert (HOOKS_DIR / "hooks.json").is_file()

    def test_hooks_json_valid(self):
        data = json.loads((HOOKS_DIR / "hooks.json").read_text())
        assert "hooks" in data

    def test_hooks_json_references_existing_scripts(self):
        data = json.loads((HOOKS_DIR / "hooks.json").read_text())
        for event, groups in data["hooks"].items():
            for group in groups:
                for hook in group["hooks"]:
                    cmd = hook["command"]
                    # Replace plugin root variable with actual path
                    script_name = cmd.split("/")[-1]
                    assert (HOOKS_DIR / script_name).is_file(), (
                        f"Hook references {script_name} but file doesn't exist. "
                        f"Fix: create {HOOKS_DIR / script_name}"
                    )

    def test_all_hook_scripts_executable(self):
        import os
        for sh in HOOKS_DIR.glob("*.sh"):
            assert os.access(sh, os.X_OK), (
                f"{sh.name} is not executable. Fix: chmod +x {sh}"
            )


class TestPostAbelVerify:
    def test_fires_on_abel_skill(self):
        rc, out, err = run_hook(
            "post-abel-verify.sh",
            '{"tool_input":{"skill":"abel"}}'
        )
        assert rc == 0
        data = json.loads(out)
        assert "Abel Harness" in data["hookSpecificOutput"]["additionalContext"]

    def test_fires_on_causal_abel_skill(self):
        rc, out, err = run_hook(
            "post-abel-verify.sh",
            '{"tool_input":{"skill":"causal-abel"}}'
        )
        assert rc == 0
        assert "Abel Harness" in out

    def test_silent_on_unrelated_skill(self):
        rc, out, err = run_hook(
            "post-abel-verify.sh",
            '{"tool_input":{"skill":"harness-engineering"}}'
        )
        assert out == ""

    def test_output_is_valid_json_when_fired(self):
        rc, out, err = run_hook(
            "post-abel-verify.sh",
            '{"tool_input":{"skill":"abel"}}'
        )
        data = json.loads(out)
        assert "hookSpecificOutput" in data
        assert "additionalContext" in data["hookSpecificOutput"]


class TestPostProbeCheck:
    def test_catches_401(self):
        rc, out, err = run_hook(
            "post-probe-check.sh",
            '{"tool_input":{"command":"python cap_probe.py observe X"},"tool_response":"{\\"ok\\": false, \\"status_code\\": 401}"}'
        )
        assert "401" in out
        assert "ABEL_API_KEY" in out

    def test_catches_503(self):
        rc, out, err = run_hook(
            "post-probe-check.sh",
            '{"tool_input":{"command":"python cap_probe.py observe X"},"tool_response":"{\\"ok\\": false, \\"status_code\\": 503}"}'
        )
        assert "503" in out

    def test_silent_on_success(self):
        rc, out, err = run_hook(
            "post-probe-check.sh",
            '{"tool_input":{"command":"python cap_probe.py observe X"},"tool_response":"{\\"ok\\": true}"}'
        )
        assert out == ""

    def test_silent_on_non_probe_command(self):
        rc, out, err = run_hook(
            "post-probe-check.sh",
            '{"tool_input":{"command":"ls -la"},"tool_response":""}'
        )
        assert out == ""


class TestPluginJson:
    def test_plugin_json_exists(self):
        pj = Path(__file__).resolve().parent.parent / "causal-abel" / ".claude-plugin" / "plugin.json"
        assert pj.is_file()

    def test_plugin_json_valid(self):
        pj = Path(__file__).resolve().parent.parent / "causal-abel" / ".claude-plugin" / "plugin.json"
        data = json.loads(pj.read_text())
        assert data["name"] == "causal-abel"
        assert "version" in data
        assert "author" in data
