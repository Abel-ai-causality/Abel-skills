from pathlib import Path

from shared.cap.auth import preferred_auth_files


def test_preferred_auth_files_include_skill_local_and_shared_paths(tmp_path: Path) -> None:
    files = preferred_auth_files(tmp_path / "skills" / "abel-ask")
    rendered = [str(item) for item in files]
    assert any(path.endswith(".env.skill") for path in rendered)
    assert any("abel-ask" in path for path in rendered)
