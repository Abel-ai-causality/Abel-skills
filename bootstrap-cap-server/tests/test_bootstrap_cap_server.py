from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "bootstrap_cap_server.py"
PYTHON_SDK_ROOT = Path("/Users/rayz/Documents/causal-agent-protocol/python-sdk")
FIXTURES_DIR = SKILL_ROOT / "tests" / "fixtures"


def run_generator(tmp_path: Path, project_name: str, *extra_args: str) -> Path:
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            project_name,
            "--output-dir",
            str(tmp_path),
            *extra_args,
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    return tmp_path / project_name


def import_generated_module(project_dir: Path, module_name: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{project_dir}:{PYTHON_SDK_ROOT}"
    return subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        text=True,
        capture_output=True,
        env=env,
    )


def invoke_generated_app(project_dir: Path, *, package_name: str, verb: str, params: dict) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{project_dir}:{PYTHON_SDK_ROOT}"
    script = f"""
from fastapi.testclient import TestClient
from {package_name}.app import app

client = TestClient(app)
response = client.post(
    "/cap",
    json={{"cap_version": "0.2.2", "request_id": "req-smoke", "verb": "{verb}", "params": {params!r}}},
)
print(response.json())
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        text=True,
        capture_output=True,
        env=env,
        check=True,
    )
    return ast.literal_eval(result.stdout.strip())


def test_help_omits_graph_ref_mode_and_graph_id_flags() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "--graph-ref-mode" not in result.stdout
    assert "--graph-id" not in result.stdout
    assert "--graph-version" in result.stdout


def test_level1_scaffold_defaults_to_single_graph_without_graph_ref_scaffolding(
    tmp_path: Path,
) -> None:
    project_dir = run_generator(
        tmp_path,
        "demo-level1",
        "--predictor-mode",
        "stub",
        "--with-paths",
    )

    config_text = (project_dir / "demo_level1" / "config.py").read_text()
    common_text = (project_dir / "demo_level1" / "handlers" / "common.py").read_text()
    graph_text = (project_dir / "demo_level1" / "handlers" / "graph.py").read_text()
    observe_text = (project_dir / "demo_level1" / "handlers" / "observe.py").read_text()
    capability_text = (project_dir / "demo_level1" / "capability.py").read_text()
    test_text = (project_dir / "tests" / "test_app.py").read_text()

    assert "GRAPH_VERSION" in config_text
    assert "GRAPH_ID" not in config_text
    assert "validate_graph_ref" not in common_text
    assert "validate_graph_ref" not in graph_text
    assert "validate_graph_ref" not in observe_text
    assert "graph_ref" not in test_text
    assert "one deployed graph by default" in capability_text


def test_level2_scaffold_uses_same_single_graph_default(tmp_path: Path) -> None:
    project_dir = run_generator(
        tmp_path,
        "demo-level2",
        "--level",
        "2",
        "--predictor-mode",
        "stub",
        "--intervention-mode",
        "stub",
    )

    common_text = (project_dir / "demo_level2" / "handlers" / "common.py").read_text()
    graph_text = (project_dir / "demo_level2" / "handlers" / "graph.py").read_text()
    observe_text = (project_dir / "demo_level2" / "handlers" / "observe.py").read_text()
    intervene_text = (project_dir / "demo_level2" / "handlers" / "intervene.py").read_text()
    capability_text = (project_dir / "demo_level2" / "capability.py").read_text()
    test_text = (project_dir / "tests" / "test_app.py").read_text()

    assert "validate_graph_ref" not in common_text
    assert "validate_graph_ref" not in graph_text
    assert "validate_graph_ref" not in observe_text
    assert "validate_graph_ref" not in intervene_text
    assert "graph_ref" not in test_text
    assert "one deployed graph by default" in capability_text


def test_generated_capability_modules_import_with_local_python_sdk(tmp_path: Path) -> None:
    level1_dir = run_generator(
        tmp_path,
        "import-level1",
        "--predictor-mode",
        "stub",
        "--with-paths",
    )
    level2_dir = run_generator(
        tmp_path,
        "import-level2",
        "--level",
        "2",
        "--predictor-mode",
        "stub",
        "--intervention-mode",
        "stub",
    )

    level1_result = import_generated_module(level1_dir, "import_level1.capability")
    assert level1_result.returncode == 0, level1_result.stderr

    level2_result = import_generated_module(level2_dir, "import_level2.capability")
    assert level2_result.returncode == 0, level2_result.stderr

    level2_intervene_result = import_generated_module(level2_dir, "import_level2.handlers.intervene")
    assert level2_intervene_result.returncode == 0, level2_intervene_result.stderr


def test_generated_app_module_imports_with_local_python_sdk(tmp_path: Path) -> None:
    project_dir = run_generator(
        tmp_path,
        "smoke-level1",
        "--runtime-shape",
        "generic-runtime",
        "--predictor-mode",
        "stub",
        "--with-paths",
    )

    result = import_generated_module(project_dir, "smoke_level1.app")
    assert result.returncode == 0, result.stderr

    readme_text = (project_dir / "README.md").read_text()
    assert "uv sync --extra dev" in readme_text
    assert "uv run uvicorn" in readme_text
    assert "uv run pytest" in readme_text


def test_generated_level2_app_module_imports_with_local_python_sdk(tmp_path: Path) -> None:
    project_dir = run_generator(
        tmp_path,
        "smoke-level2",
        "--level",
        "2",
        "--runtime-shape",
        "generic-runtime",
        "--predictor-mode",
        "stub",
        "--intervention-mode",
        "stub",
        "--with-paths",
    )

    result = import_generated_module(project_dir, "smoke_level2.app")
    assert result.returncode == 0, result.stderr


def test_json_graph_scaffold_serves_structural_verbs(tmp_path: Path) -> None:
    project_dir = run_generator(
        tmp_path,
        "json-graph-level1",
        "--runtime-shape",
        "json-graph",
        "--nodes-path",
        str(FIXTURES_DIR / "json_graph_nodes.json"),
        "--edges-path",
        str(FIXTURES_DIR / "json_graph_edges.json"),
        "--node-id-field",
        "full_name",
        "--source-field",
        "source_id",
        "--target-field",
        "target_id",
        "--with-paths",
    )

    meta_response = invoke_generated_app(
        project_dir,
        package_name="json_graph_level1",
        verb="meta.methods",
        params={"detail": "compact"},
    )
    assert meta_response["status"] == "success"
    methods = {item["verb"] for item in meta_response["result"]["methods"]}
    assert "meta.methods" in methods
    assert "graph.neighbors" in methods
    assert "graph.paths" in methods

    neighbors_response = invoke_generated_app(
        project_dir,
        package_name="json_graph_level1",
        verb="graph.neighbors",
        params={"node_id": "coin.aave.market_caps", "scope": "children"},
    )
    assert neighbors_response["status"] == "success"
    assert neighbors_response["result"]["node_id"] == "coin.aave.market_caps"

    paths_response = invoke_generated_app(
        project_dir,
        package_name="json_graph_level1",
        verb="graph.paths",
        params={
            "source_node_id": "coin.aave.market_caps",
            "target_node_id": "coin.ethena.market_caps",
            "max_paths": 3,
        },
    )
    assert paths_response["status"] == "success"
    assert paths_response["result"]["connected"] is True
