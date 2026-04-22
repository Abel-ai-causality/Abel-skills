from pathlib import Path


def test_abel_auth_skill_mentions_reuse_then_oauth() -> None:
    text = Path("skills/abel-auth/SKILL.md").read_text(encoding="utf-8")
    assert "reuse existing auth" in text.lower()
    assert "oauth" in text.lower()
