# Causal Abel Report Template

Use this template to turn raw skill output into a stable report that explains how the user's original question relates to graph nodes, what each verb found, and what those findings mean.

Do not center the report on commands, payloads, script flags, or call mechanics unless the user explicitly asks for reproducible invocation details.

## Report Goal

Every report should answer four things in order:

1. What is the user's real causal question?
2. Which graph nodes are being used to represent that question?
3. What did the graph verbs return?
4. What do those verb results mean for the original question?

## Output Rules

- Start from the original question, not from raw graph output.
- Explain the relationship between the question and the chosen nodes before interpreting verb results.
- For each verb used, separate `result` from `meaning`.
- Prefer semantic names over raw node IDs when a node is acting as a proxy or bridge.
- If the question is proxy-routed, say clearly that the graph is reading market proxies rather than directly modeling the real-world subject.
- Keep command, route, OAuth, and script details out of the main report unless the user asks for them.
- Do not dump raw JSON when a short natural-language rendering will preserve the meaning.

## Stable Report Structure

### 1. Original Question

State the user's real cause-effect question in one or two lines.

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

Generator guidance:

- If the graph contains direct nodes for the topic, say that this is a direct graph read.
- If the graph does not contain direct nodes for the topic, explain which proxy dimensions are being used and why.
- When proxy routing is used, describe nodes by economic role first and ticker second.

### 3. Verb Findings

Group findings by verb. Each verb section should contain two parts only:

- `result`: what the graph returned
- `meaning`: what that result contributes to the original question

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

- `result`: what changes when the treatment node is perturbed, and how that effect rolls out if time-lag is used
- `meaning`: what this says about directional causal influence and timing

#### `counterfactual-preview`

- `result`: what the preview surface says would differ under the alternate setting
- `meaning`: what this suggests as a what-if read, while preserving preview-only caveats

### 4. Integrated Interpretation

Synthesize the verb findings back into the original question.

Prompt for the generator:

```text
Given the node mapping and verb findings, what is the best plain-language answer to the user's original question?
```

Guidance:

- Do not merely repeat the verb outputs.
- Explain how the structural and effect findings combine.
- Prioritize the user's decision or explanation need over graph-internal jargon.

### 5. Boundaries And Caveats

State the limits that materially change interpretation.

Always check for these caveats:

- observational result versus intervention result
- direct graph signal versus proxy-routed signal
- direct path versus indirect path
- preview-only or approximate surface
- missing graph support or weak structural evidence

Prompt for the generator:

```text
What should the user not over-interpret from these graph findings?
```

## Preferred Output Shape

Use this markdown skeleton when presenting the report:

```md
# Causal Abel Report

## Original Question
[Restate the user's actual causal question.]

## Question To Graph Mapping
- Question focus:
- Core nodes:
- Supporting nodes:
- Mapping type:
- Why these nodes fit:

## Verb Findings
### [Verb name]
- Result:
- Meaning:

### [Verb name]
- Result:
- Meaning:

## Integrated Interpretation
[Tie the node mapping and verb findings back to the original question.]

## Boundaries And Caveats
- [Limit 1]
- [Limit 2]
- [Limit 3]
```

## Quality Check

Before finalizing a report, verify that:

- the original question appears before any graph mechanics
- each chosen node is explained, not just listed
- each verb section has both a result and a meaning
- the integrated interpretation answers the user's question directly
- caveats are strong enough to prevent overclaiming
