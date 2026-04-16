from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SMOKE_NARRATIVE_CAP_PROBE_PATH = (
    REPO_ROOT / "maintainers" / "causal-abel" / "smoke_narrative_cap_probe.py"
)


def _load_smoke_narrative_cap_probe_module():
    spec = importlib.util.spec_from_file_location(
        "causal_abel_smoke_narrative_cap_probe",
        SMOKE_NARRATIVE_CAP_PROBE_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_skill_root_points_to_local_dist() -> None:
    smoke_narrative_cap_probe = _load_smoke_narrative_cap_probe_module()

    assert smoke_narrative_cap_probe.DEFAULT_SKILL_ROOT == REPO_ROOT / "dist" / "local" / "causal-abel"


def test_build_narrative_cap_probe_command_targets_dist_local_script() -> None:
    smoke_narrative_cap_probe = _load_smoke_narrative_cap_probe_module()

    skill_root = Path("/tmp/causal-abel")

    command = smoke_narrative_cap_probe.build_narrative_cap_probe_command(
        skill_root,
        ["narrate", "--query", "AI datacenter demand and NVDA"],
    )

    assert command == [
        "python3",
        "/tmp/causal-abel/scripts/narrative_cap_probe.py",
        "--compact",
        "narrate",
        "--query",
        "AI datacenter demand and NVDA",
    ]


def test_run_checks_covers_query_node_extension(monkeypatch) -> None:
    smoke_narrative_cap_probe = _load_smoke_narrative_cap_probe_module()
    captured: list[list[str]] = []

    def _fake_run_probe(skill_root, probe_args):
        captured.append(list(probe_args))
        return {
            "command": ["python3", "narrative_cap_probe.py", *probe_args],
            "exit_code": 0,
            "payload": {"ok": True, "status_code": 200},
            "stderr": "",
        }

    monkeypatch.setattr(smoke_narrative_cap_probe, "_run_probe", _fake_run_probe)

    checks = smoke_narrative_cap_probe._run_checks(
        Path("/tmp/causal-abel"),
        "https://cap-sit.abel.ai/narrative",
    )

    assert [check["name"] for check in checks] == [
        "card",
        "methods",
        "narrate",
        "query-node",
        "search-prepare",
    ]
    assert any(args[-2:] == ["--query", smoke_narrative_cap_probe.DEFAULT_QUERY] for args in captured)
