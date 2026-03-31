from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "bootstrap_cap_server.py"
FIXTURES_DIR = SKILL_ROOT / "tests" / "fixtures"


def test_parse_json_output_ignores_non_json_lines() -> None:
    payload = _parse_json_output('bootstrap log\n{"status":"success","result":{}}\n')
    assert payload["status"] == "success"


def test_help_lists_runtime_shape_and_json_graph_flags() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        text=True,
        capture_output=True,
        check=True,
    )
    assert "--runtime-shape" in result.stdout
    assert "--nodes-path" in result.stdout
    assert "--edges-path" in result.stdout
    assert "--node-key-field" in result.stdout
    assert "--node-id-field" in result.stdout


def test_json_graph_requires_nodes_and_edges(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "demo",
            "--output-dir",
            str(tmp_path),
            "--runtime-shape",
            "json-graph",
        ],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "--nodes-path" in result.stderr
    assert "--edges-path" in result.stderr


def _parse_json_output(stdout: str) -> dict:
    for line in reversed(stdout.splitlines()):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise AssertionError(f"No JSON object found in subprocess stdout: {stdout!r}")


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


def sync_generated_project(project_dir: Path) -> None:
    if (project_dir / ".venv").exists():
        return
    subprocess.run(
        ["uv", "sync", "--extra", "dev"],
        cwd=project_dir,
        text=True,
        capture_output=True,
        check=True,
    )


def import_generated_module(project_dir: Path, module_name: str) -> subprocess.CompletedProcess[str]:
    sync_generated_project(project_dir)
    return subprocess.run(
        ["uv", "run", "python", "-c", f"import {module_name}"],
        text=True,
        capture_output=True,
        cwd=project_dir,
    )


def run_generated_pytest(project_dir: Path) -> subprocess.CompletedProcess[str]:
    sync_generated_project(project_dir)
    return subprocess.run(
        ["uv", "run", "pytest", "tests/test_app.py", "-q"],
        text=True,
        capture_output=True,
        cwd=project_dir,
    )


def invoke_generated_app(project_dir: Path, *, package_name: str, verb: str, params: dict) -> dict:
    sync_generated_project(project_dir)
    script = f"""
import json
from fastapi.testclient import TestClient
from {package_name}.app import app

client = TestClient(app)
response = client.post(
    "/cap",
    json={{"cap_version": "0.2.2", "request_id": "req-smoke", "verb": "{verb}", "params": {params!r}}},
)
print(json.dumps(response.json()))
"""
    result = subprocess.run(
        ["uv", "run", "python", "-c", script],
        text=True,
        capture_output=True,
        cwd=project_dir,
        check=True,
    )
    return _parse_json_output(result.stdout)


def invoke_generated_well_known(project_dir: Path, *, package_name: str) -> dict:
    sync_generated_project(project_dir)
    script = f"""
import json
from fastapi.testclient import TestClient
from {package_name}.app import app

client = TestClient(app)
response = client.get("/.well-known/cap.json")
print(json.dumps(response.json()))
"""
    result = subprocess.run(
        ["uv", "run", "python", "-c", script],
        text=True,
        capture_output=True,
        cwd=project_dir,
        check=True,
    )
    return _parse_json_output(result.stdout)


def assert_uv_workflow_files(project_dir: Path) -> None:
    readme_text = (project_dir / "README.md").read_text()
    assert "uv sync --extra dev" in readme_text
    assert "uv run uvicorn" in readme_text
    assert "uv run pytest" in readme_text
    assert "meta.methods" in readme_text
    assert "graph.neighbors" in readme_text
    assert "graph.paths" in readme_text
    assert "single deployed graph" in readme_text

    pyproject_text = (project_dir / "pyproject.toml").read_text()
    assert 'requires-python = ">=3.11"' in pyproject_text
    assert "[tool.uv]" in pyproject_text
    assert "package = true" in pyproject_text


def generate_json_graph_project(tmp_path: Path) -> Path:
    return run_generator(
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


def test_generated_app_module_imports_with_released_cap_protocol(tmp_path: Path) -> None:
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


def test_generated_level1_files_use_uv_workflow(tmp_path: Path) -> None:
    project_dir = run_generator(
        tmp_path,
        "smoke-level1-uv",
        "--predictor-mode",
        "stub",
        "--with-paths",
    )

    assert_uv_workflow_files(project_dir)


def test_generated_level2_app_module_imports_with_released_cap_protocol(tmp_path: Path) -> None:
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


def test_generated_level2_files_use_uv_workflow(tmp_path: Path) -> None:
    project_dir = run_generator(
        tmp_path,
        "smoke-level2-uv",
        "--level",
        "2",
        "--predictor-mode",
        "stub",
        "--intervention-mode",
        "stub",
        "--with-paths",
    )

    assert_uv_workflow_files(project_dir)


def test_generic_runtime_defaults_to_structural_surface(tmp_path: Path) -> None:
    project_dir = run_generator(
        tmp_path,
        "generic-runtime-default",
        "--with-paths",
    )

    capability = invoke_generated_well_known(
        project_dir,
        package_name="generic_runtime_default",
    )
    assert "observe.predict" not in capability["supported_verbs"]["core"]


def test_level2_generic_runtime_defaults_to_structural_surface(tmp_path: Path) -> None:
    project_dir = run_generator(
        tmp_path,
        "generic-runtime-level2-default",
        "--level",
        "2",
    )

    capability = invoke_generated_well_known(
        project_dir,
        package_name="generic_runtime_level2_default",
    )
    assert "observe.predict" not in capability["supported_verbs"]["core"]
    assert "intervene.do" not in capability["supported_verbs"]["core"]


def test_json_graph_scaffold_serves_structural_verbs(tmp_path: Path) -> None:
    project_dir = generate_json_graph_project(tmp_path)

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
    assert neighbors_response["result"]["neighbors"] == [
        {"node_id": "coin.aptos.market_caps", "roles": ["child"]}
    ]

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

    capability = invoke_generated_well_known(
        project_dir,
        package_name="json_graph_level1",
    )
    assert capability["graph"]["node_count"] == 3
    assert capability["graph"]["edge_count"] == 2


def test_json_graph_paths_are_bounded(tmp_path: Path) -> None:
    project_dir = generate_json_graph_project(tmp_path)

    response = invoke_generated_app(
        project_dir,
        package_name="json_graph_level1",
        verb="graph.paths",
        params={
            "source_node_id": "coin.aave.market_caps",
            "target_node_id": "coin.ethena.market_caps",
            "max_paths": 3,
        },
    )
    assert response["status"] == "success"
    assert response["result"]["path_count"] == 1
    assert len(response["result"]["paths"]) == 1
    assert response["result"]["paths"][0]["distance"] == 2


def test_json_graph_scaffold_generated_pytest_suite_passes(tmp_path: Path) -> None:
    project_dir = generate_json_graph_project(tmp_path)

    result = run_generated_pytest(project_dir)

    assert result.returncode == 0, result.stdout + "\n" + result.stderr
