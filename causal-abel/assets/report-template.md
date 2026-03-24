# Causal Abel Report Template

Use this template to turn raw skill output into a stable report that explains how the user's original question relates to graph nodes, what each verb found, and what those findings mean.

Do not center the report on commands, payloads, script flags, or call mechanics unless the user explicitly asks for reproducible invocation details.

## Report Goal

Every report should answer these things in order:

1. What is the user's real causal question?
2. Which graph nodes are being used to represent that question?
3. What did the graph verbs return?
4. What did graph-grounded web evidence clarify about the current mechanism?
5. What did the red-team pass fail to disprove?
6. What pressure test or next-step probe would most change the answer?
7. What do those combined findings mean for the original question?

## Output Rules

- For ordinary user-facing answers, lead with a short verdict-first answer before the fuller report body.
- For high-stakes or non-trivial `proxy_routed` and multi-step analyses, the full report is the default deliverable.
- Low-stakes casual comparisons may stay shorter, but they should still preserve graph-grounded reasoning and any critical web-grounded mechanism.
- Only collapse to a short answer when the user explicitly asks for brevity.
- After the first-screen answer, prefer a compact card with:
  - `Signal`
  - `Causal link`
  - `Sharp`
  - `Certain`
  - `Decision tip`
- Start from the original question, not from raw graph output.
- Include a short `intent_read` before graph mechanics when the user's request could be interpreted in more than one way.
- Explain the relationship between the question and the chosen nodes before interpreting verb results.
- Name the `surface_used` as the minimum sufficient capability set rather than as an exhaustive log of everything available.
- Separate graph findings from web-grounded evidence. Do not blur them into one unsupported narrative.
- For each verb used, separate `result` from `meaning`.
- When search is used, separate `graph_fact`, `searched_mechanism`, and `inference`.
- Prefer semantic names over raw node IDs when a node is acting as a proxy or bridge.
- If the question is proxy-routed, say clearly that the graph is reading market proxies rather than directly modeling the real-world subject.
- If a financial transmission node or small-cap bridge was considered but then downgraded, say so briefly in the report instead of silently dropping it.
- Include a short challenge section for non-trivial analyses: untested assumption, counter-evidence, weakest link.
- When intervention adds value, frame it as a pressure test or next-step probe, not as a detached method demo.
- Keep command, route, OAuth, and script details out of the main report unless the user asks for them.
- Do not dump raw JSON when a short natural-language rendering will preserve the meaning.

Even in compact form, the report should preserve these contract fields:

- `intent_read`
- `graph_mapping`
- `surface_used`
- `finding`
- `web_evidence`
- `challenge`
- `meaning`
- `caveat`
- `provenance`

## Stable Report Structure

### 1. Original Question

State the user's real cause-effect question in one or two lines.

Optional but recommended field:

- `intent_read`: what the user is actually trying to obtain from this analysis

Prompt for the generator:

```text
What is the user actually trying to understand, decide, or explain?
```

### 2. Question To Graph Mapping

Explain how the original question maps onto graph nodes.

Required fields:

- `question_focus`: the real-world issue the user cares about
- `core_nodes`: the main graph nodes used for analysis
- `supporting_nodes`: bridge or comparison nodes if needed
- `mapping_type`: `direct_graph` or `proxy_routed`
- `mapping_reason`: why these nodes are relevant to the question

Compact contract name:

- `graph_mapping`: a concise rendering of the mapping fields above

Generator guidance:

- If the graph contains direct nodes for the topic, say that this is a direct graph read.
- If the graph does not contain direct nodes for the topic, explain which proxy dimensions are being used and why.
- When proxy routing is used, describe nodes by economic role first and ticker second.

### 3. Verb Findings

Group findings by verb. Each verb section should contain two parts only:

- `result`: what the graph returned
- `meaning`: what that result contributes to the original question

When search or external evidence is part of the same section, add:

- `graph_fact`: the structural fact from CAP
- `searched_mechanism`: the mechanism evidence gathered outside the graph
- `inference`: the conclusion that combines both without blurring them

Before the verb sections, add:

- `surface_used`: the minimum sufficient capability set selected for the user's intent
- `finding`: a compact statement of the most decision-relevant graph result when a short answer is needed
- `provenance`: a compact note on which parts are graph-backed, search-backed, or still inferential

Recommended verb sections:

#### `neighbors` / `traverse-parents` / `traverse-children`

- `result`: which nearby drivers, children, or local influences appear around the node
- `meaning`: what this says about immediate pressure, exposure, or influence direction

#### `markov_blanket` / `abel-markov-blanket`

- `result`: which surrounding nodes best localize the node's informational neighborhood
- `meaning`: what this says about the node's most relevant local causal context

#### `paths` / `validate-connectivity`

- `result`: whether a connection exists, through which intermediaries, and whether it looks direct or indirect
- `meaning`: what this says about transmission, mediation, or whether the proposed relationship is structurally plausible

#### `observe.predict`

- `result`: what the observational surface currently predicts
- `meaning`: what the current regime suggests, without overstating it as intervention effect

#### `intervene.do` / `intervene-time-lag`

- `result`: what changes when the treatment node is stressed, and how that stress rolls out if time-lag is used
- `meaning`: what this says about how robust or fragile the current verdict is

