# Changelog

All notable changes to `causal-abel` will be documented in this file.

This project follows a skill-local release log so the agent can summarize user-visible updates before asking to run `npx skills update`.

## [1.0.0] - 2026-03-23

### Added

- Explicit skill version metadata in `SKILL.md`.
- A skill-local `CHANGELOG.md` for release summaries.
- A bundled `scripts/check_skill_update.py` helper that runs `npx skills check`, reads the remote `SKILL.md` and `CHANGELOG.md`, and returns a machine-readable update summary.

### Changed

- The skill instructions now treat the first-use update check as a soft prerequisite before live Abel API usage.
- The update flow now checks only the installed `causal-abel` skill instead of scanning every tracked skill.
- The refresh guidance now uses a single-skill `npx skills add ... --skill causal-abel` command instead of `npx skills update`.
- The user-facing prompt is now intentionally warmer and ends with a short `Y/N` choice.

### Notes

- Update-check failures are intentionally non-blocking so the normal authorization and probing flow can continue.
