from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CAP_PROBE_PATH = REPO_ROOT / "skills" / "causal-abel" / "scripts" / "cap_probe.py"


def _load_cap_probe_module():
    spec = importlib.util.spec_from_file_location("causal_abel_cap_probe", CAP_PROBE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_paths_command_preserves_macro_canonical_node_ids(monkeypatch) -> None:
    cap_probe = _load_cap_probe_module()

    captured: dict[str, object] = {}

    def _fake_call_verb(args, verb: str, params: dict[str, object] | None = None) -> dict[str, object]:
        captured["verb"] = verb
        captured["params"] = params or {}
        return {"ok": True}

    monkeypatch.setattr(cap_probe, "_call_verb", _fake_call_verb)

    args = argparse.Namespace(
        source_node_id="CPI",
        target_node_id="NVDA.price",
        max_paths=3,
        include_edge_signs=False,
        default_suffix="price",
    )

    result = cap_probe._cmd_paths(args)

    assert result == {"ok": True}
    assert captured["verb"] == "graph.paths"
    assert captured["params"] == {
        "source_node_id": "CPI",
        "target_node_id": "NVDA.price",
        "max_paths": 3,
    }


def test_paths_command_accepts_lowercase_macro_alias_as_canonical(monkeypatch) -> None:
    cap_probe = _load_cap_probe_module()

    captured: dict[str, object] = {}

    def _fake_call_verb(args, verb: str, params: dict[str, object] | None = None) -> dict[str, object]:
        captured["params"] = params or {}
        return {"ok": True}

    monkeypatch.setattr(cap_probe, "_call_verb", _fake_call_verb)

    args = argparse.Namespace(
        source_node_id="cpi",
        target_node_id="treasuryrateyear10",
        max_paths=2,
        include_edge_signs=False,
        default_suffix="price",
    )

    cap_probe._cmd_paths(args)

    assert captured["params"] == {
        "source_node_id": "CPI",
        "target_node_id": "treasuryRateYear10",
        "max_paths": 2,
    }


def test_paths_command_keeps_asset_normalization_for_tickers(monkeypatch) -> None:
    cap_probe = _load_cap_probe_module()

    captured: dict[str, object] = {}

    def _fake_call_verb(args, verb: str, params: dict[str, object] | None = None) -> dict[str, object]:
        captured["params"] = params or {}
        return {"ok": True}

    monkeypatch.setattr(cap_probe, "_call_verb", _fake_call_verb)

    args = argparse.Namespace(
        source_node_id="NVDA",
        target_node_id="AMD",
        max_paths=4,
        include_edge_signs=True,
        default_suffix="price",
    )

    cap_probe._cmd_paths(args)

    assert captured["params"] == {
        "source_node_id": "NVDA.price",
        "target_node_id": "AMD.price",
        "max_paths": 4,
        "include_edge_signs": True,
    }


def test_normalize_node_command_preserves_macro_canonical_node_id() -> None:
    cap_probe = _load_cap_probe_module()

    args = argparse.Namespace(
        input_value="CPI",
        default_suffix="price",
    )

    result = cap_probe._cmd_normalize_node(args)

    assert result == {
        "ok": True,
        "status_code": 0,
        "input": "CPI",
        "normalized_node_id": "CPI",
        "default_suffix": "price",
    }


def test_normalize_node_command_accepts_lowercase_macro_alias() -> None:
    cap_probe = _load_cap_probe_module()

    args = argparse.Namespace(
        input_value="cpi",
        default_suffix="price",
    )

    result = cap_probe._cmd_normalize_node(args)

    assert result == {
        "ok": True,
        "status_code": 0,
        "input": "cpi",
        "normalized_node_id": "CPI",
        "default_suffix": "price",
    }


def test_load_env_file_falls_back_to_dot_env_when_skill_env_missing(
    monkeypatch, tmp_path
) -> None:
    cap_probe = _load_cap_probe_module()

    monkeypatch.delenv("ABEL_API_KEY", raising=False)
    monkeypatch.delenv("CAP_API_KEY", raising=False)

    env_path = tmp_path / ".env"
    env_path.write_text("ABEL_API_KEY=abel-from-dot-env\n", encoding="utf-8")

    cap_probe._load_env_file(str(tmp_path / ".env.skill"))

    assert os.getenv("ABEL_API_KEY") == "abel-from-dot-env"


def test_load_env_file_prefers_skill_env_over_dot_env(monkeypatch, tmp_path) -> None:
    cap_probe = _load_cap_probe_module()

    monkeypatch.delenv("ABEL_API_KEY", raising=False)
    monkeypatch.delenv("CAP_API_KEY", raising=False)

    (tmp_path / ".env.skill").write_text(
        "ABEL_API_KEY=abel-from-dot-env-skill\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("ABEL_API_KEY=abel-from-dot-env\n", encoding="utf-8")

    cap_probe._load_env_file(str(tmp_path / ".env.skill"))

    assert os.getenv("ABEL_API_KEY") == "abel-from-dot-env-skill"
