from __future__ import annotations

from pathlib import Path


ENV_FILE_BASENAMES = (".env.skill", ".env.skills")
ENV_FALLBACK_BASENAME = ".env"
COLLECTION_SHARED_SKILLS = ("abel-auth", "abel", "abel-ask")


def preferred_auth_files(skill_root: Path) -> list[Path]:
    return [
        skill_root / ".env.skill",
        skill_root / ".env.skills",
        skill_root / ".env",
    ]


def _collection_auth_files(skill_root: Path) -> list[Path]:
    skill_root = skill_root.expanduser()
    skills_root = skill_root.parent
    if skills_root.name != "skills":
        return []

    files: list[Path] = []
    for basename in (*ENV_FILE_BASENAMES, ENV_FALLBACK_BASENAME):
        files.append(skills_root / basename)
    for sibling_name in COLLECTION_SHARED_SKILLS:
        sibling_root = skills_root / sibling_name
        if sibling_root == skill_root:
            continue
        files.extend(preferred_auth_files(sibling_root))
    return files


def candidate_env_files(path: str | Path) -> list[Path]:
    env_path = Path(path).expanduser()
    candidates = [env_path]
    if env_path.name in ENV_FILE_BASENAMES:
        for basename in ENV_FILE_BASENAMES:
            candidate = env_path.with_name(basename)
            if candidate not in candidates:
                candidates.append(candidate)
        fallback_candidate = env_path.with_name(ENV_FALLBACK_BASENAME)
        if fallback_candidate not in candidates:
            candidates.append(fallback_candidate)
        for candidate in _collection_auth_files(env_path.parent):
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates
