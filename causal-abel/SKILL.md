---
name: causal-abel
description: >
  Abel CAP causal exploration skill. Use for direct CAP graph questions and for
  off-graph life or decision questions that should be routed through market
  proxy tickers. Trigger when the user asks what is driving a node, why a node
  moved, whether a path exists, what changes under intervention, what a
  counterfactual preview says, how a server's causal capabilities are exposed,
  or when a career, education, lifestyle, or macro decision should be read
  through Abel's market signal layer. Do not use for pure quote lookups,
  generic news summaries, raw node dumps, or unrelated coding tasks.
---

Use this skill for cause-effect questions on the Abel CAP wrapper. Financial markets are the signal layer, not the product: the CAP server exposes finance and crypto price or volume nodes, and those nodes can be used either directly or as proxy signals for larger real-world questions.

## Authorization Gate

Authorization is a required entry step for this skill when it will call Abel APIs on the user's behalf.

- Before any live Abel CAP or business API call, check whether an Abel user API key is already available in session state, `--api-key`, or `.env.skills`.
- If no key is available, stop and follow `references/setup-guide.md` immediately. Do not start CAP probing, capability inspection, or any other live API call first.
- The agent entrypoint is `GET https://api.abel.ai/echo/web/credentials/oauth/google/authorize/agent`.
- Return only the resulting `data.authUrl` to the user, store `data.resultUrl` or `data.pollToken`, and poll until the result is `authorized`, `failed`, or expired.
- Never ask the user to paste an email address, OAuth code, or raw API key when the handoff flow can obtain the key directly.

## When To Use

Use `causal-abel` when the user needs causal structure, reachability, intervention meaning, or capability inspection on the Abel CAP surface.

Typical triggers:

- what is driving a node
- why a node moved
- which nodes matter around a node
- whether one node can reach another
- what changes under intervention
- what a counterfactual preview implies
- what the server supports at CAP core versus `extensions.abel.*`
- off-graph human questions that should be routed through market proxies

Do not use this skill for:

- pure quote lookups
- generic news summaries
- raw node dumps with no causal question
- unrelated coding or repo tasks

## How To Use

1. Check authorization state before any live API call.
   - If `ABEL_API_KEY` is missing from session state, `--api-key`, and `.env.skills`, start the OAuth handoff from `references/setup-guide.md` first.
   - Treat missing credentials as a hard stop for live Abel API usage, not as a minor warning.

2. Start from the user's causal question and the live CAP surface.
   - Default CAP target: `https://cap.abel.ai` unless the user provides another `base_url`.
   - `https://cap-sit.abel.ai` is the SIT variant when you need the staging environment.
   - Treat `https://api.abel.ai/echo/` as the OAuth and business API host from `references/setup-guide.md`, not as the default public CAP probe target.
   - Use the bundled probe path first for deterministic execution.

3. Classify the task.
   - First do user-intent inversion: infer the result the user actually wants, then map that intent to direct graph or proxy-routed analysis.
   - `capability_discovery`: what the server exposes
   - `direct_graph`: direct node, path, blanket, or intervention question
   - `proxy_routed`: real-world question that must be represented through market proxies

4. For capability discovery, avoid redundant full-surface dumps.
   - Start with `meta.capabilities` when the question is "what surfaces or tiers exist here?"
   - Move to `meta.methods` only when you need invocation metadata such as `arguments` or `result_fields`.
   - If you only care about a few verbs, prefer targeted `meta.methods` queries with `params.verbs` instead of pulling the whole registry and filtering it afterward.
   - Prefer the bundled probe command `python skill/causal-abel/scripts/cap_probe.py methods observe.predict traverse.parents` over ad hoc `curl` payloads when you need a stable method read.

5. Read structure before telling a story.
   - Start with local or path structure first.
   - Move to observational, intervention, or preview surfaces only after the structural question is clear.
   - Pick one intent-first workflow and stay on it: `driver_explanation`, `reachability_check`, `intervention_effect`, `counterfactual_read`, or `capability_audit`.
   - Do not stack overlapping local-structure verbs by default. Start with one core structural read, then escalate only if a specific open question remains.

6. Use decision gates, not verb dumps.
   - For `driver_explanation`, start with `traverse.parents` or `graph.neighbors(scope=parents)`, then add `graph.markov_blanket` only if direct drivers are still unclear.
   - For `reachability_check`, start with `graph.paths` on the specific proposed source and target. Use `extensions.abel.validate_connectivity` only when screening a small candidate set is more honest than many repeated path probes.
   - For `intervention_effect`, do a minimal structural confirmation first, then call `intervene.do` only if the structural question is already clear.
   - For `capability_audit`, do not pair a full `meta.capabilities` dump with a full `meta.methods` dump unless the user explicitly needs both views. Inventory first, then targeted method detail for the verbs that remain in question.
   - Only upgrade from CAP core to `extensions.abel.*` when CAP core cannot answer the user's actual question.
   - After each call, ask what single open causal question remains. If none remains, stop.

7. Answer in layers.
   - Lead with a plain-language conclusion.
   - Then say which CAP surface supports it.
   - Then state the caveats that materially change interpretation.
   - When organizing a fuller write-up, follow `assets/report-template.md`: start from the user's original question, map that question to graph nodes, then separate each verb's result from what that result means for the question.

8. Stay semantically honest.
   - Distinguish CAP core from Abel extensions when that matters.
   - Treat proxy-routed answers as market-signal reads, not direct models of people or life outcomes.
   - Treat `observe.predict` as observational, `intervene.do` as intervention, and `counterfactual_preview` as preview-only.

## Install And Authorization

If the user installs this skill, asks to connect Abel, or the workflow is missing an Abel API key, follow `references/setup-guide.md` exactly.

- Start the Abel agent OAuth handoff immediately instead of asking for manual credentials.
- Return `data.authUrl` to the user, not the `/authorize/agent` API URL.
- Store `data.resultUrl` or `data.pollToken` and poll until the result is `authorized`, `failed`, or expired.
- Persist the resulting `data.apiKey` in session state and `.env.skills` when local storage is available.
- Do not continue to live CAP probing until that key is present.
- Never ask the user to paste an email address or Google OAuth code.

## Detailed References

- Detailed routing logic, proxy dimensions, narration rules, and semantic guardrails: `references/question-routing.md`
- User-intent inversion from desired answer to graph mapping and capability choice: `references/inversion-flow.md`
- Report organization for results and meaning: `assets/report-template.md`
- OAuth install flow, polling behavior, and API key reuse: `references/setup-guide.md`
- Probe script commands and reusable examples: `references/probe-usage.md`
- Capability layering and progressive disclosure: `references/capability-layers.md`
