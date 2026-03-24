# Inversion Flow

Use this file to invert from user intent to the smallest useful `causal-abel` workflow.

The goal is to start from the answer the user actually wants, then work backward into graph representation, CAP surface selection, and report structure.

## Core Principle

Do not start from verbs.

Start from:

1. what the user is trying to understand, decide, or verify
2. what shape of answer would satisfy that intent
3. how that intent can be represented in the graph
4. which minimum set of capabilities is sufficient

## Inversion Steps

### 1. Identify User Intent

Classify the user's real objective before choosing nodes or verbs.

Common intent types:

- `driver_explanation`: why something moved or what is driving it
- `local_context`: what matters around a node
- `reachability_check`: whether one node can influence another
- `intervention_effect`: what changes if a node is perturbed
- `counterfactual_read`: what would have looked different under another setting
- `capability_audit`: what the server supports and where the boundaries are
- `decision_proxy_read`: how to think about an off-graph life, business, or macro decision through market proxies

Prompt for the agent:

```text
What result is the user actually trying to obtain: explanation, reachability, effect estimate, comparison, or capability audit?
```

### 2. Define The Desired Answer Shape

Decide what a satisfying answer should look like before choosing the graph path.

Examples:

- `driver_explanation` -> immediate drivers plus why they matter
- `local_context` -> nearby relevant nodes plus their roles
- `reachability_check` -> whether a path exists, through what intermediaries, and whether it looks direct or indirect
- `intervention_effect` -> expected change after perturbation plus timing if needed
- `counterfactual_read` -> preview of what would differ under the alternate scenario
- `capability_audit` -> capability groups, extension boundaries, and semantic caveats
- `decision_proxy_read` -> proxy dimensions, compared signals, and what they imply for the original decision

Prompt for the agent:

```text
If this goes well, what kind of answer should the user walk away with?
```

### 3. Map The Question Into Graph Form

Choose the graph representation only after the desired answer shape is clear.

Required outputs:

- `question_focus`
- `mapping_type`: `direct_graph` or `proxy_routed`
- `core_nodes`
- `supporting_nodes`
- `mapping_reason`

Routing rule:

- If the graph already contains direct nodes for the topic, use `direct_graph`.
- If the graph does not contain direct nodes for the topic, use `proxy_routed` and map the question through decision dimensions and proxy roles.

Prompt for the agent:

```text
Which nodes best represent the user's question, and is this a direct graph read or a proxy-routed read?
```

Node grounding rule:

- Finish proxy-routed mapping in two stages: proxy role -> ticker candidate -> executable Abel node id.
- Treat bare tickers as query shapes that still need normalization before a live CAP call.
- Default a bare ticker to `<ticker>_close`; switch to `<ticker>_volume` only when the user is clearly asking about volume or trading activity.
- Do not treat a company name or free-form proxy phrase as an executable node.

### 4. Select The Minimum Sufficient Capability Set

Pick the smallest set of CAP surfaces that can answer the user's intent.

Default mapping:

| Intent | Minimum useful surface |
|--------|------------------------|
| `driver_explanation` | `neighbors`, `traverse-parents`, `markov-blanket` |
| `local_context` | `neighbors`, `markov-blanket`, `traverse-children` |
| `reachability_check` | `paths`, optionally `validate-connectivity` |
| `intervention_effect` | `intervene.do`, optionally `intervene-time-lag` |
| `counterfactual_read` | `counterfactual-preview` |
| `capability_audit` | `capabilities` |
| `decision_proxy_read` | start with structural verbs, then move to effect surfaces only if needed |
| `convergence_read` | multi-anchor structural reads first, then targeted search or effect surfaces only if a specific gap remains |

Selection rules:

- Start with structural surfaces before effect surfaces when possible.
- Do not run all verbs just because they exist.
- Use richer Abel extensions only when CAP core is insufficient for the user's actual question.
- Prefer one clean causal chain over many weak exploratory calls.
- Choose exactly one primary workflow for the current turn: `driver_explanation`, `reachability_check`, `intervention_effect`, `counterfactual_read`, or `capability_audit`.
- Avoid overlapping local-structure probes by default. For example, start with `traverse.parents` or `graph.neighbors(scope=parents)`, then add `graph.markov_blanket` only when a specific structural question remains.
- Treat `graph.paths` as a narrowed structural test, not a bulk discovery substitute.
- Do not escalate to `intervene.do` until the treatment-outcome structural question is already clear enough to justify an effect query.
- In proxy-routed work, only escalate to search after naming the edge or proxy dimension being explained.
- In broad proxy-routed work, prefer convergence over deeper single-anchor wandering.
- Keep each search hop question-driven: if you cannot state the remaining uncertainty, stop.

Prompt for the agent:

```text
What is the smallest set of verbs or capability layers that can answer this user's intent honestly?
```

### 5. Organize The Result By Meaning

Once results exist, organize them in the order the user can understand.

Use this output order:

1. original question
2. question-to-node mapping
3. verb findings
4. integrated interpretation
5. caveats

Within each verb section, always separate:

- `result`: what the graph returned
- `meaning`: what that finding means for the original question

This should align with `../assets/report-template.md`.

When proxy-routed search is involved, preserve provenance inside each section:

- `graph_fact`: what the CAP surface actually showed
- `searched_mechanism`: what external evidence explains about that structure
- `inference`: what you conclude by combining them

### 6. Offer The Next Best Causal Question

After answering the current question, propose the most useful next step based on what is still unresolved.

Examples:

- if local drivers are clear but transmission is not, move to `paths`
- if a path exists but effect strength is unclear, move to `intervene.do`
- if intervention answers direction but timing matters, move to `intervene-time-lag`
- if proxy routing looks weak, ask whether a different proxy dimension is more honest
- if several anchors keep pointing to the same hub, move to convergence validation instead of adding more random anchors
- if the public surface is exhausted, say so instead of inventing a deeper answer

Prompt for the agent:

```text
What is the single highest-value follow-up question now that this result is known?
```

## Intent Matrix

| Intent | Desired answer shape | Mapping type | Preferred surface | Caveat focus |
|--------|----------------------|--------------|-------------------|--------------|
| `driver_explanation` | why this node moves | direct first | local structure | structural evidence is not full causal proof |
| `local_context` | what matters around this node | direct first | neighbors / blanket | nearby relevance does not imply dominant cause |
| `reachability_check` | can A reach B | direct first | paths | path existence does not by itself quantify effect |
| `intervention_effect` | what changes if X changes | direct first | intervene | intervention semantics versus observation |
| `counterfactual_read` | what would differ under another setting | direct first | counterfactual preview | preview-only and approximate semantics |
| `capability_audit` | what the server can expose | direct | capabilities and layers | CAP core versus Abel extension boundary |
| `decision_proxy_read` | what market proxies suggest about a real-world choice | proxy-routed | structural first, then effect if needed | proxy signal is not direct modeling of the real subject |
| `convergence_read` | what repeated anchors jointly imply about a broad question | proxy-routed | multi-anchor structure first, then targeted validation | repeated structure is stronger than a single noisy anchor |

## Output Contract

When this inversion flow is used, the final answer should contain these layers even if it is brief:

- `intent_read`: what the user is actually asking for
- `graph_mapping`: how the question became graph nodes
- `surface_used`: which minimum capability set was chosen
- `finding`: what the graph showed
- `meaning`: what that finding means for the user's original question
- `caveat`: what should not be over-interpreted
- `provenance`: which parts came from graph structure, which from search evidence, and which remain inference

## Failure Modes To Avoid

- starting from a favorite verb instead of the user's intent
- dumping raw node names without explaining why they represent the question
- running many surfaces with no clear contribution to the answer
- confusing observational prediction with intervention effect
- treating proxy routing as direct modeling of a person, choice, or value system
- stopping at "the graph does not contain that topic" when an honest proxy route exists
- running search before an edge or proxy dimension has been grounded
- narrating convergence without checking whether repeated anchors actually support the same mechanism

## See Also

- `../SKILL.md` for the short agent-facing framework
- `question-routing.md` for detailed direct versus proxy routing logic
- `search-loop.md` for edge-anchored search and feedback discipline
- `layered-routing.md` for layered proxy anchor selection
- `capability-layers.md` for choosing how deep to explain the stack
- `../assets/report-template.md` for structuring findings around question, nodes, verb results, and meaning
