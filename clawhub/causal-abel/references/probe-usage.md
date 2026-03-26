# Probe Usage

Use this file only after `SKILL.md` and the chosen route file have already fixed:

- the mode
- the anchor set
- whether web grounding is needed

This file is a command manual, not the main workflow.

## Authorization First

- Do not run the bundled probe until an Abel user API key is available in session state, `--api-key`, or `<skill-root>/.env.skill`.
- If a key is already available, skip auth docs and go straight to the chosen route.
- If the key is missing, start the OAuth handoff from `setup-guide.md` first.
- By default, use `<skill-root>/.env.skill` as the local auth file.

## Bundled Script

Prefer `scripts/cap_probe.py` over ad hoc payload construction. Default to the generic `verb` path for extension surfaces, then use the dedicated graph helpers for local structure.

## Common Direct Calls

Run these from the skill root:

```bash
BASE_URL="https://cap.abel.ai/api"

python scripts/cap_probe.py --base-url "$BASE_URL" capabilities
python scripts/cap_probe.py normalize-node NVDA
python scripts/cap_probe.py --base-url "$BASE_URL" methods extensions.abel.query_node extensions.abel.node_description
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.observe_predict_resolved_time --params-json '{"target_node":"NVDA.price"}'
python scripts/cap_probe.py --base-url "$BASE_URL" neighbors NVDA.price --scope children --max-neighbors 5
python scripts/cap_probe.py --base-url "$BASE_URL" paths NVDA.price AMD.price --max-paths 3
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.intervene_time_lag --params-json '{"treatment_node":"NVDA.price","treatment_value":0.05,"outcome_node":"AMD.price","horizon_steps":3,"model":"linear"}'
```

For `extensions.abel.intervene_time_lag`, first confirm the treatment/outcome pair is structurally meaningful with `graph.paths`. The request shape above is the template; not every node pair returns a propagated effect.

## Usage Rules

- `normalize-node` is the safest first step when a prompt gives a bare ticker.
- Manual mapping is still the first pass for obvious company and proxy anchors.
- Use `extensions.abel.query_node` for fuzzy or broad phrases.
- Use `extensions.abel.node_description` on the final shortlist before writing the answer.
- For executable anchors that materially bear on the question, run one observational read before deeper structure.
- Search the company or industry labels from `node_description`, not raw node ids.
- Check `meta.methods` before assuming a local wrapper is current.
- Use `extensions.abel.observe_predict_resolved_time` as the default observational surface.
- Use `extensions.abel.intervene_time_lag` as the default pressure-test surface.
- Treat pressure tests as late robustness checks after the mechanism is already coherent.
- Call newly added extension verbs through the generic `verb` path.

## Generic Fallbacks

```bash
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.query_node --params-json '{"search":"music streaming","search_mode":"hybrid","top_k":5}'
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.node_description --params-json '{"node_id":"SPOT.price"}'
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.observe_predict_resolved_time --params-json '{"target_node":"SPOT.price"}'
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.intervene_time_lag --params-json '{"treatment_node":"SPOT.price","treatment_value":0.05,"outcome_node":"NFLX.price","horizon_steps":3,"model":"linear"}'
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.validate_connectivity --params-json '{"variables":["NVDA.price","AMD.price","SOXX.price"]}'
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.discover_consensus --params-json '{"seed_nodes":["NVDA.price","ANET.price"],"direction":"out","limit":10}'
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.discover_deconsensus --params-json '{"seed_nodes":["NVDA.price"],"direction":"out","contrast_level":"medium","limit":8}'
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.discover_fragility --params-json '{"node_ids":["SIM.price","MOOOUSD.price"],"severity_level":"medium","only_fragility":true,"limit":10}'
```

## Validation

Probe the live surface first with:

- one `capabilities`
- one targeted `methods`
- one resolved-time observational call
- one simple structural call

Bridge-node rule:

- repeated bridge + semantically rich neighborhood -> inspect further
- repeated bridge + microcap or crypto-heavy neighborhood -> summarize as transmission noise and move on

## Endpoint Notes

- The current default CAP surface answers on `https://cap.abel.ai/api/cap`.
- Production CAP surface answers on `https://cap.abel.ai/api/cap`.
- The probe accepts base URLs such as `https://cap.abel.ai/api` and resolves them to `/cap`.
- `https://api.abel.ai/echo/` is used for OAuth and business API flows in `setup-guide.md`; it is not the default CAP probe base.

## See Also

- `../SKILL.md` for the dispatcher and read order
- `routes/direct-graph.md` for direct graph flow
- `routes/proxy-routed.md` for proxy-routed flow
- `routes/capability-discovery.md` for live surface inspection
- `grounding-and-labeling.md` for node mapping and answer labels
- `web-grounding.md` for graph-grounded web search
