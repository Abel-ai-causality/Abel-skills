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
