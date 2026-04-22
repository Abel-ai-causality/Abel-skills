from pathlib import Path

from abel_common.cap.auth import candidate_env_files, preferred_auth_files


def test_preferred_auth_files_include_skill_local_and_shared_paths(tmp_path: Path) -> None:
    files = preferred_auth_files(tmp_path / "skills" / "abel-ask")
    rendered = [str(item) for item in files]
    assert any(path.endswith(".env.skill") for path in rendered)
    assert any("abel-ask" in path for path in rendered)


def test_candidate_env_files_include_collection_shared_locations(tmp_path: Path) -> None:
    env_file = tmp_path / "skills" / "abel-ask" / ".env.skill"
    rendered = [str(item) for item in candidate_env_files(env_file)]

    assert str(tmp_path / "skills" / ".env.skill") in rendered
    assert str(tmp_path / "skills" / "abel-auth" / ".env.skill") in rendered
    assert str(tmp_path / "skills" / "abel" / ".env.skill") in rendered
