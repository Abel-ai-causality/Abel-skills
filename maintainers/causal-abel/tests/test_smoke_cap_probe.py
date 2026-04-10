from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SMOKE_CAP_PROBE_PATH = REPO_ROOT / "maintainers" / "causal-abel" / "smoke_cap_probe.py"


def _load_smoke_cap_probe_module():
    spec = importlib.util.spec_from_file_location(
        "causal_abel_smoke_cap_probe",
        SMOKE_CAP_PROBE_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_skill_root_points_to_local_dist() -> None:
    smoke_cap_probe = _load_smoke_cap_probe_module()

    assert smoke_cap_probe.DEFAULT_SKILL_ROOT == REPO_ROOT / "dist" / "local" / "causal-abel"


def test_build_cap_probe_command_targets_dist_local_script() -> None:
    smoke_cap_probe = _load_smoke_cap_probe_module()

    skill_root = Path("/tmp/causal-abel")

    command = smoke_cap_probe.build_cap_probe_command(
        skill_root,
        ["observe-dual", "BTCM"],
    )

    assert command == [
        "python3",
        "/tmp/causal-abel/scripts/cap_probe.py",
        "--compact",
        "observe-dual",
        "BTCM",
    ]


def test_evaluate_ranked_nodes_checks_prefix_and_required_nodes() -> None:
    smoke_cap_probe = _load_smoke_cap_probe_module()

    actual = [
        "LFST.price",
        "LFST.volume",
        "CMPS.price",
        "CMPS.volume",
        "commercialBankInterestRateOnCreditCardPlansAllAccounts",
    ]

    assert smoke_cap_probe.evaluate_ranked_nodes(
        actual,
        expected_prefix=[
            "LFST.price",
            "LFST.volume",
            "CMPS.price",
            "CMPS.volume",
        ],
        required_nodes=["commercialBankInterestRateOnCreditCardPlansAllAccounts"],
    ) == []

    failures = smoke_cap_probe.evaluate_ranked_nodes(
        actual,
        expected_prefix=["LFST.price", "CMPS.price"],
        required_nodes=["consumerSentiment"],
    )

    assert failures == [
        "expected prefix ['LFST.price', 'CMPS.price'], got ['LFST.price', 'LFST.volume']",
        "missing required nodes ['consumerSentiment']",
    ]


def test_extract_variable_node_ids_reads_query_node_variables() -> None:
    smoke_cap_probe = _load_smoke_cap_probe_module()

    payload = {
        "result": {
            "variables": [
                {"node_id": "BTCM.price"},
                {"node_id": "BTCM.volume"},
                {"node_id": "RIOT.price"},
            ]
        }
    }

    assert smoke_cap_probe.extract_variable_node_ids(payload) == [
        "BTCM.price",
        "BTCM.volume",
        "RIOT.price",
    ]
