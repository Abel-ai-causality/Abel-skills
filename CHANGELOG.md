# Changelog

All notable changes to `causal-abel` will be documented in this file.

This project follows a repo-level release log so agents can summarize user-visible changes across GitHub and ClawHub-facing revisions.

## [1.0.1] - 2026-03-23

### Added

- Explicit `metadata.openclaw` runtime requirements in `SKILL.md` for ClawHub publishing.
- A root build script at `scripts/build_clawhub_release.py` that assembles a ClawHub-ready artifact in `dist/clawhub/causal-abel`.

### Changed

- Reworked the main skill instructions to fit ClawHub and OpenClaw installs without assuming a GitHub-first self-update flow.
- Simplified `agents/openai.yaml` so the default prompt focuses on authorization and causal routing.
- Updated probe examples to use bundled relative paths such as `scripts/cap_probe.py`, which work cleanly after installation.
- Reframed update guidance so published installs prefer `clawhub update causal-abel` instead of `npx skills` refresh commands.
- Restored the source `causal-abel` skill as the full legacy-aware variant with first-use soft update guidance.
- Switched the release model from runtime environment detection to build-time packaging, so ClawHub can receive a stripped variant with no automatic update mechanism.
- Kept `metadata.openclaw` in the source skill so ClawHub requirements remain explicit even though the published artifact is generated.

## [1.0.0] - 2026-03-23

### Added

- Explicit skill version metadata in `SKILL.md`.
- A repository `CHANGELOG.md` for release summaries.
- A bundled `scripts/check_skill_update.py` helper that runs `npx skills check`, reads the remote `SKILL.md` and `CHANGELOG.md`, and returns a machine-readable update summary.

### Changed

- The skill instructions now treat the first-use update check as a soft prerequisite before live Abel API usage.
- The update flow now checks only the installed `causal-abel` skill instead of scanning every tracked skill.
- The refresh guidance now uses a single-skill `npx skills add ... --skill causal-abel` command instead of `npx skills update`.
- The user-facing prompt is now intentionally warmer and ends with a short `Y/N` choice.

### Notes

- Update-check failures are intentionally non-blocking so the normal authorization and probing flow can continue.
