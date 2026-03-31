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
