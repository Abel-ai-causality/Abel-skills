from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
ENDPOINT_CONFIG_PATH = (
    REPO_ROOT / "maintainers" / "abel-ask" / "endpoint_config.py"
)


def _load_endpoint_config_module():
    spec = importlib.util.spec_from_file_location(
        "abel_ask_endpoint_config",
        ENDPOINT_CONFIG_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_profiles_preserves_optional_narrative_fields() -> None:
    endpoint_config = _load_endpoint_config_module()

    config = {
        "active_profile": "sit",
        "profiles": {
            "sit": {
                "cap_base_url": "https://cap-sit.abel.ai/api",
                "oauth_base_url": "https://api-sit.abel.ai/echo/",
                "narrative_cap_base_url": "https://abel-data-intelligence-sit.abel.ai",
                "narrative_cap_api_key_env": "ABEL_DATA_INTEL_API_KEY",
            }
        },
    }

    profiles = endpoint_config.get_profiles(config)

    assert profiles["sit"]["narrative_cap_base_url"] == (
        "https://abel-data-intelligence-sit.abel.ai"
    )
    assert profiles["sit"]["narrative_cap_api_key_env"] == (
        "ABEL_DATA_INTEL_API_KEY"
    )


def test_get_template_values_exposes_active_narrative_base_url() -> None:
    endpoint_config = _load_endpoint_config_module()

    config = {
        "active_profile": "sit",
        "profiles": {
            "sit": {
                "cap_base_url": "https://cap-sit.abel.ai/api",
                "oauth_base_url": "https://api-sit.abel.ai/echo/",
                "narrative_cap_base_url": "https://abel-data-intelligence-sit.abel.ai",
            }
        },
    }

    values = endpoint_config.get_template_values(config)

    assert values["ACTIVE_NARRATIVE_CAP_BASE_URL"] == (
        "https://abel-data-intelligence-sit.abel.ai"
    )
    assert values["SIT_NARRATIVE_CAP_BASE_URL"] == (
        "https://abel-data-intelligence-sit.abel.ai"
    )
