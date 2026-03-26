#!/usr/bin/env python
"""Shared endpoint configuration for causal-abel scripts and docs."""

from __future__ import annotations

import json
import urllib.parse
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "endpoints.json"
AUTHORIZE_PATH = "web/credentials/oauth/google/authorize/agent"
RESULT_PATH_TEMPLATE = (
    "web/credentials/oauth/google/result?pollToken=POLL_TOKEN"
)
CALLBACK_PATH = "web/credentials/oauth/google/callback"


def load_endpoint_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def resolve_cap_endpoint(base_url: str) -> str:
    parsed = urllib.parse.urlsplit(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid base URL: {base_url!r}")
    path = parsed.path.rstrip("/")
    if path.endswith("/echo"):
        endpoint_path = f"{path}/api/v1/cap"
    else:
        endpoint_path = f"{path}/cap"
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, endpoint_path, "", "")
    )


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/"


def join_url(base_url: str, path: str) -> str:
    return urllib.parse.urljoin(normalize_base_url(base_url), path)


def _profile_label(name: str) -> str:
    labels = {"prod": "production", "sit": "SIT"}
    return labels.get(name, name)


def build_profile(name: str, profile: dict) -> dict[str, str]:
    cap_base_url = profile["cap_base_url"].rstrip("/")
    oauth_base_url = normalize_base_url(profile["oauth_base_url"])
    return {
        "name": name,
        "label": _profile_label(name),
        "cap_base_url": cap_base_url,
        "cap_endpoint_url": resolve_cap_endpoint(cap_base_url),
        "oauth_base_url": oauth_base_url,
        "authorize_agent_url": join_url(oauth_base_url, AUTHORIZE_PATH),
        "result_url_template": join_url(oauth_base_url, RESULT_PATH_TEMPLATE),
        "callback_url": join_url(oauth_base_url, CALLBACK_PATH),
        "callback_example_url": join_url(
            oauth_base_url, f"{CALLBACK_PATH}?code=GOOGLE_CODE&format=json"
        ),
    }


def get_profiles(config: dict | None = None) -> dict[str, dict[str, str]]:
    config = config or load_endpoint_config()
    return {
        name: build_profile(name, profile)
        for name, profile in config["profiles"].items()
    }


def get_active_profile(config: dict | None = None) -> dict[str, str]:
    config = config or load_endpoint_config()
    profiles = get_profiles(config)
    return profiles[config["active_profile"]]


def get_template_values(config: dict | None = None) -> dict[str, str]:
    config = config or load_endpoint_config()
    profiles = get_profiles(config)
    active = profiles[config["active_profile"]]
    values = {
        "ACTIVE_PROFILE": active["name"],
        "ACTIVE_PROFILE_LABEL": active["label"],
        "ACTIVE_CAP_BASE_URL": active["cap_base_url"],
        "ACTIVE_CAP_ENDPOINT_URL": active["cap_endpoint_url"],
        "ACTIVE_OAUTH_BASE_URL": active["oauth_base_url"],
        "ACTIVE_AUTHORIZE_AGENT_URL": active["authorize_agent_url"],
        "ACTIVE_RESULT_URL_TEMPLATE": active["result_url_template"],
        "ACTIVE_CALLBACK_URL": active["callback_url"],
        "ACTIVE_CALLBACK_EXAMPLE_URL": active["callback_example_url"],
    }
    for name, profile in profiles.items():
        prefix = name.upper()
        values[f"{prefix}_PROFILE_LABEL"] = profile["label"]
        values[f"{prefix}_CAP_BASE_URL"] = profile["cap_base_url"]
        values[f"{prefix}_CAP_ENDPOINT_URL"] = profile["cap_endpoint_url"]
        values[f"{prefix}_OAUTH_BASE_URL"] = profile["oauth_base_url"]
        values[f"{prefix}_AUTHORIZE_AGENT_URL"] = profile["authorize_agent_url"]
        values[f"{prefix}_RESULT_URL_TEMPLATE"] = profile["result_url_template"]
        values[f"{prefix}_CALLBACK_URL"] = profile["callback_url"]
        values[f"{prefix}_CALLBACK_EXAMPLE_URL"] = profile[
            "callback_example_url"
        ]
    return values
