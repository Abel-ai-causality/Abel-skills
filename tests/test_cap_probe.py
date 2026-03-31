"""Smoke tests for cap_probe.py — verify CLI parsing, output format, error handling."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROBE = Path(__file__).resolve().parent.parent / "causal-abel" / "scripts" / "cap_probe.py"


def run_probe(*args, stdin_data=None, timeout=15):
    """Run cap_probe.py and return (returncode, stdout, stderr)."""
    cmd = [sys.executable, str(PROBE)] + list(args)
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, input=stdin_data
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


class TestCLIParsing:
    def test_no_args_shows_help(self):
        rc, out, err = run_probe()
        assert rc != 0  # should fail without subcommand

    def test_help_flag(self):
        rc, out, err = run_probe("--help")
        assert rc == 0
        assert "cap_probe" in out or "usage" in out.lower()

    def test_capabilities_subcommand_exists(self):
        rc, out, err = run_probe("capabilities", "--help")
        assert rc == 0

    def test_observe_subcommand_exists(self):
        rc, out, err = run_probe("observe", "--help")
        assert rc == 0
        assert "target_node" in out

    def test_neighbors_subcommand_exists(self):
        rc, out, err = run_probe("neighbors", "--help")
        assert rc == 0

    def test_paths_subcommand_exists(self):
        rc, out, err = run_probe("paths", "--help")
        assert rc == 0

    def test_intervene_do_subcommand_exists(self):
        rc, out, err = run_probe("intervene-do", "--help")
        assert rc == 0
        assert "outcome-node" in out or "outcome_node" in out

    def test_normalize_node(self):
        rc, out, err = run_probe("normalize-node", "NVDA")
        assert rc == 0
        data = json.loads(out)
        assert data.get("ok") is True
        assert "NVDA" in out


class TestOutputFormat:
    def test_capabilities_returns_json(self):
        # Will fail with 401 without key, but should still return valid JSON
        rc, out, err = run_probe("capabilities")
        data = json.loads(out)
        assert "ok" in data

    def test_observe_without_key_returns_json_error(self):
        rc, out, err = run_probe("observe", "NVDA.price")
        data = json.loads(out)
        assert "ok" in data
        # Without API key, expect 401 or similar
        if not data["ok"]:
            assert data.get("status_code") in (401, 403, 500, None)

    def test_compact_flag_single_line(self):
        rc, out, err = run_probe("--compact", "normalize-node", "AAPL")
        # Compact should be single line (no pretty-print newlines)
        assert "\n" not in out or out.count("\n") <= 1


class TestErrorHandling:
    def test_invalid_subcommand(self):
        rc, out, err = run_probe("nonexistent-verb")
        assert rc != 0

    def test_missing_required_arg(self):
        rc, out, err = run_probe("observe")  # missing target_node
        assert rc != 0