#### `counterfactual-preview`

- `result`: what the preview surface says would differ under the alternate setting
- `meaning`: what this suggests as a what-if or next-step read, while preserving preview-only caveats

### 4. Web-Grounded Evidence

Summarize the focused web evidence gathered after the graph shortlist was clear.

Required fields:

- `search_target`: the edge, node, sector, or proxy dimension being clarified
- `search_result`: the most relevant current fact or mechanism found
- `why_it_matters`: how that evidence changes, confirms, or constrains the graph reading

Guidance:

- Use ordinary web or news search for this phase, not image search.
- Keep each search target narrow and graph-grounded.
- If a searched financial transmission node turned out to be low-signal, say that and explain the cleaner anchor you switched to.
- Do not inflate weak web evidence into a firm mechanism claim.

Compact contract name:

- `web_evidence`: the single most decision-relevant external grounding point

### 5. Challenges

Run a brief red-team pass against the working conclusion.

Required fields:

- `untested_assumption`: the key assumption not directly established by graph or web evidence
- `counter_evidence`: the strongest alternative explanation or contrary signal found
- `weakest_link`: the graph edge, bridge node, or proxy mapping most likely to fail

Guidance:

- Keep this evidence-based and brief.
- For non-trivial proxy-routed decisions, do one falsification-oriented search when search is available.
- If the challenge pass materially weakens the thesis, lower certainty or make the verdict conditional.
- Do not write generic balance language. Name the specific failure mode.

Compact contract name:

- `challenge`: the single most important reason the conclusion could be wrong

### 6. Pressure Test

Use this section only when it adds decision value.

Required fields:

- `stress_target`: the node, bridge, or proxy dimension being stressed
- `stress_outcome`: the node, path, or proxy comparison most affected
- `stress_result`: whether the verdict held, weakened, or flipped

Guidance:

- Prefer one strong pressure test over multiple weak ones.
- Prefer a real graph-lever stress test over a user workflow suggestion.
- If a live intervention is not worth running, name the cleanest fallback graph lever instead of giving a generic execution plan.
- Keep this short and decision-oriented.

### 7. Integrated Interpretation

Synthesize the verb findings back into the original question.

Prompt for the generator:

```text
Given the node mapping, graph findings, web-grounded evidence, and challenge pass, what is the best plain-language answer to the user's original question?
```

Guidance:

- Do not merely repeat the verb outputs.
- Explain how the structural and effect findings combine.
- Prioritize the user's decision or explanation need over graph-internal jargon.
- If a search loop was used, say which part of the interpretation comes from graph structure versus mechanism evidence.

### 8. Boundaries And Caveats

State the limits that materially change interpretation.

Always check for these caveats:

- observational result versus intervention result
- direct graph signal versus proxy-routed signal
- direct path versus indirect path
- preview-only or approximate surface
- missing graph support or weak structural evidence
- searched mechanism that is plausible but not yet structurally re-grounded
- repeated anchor pattern that may still reflect a bridge rather than a true hub

Prompt for the generator:

```text
What should the user not over-interpret from these graph findings?
```

Compact contract name:

- `caveat`: the highest-priority limit that changes interpretation

## Preferred Output Shape

Use this markdown skeleton when presenting the report:

```md
# Causal Abel Report

## Original Question
[Restate the user's actual causal question.]

- Intent read:

## Question To Graph Mapping
- Question focus:
- Core nodes:
- Supporting nodes:
- Mapping type:
- Why these nodes fit:

## Surface Used
- Minimum sufficient capability set:

## Verb Findings
### [Verb name]
- Result:
- Meaning:

### [Verb name]
- Result:
- Meaning:

## Web-Grounded Evidence
- Search target:
- Search result:
- Why it matters:

## Challenges
- Untested assumption:
- Counter-evidence:
- Weakest link:

## Pressure Test
- Stress target:
- Stress outcome:
- Stress result:

## Integrated Interpretation
[Tie the node mapping, graph findings, web evidence, and challenge pass back to the original question.]

## Insight Card
- Signal:
- Causal link:
- Sharp:
- Certain:
- Decision tip:

## Compact Contract
- Graph mapping:
- Finding:
- Web evidence:
- Challenge:
- Meaning:
- Caveat:
- Provenance:

## Boundaries And Caveats
- [Limit 1]
- [Limit 2]
- [Limit 3]

## Trace
- Routing:
- Searches used:
- Key nodes:
```

## Quality Check

Before finalizing a report, verify that:

- the original question appears before any graph mechanics
- the user's intent is explicit when ambiguity would otherwise change the result
- each chosen node is explained, not just listed
- the surface used is the smallest honest capability set, not an exhaustive dump
- each verb section has both a result and a meaning
- the web-grounded evidence section explains at least one current mechanism when the task is proxy-routed or current-state dependent
- the challenge section names a concrete way the answer could be wrong instead of generic hedging
- the pressure-test section either sharpens the verdict or gives useful next probes instead of acting like a method dump
- the integrated interpretation answers the user's question directly
- caveats are strong enough to prevent overclaiming
- provenance is clear whenever search evidence or proxy reasoning materially shapes the answer
