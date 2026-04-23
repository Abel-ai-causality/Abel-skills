from pathlib import Path


def test_strategy_discovery_bootstrap_script_exists() -> None:
    script = Path("skills/abel-strategy-discovery/scripts/bootstrap_workspace.py")
    assert script.exists(), "bootstrap script is missing"
