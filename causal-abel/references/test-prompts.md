# Causal Abel Skill Test Prompts

Use these prompts to verify that the skill behaves like an Abel-style causal router over the CAP wrapper: it should use the bundled `cap_probe.py` script, distinguish direct graph questions from proxy-routed human questions, and stay honest about what is direct graph signal versus proxy inference.

## Authorization Precondition

Unless a valid Abel API key is already present in session state or `.env.skills`, every live Abel prompt below should first trigger the authorization behavior in Prompt 0 before any CAP probing or business API call.

## Prompt 0: Install And Authorize

```text
Install $causal-abel and connect it to Abel automatically if authorization is required.
```

Expected shape:
- Start with the agent authorize endpoint, not a manual email request
- Return `data.authUrl` as the user-facing link, not the `/authorize/agent` API URL
- Store `data.resultUrl` or `data.pollToken` and poll immediately
- Do not ask the user for the Google OAuth code or a "done" reply before polling
- Continue the skill setup once the result becomes `authorized`
- Persist the resulting API key so later prompts can reuse it without reopening the auth flow

## Prompt 1: Live Capability Layering

```text
Use $causal-abel to inspect the live Abel CAP server at https://cap.abel.ai and tell me what it supports, grouped by public CAP, Abel extensions, and any semantic caveats I should know before using them.
```

Expected shape:
- Use the bundled probe script against the live server first
- Public CAP verbs first
- Then `extensions.abel.*`
- Call out preview/proxy semantics when relevant

## Prompt 2: Direct Graph Question

```text
Use $causal-abel to tell me what is driving `NVDA_close` on https://cap.abel.ai.
```

Expected shape:
- Route to direct CAP mode
- Start with structure calls such as neighbors, Markov blanket, or traverse-parents
- Explain the result in plain language before implementation details

## Prompt 3: Off-Graph Human Question

```text
Use $causal-abel to help me think about whether a child should pursue music or writing in the AI era, using https://cap.abel.ai if it can help.
```

Expected shape:
- Do not stop at "the graph only has equities and crypto"
- Switch into proxy-routing mode
- Name the decision dimensions and proxy tickers used
- Clearly state that the answer is a proxy-based causal read, not a direct personal-talent model
- Avoid dated phrasing like "2026-03-20 live Abel CAP"
- Use semantic descriptions for proxies in the narrative, not just raw node IDs

## Prompt 4: Path And Mechanism

```text
Use $causal-abel to run `graph.paths` for `NVDA_close` and `AMD_close`, then explain what mechanism that path might represent.
```

Expected shape:
- Execute `graph.paths` first
- Explain the graph structure before any narrative leap
- If search is used, tie it to an explicit edge or proxy dimension
- Prefer human-readable node meanings over raw node IDs in the conclusion unless exact IDs were requested

## Prompt 5: Capability Or Extension Audit

```text
Use $causal-abel to check whether https://cap.abel.ai already exposes a connectivity-style capability. If it does not, tell me whether it should live in CAP core or under extensions.abel.*.
```

Expected shape:
- Check the live capability card first through the bundled probe script
- Distinguish protocol-generic capability from Abel-only capability
- Prefer `extensions.abel.*` when semantics are Abel-specific

## Prompt 6: Command-Oriented User

```text
Use $causal-abel with the default server and give me the exact `cap_probe.py` commands I can reuse for capabilities, neighbors, paths, intervene-do, and counterfactual preview.
```

Expected shape:
- Use `https://cap.abel.ai` as the default CAP target
- Return commands aligned with `skill/causal-abel/scripts/cap_probe.py`
- Prefer copy-pastable command blocks over prose

## Prompt 7: Inversion Before Verbs

```text
Use $causal-abel to help me understand whether AI pressure is more about immediate driver exposure or longer-path structural transmission for `ADBE_close`.
```

Expected shape:
- Infer the user's intent before choosing verbs
- State whether the answer target is local-driver explanation, reachability, or a combination
- Pick the smallest useful capability set instead of running every available surface
- Explain why the selected nodes and surfaces fit the user's real question

## Prompt 8: Inversion For Proxy Decision Read

```text
Use $causal-abel to help me think about whether an MBA is still worth it in an AI-heavy labor market, and make the answer about what I should learn from the graph rather than about tickers.
```

Expected shape:
- Identify the user intent as a decision-oriented proxy read before listing proxies
- Define the desired answer shape in human terms, not tool terms
- Map the question to proxy dimensions and nodes only after stating the decision frame
- Keep the conclusion centered on meaning for the decision, not on ticker enumeration
- Explicitly mark the result as proxy-routed and market-signal-based

## Prompt 9: Output Contract Check

```text
Use $causal-abel to explain whether `NVDA_close` can influence `AMD_close`, and organize the answer so I can see the user intent, graph mapping, surface used, main finding, meaning, and caveat.
```

Expected shape:
- Include an intent read
- Explain the graph mapping from the question to the chosen nodes
- Name the minimum sufficient surface used
- Separate the main finding from its meaning
- Include at least one caveat that prevents over-interpretation

## See Also

- `../SKILL.md` for the short agent-facing framework
- `question-routing.md` for the detailed routing and narration rules these prompts are checking
- `probe-usage.md` for the command patterns referenced here
