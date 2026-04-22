from __future__ import annotations

from pathlib import Path


ENV_FILE_BASENAMES = (".env.skill", ".env.skills")
ENV_FALLBACK_BASENAME = ".env"


def preferred_auth_files(skill_root: Path) -> list[Path]:
    return [
        skill_root / ".env.skill",
        skill_root / ".env.skills",
        skill_root / ".env",
    ]


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
    return candidates
