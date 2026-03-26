# Changelog

All notable changes to `causal-abel` will be documented in this file.

This project follows a repo-level release log so agents can summarize user-visible changes across GitHub and ClawHub-facing revisions.

## Unreleased

### Changed

- Trimmed `causal-abel/agents/openai.yaml` back toward trigger and routing guidance so detailed execution rules stay in `SKILL.md` and route references.
- Tightened the source `causal-abel` prompt so the core guidance is shorter and higher-leverage, with graph-first rules phrased as a small set of primary constraints.
- Refined broad ticker-driver guidance so agents anchor to executable tickers, run Abel first, and interpret surprising parents as transmission channels before leaving the graph.
- Tightened `causal-abel` prompt priority so direct graph answers now preserve graph facts first instead of replacing them with web-searched narratives.
- Reframed Abel graph outputs as high-value PCMCI-style market-data evidence and added guidance for handling surprising drivers as serious transmission signals.
- Narrowed direct-graph web grounding so driver lists, parent membership checks, and path facts are usually answered from graph output without forced search.
- Updated the report and planner guidance so graph fact, interpretation, and optional web validation stay visibly separate when the graph output is unintuitive.
- Reframed `causal-abel` so the default output shape is a compact report rather than a short verdict-only answer.
- Updated the direct and proxy routes so executable anchors are observed first, preferring `extensions.abel.observe_predict_resolved_time` before deeper structural traversal.
- Changed the planner and probe guidance so non-trivial comparative reads now default to one compact `intervene.do` pressure test after the mechanism is coherent.
- Updated the report template so pressure-test coverage is expected by default in longer comparative analyses.

## [1.0.2] - 2026-03-24

### Added

- `references/search-loop.md` for edge-anchored search discipline in proxy-routed reads.
- `references/layered-routing.md` for selecting layered proxy anchors and running convergence reads on broad questions.

### Changed

- Expanded the source and committed ClawHub skill instructions with `convergence_read`, stronger proxy/search guardrails, and clearer separation between graph facts, searched mechanisms, and inference.
- Updated `question-routing.md`, `inversion-flow.md`, and `probe-usage.md` to support layered proxy routing, search-loop escalation, and convergence-first analysis for broad comparisons.
- Updated `cap_probe.py` so `intervene-do` performs a required `graph.paths` gate before calling `intervene.do`, and added `--max-description-chars` for trimming verbose text fields in responses.
- Refined first-use update wording so the skill prompts on version differences without depending on an in-prompt changelog summary.
- Restored the repository changelog as the source of release notes for update and publish flows, while keeping the generated ClawHub artifact free of source-only update metadata.
- Bumped the source skill and committed ClawHub artifact to version `1.0.2`.

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
