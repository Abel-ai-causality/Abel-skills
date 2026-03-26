# Probe Usage

Use this file only after `SKILL.md` and the chosen route file have already fixed:

- the mode
- the anchor set
- whether web grounding is needed

This file is a command manual, not the main workflow.

## Authorization First

- Do not run the bundled probe until an Abel user API key is available in session state, `--api-key`, `<skill-root>/.env.skill`, or legacy `<skill-root>/.env.skills`.
- If a key is already available, skip auth docs and go straight to the chosen route.
- If the key is missing, start the OAuth handoff from `setup-guide.md` first.
- By default, `cap_probe.py` reads `.env.skill` first and falls back to `.env.skills`.

## Bundled Script

Prefer `scripts/cap_probe.py` over ad hoc payload construction. The main entrypoints are `capabilities`, `normalize-node`, `methods`, `neighbors`, `paths`, `observe`, `intervene-do`, `intervene-time-lag`, `validate-connectivity`, and the generic `verb` fallback.

## Common Direct Calls

Run these from the skill root:

```bash
BASE_URL="https://cap-sit.abel.ai"

python scripts/cap_probe.py --base-url "$BASE_URL" capabilities
python scripts/cap_probe.py normalize-node NVDA
python scripts/cap_probe.py --base-url "$BASE_URL" methods extensions.abel.query_node extensions.abel.node_description
python scripts/cap_probe.py --base-url "$BASE_URL" neighbors NVDA_close --scope children --max-neighbors 5
python scripts/cap_probe.py --base-url "$BASE_URL" paths NVDA_close AMD_close --max-paths 3
python scripts/cap_probe.py --base-url "$BASE_URL" observe NVDA_close
python scripts/cap_probe.py --base-url "$BASE_URL" intervene-do NVDA_close 0.05 --outcome-node AMD_close
```

## Usage Rules

- `normalize-node` is the safest first step when a prompt gives a bare ticker.
- Manual mapping is still the first pass for obvious company and proxy anchors.
- Use `extensions.abel.query_node` for fuzzy or broad phrases.
- Use `extensions.abel.node_description` on the final shortlist before writing the answer.
- For executable anchors that materially bear on the question, run one observational read before deeper structure.
- Search the company or industry labels from `node_description`, not raw node ids.
- Check `meta.methods` before assuming a local wrapper is current.
- Prefer `extensions.abel.observe_predict_resolved_time` over `observe.predict` when available.
- `observe.predict` is only an observational fallback read.
- Treat `intervene-do`, `intervene-time-lag`, and `counterfactual-preview` as late pressure-test surfaces.
- For non-trivial comparative reads, one compact `intervene-do` call is the default late pressure test after the mechanism is coherent.
- Call newly added extension verbs through the generic `verb` path.

## Generic Fallbacks

```bash
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.query_node --params-json '{"search":"music streaming","search_mode":"hybrid","top_k":5}'
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.node_description --params-json '{"node_id":"SPOT_close"}'
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.validate_connectivity --params-json '{"variables":["NVDA_close","AMD_close","SOXX_close"]}'
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.discover_consensus --params-json '{"seed_nodes":["NVDA_close","ANET_close"],"direction":"out","limit":10}'
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.discover_deconsensus --params-json '{"seed_nodes":["NVDA_close"],"direction":"out","contrast_level":"medium","limit":8}'
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.discover_fragility --params-json '{"node_ids":["SIM_close","MOOOUSD_close"],"severity_level":"medium","only_fragility":true,"limit":10}'
```

## Validation

Probe the live surface first with:

- one `capabilities`
- one targeted `methods`
- one simple observational call
- one simple structural call

Bridge-node rule:

- repeated bridge + semantically rich neighborhood -> inspect further
- repeated bridge + microcap or crypto-heavy neighborhood -> summarize as transmission noise and move on

## Endpoint Notes

- The current default CAP surface answers on `https://cap-sit.abel.ai/cap`.
- Production CAP surface answers on `https://cap.abel.ai/cap`.
- SIT CAP surface answers on `https://cap-sit.abel.ai/cap`.
- The probe accepts base URLs such as `https://cap-sit.abel.ai` and resolves them to `/cap`.
- `https://api-sit.abel.ai/echo/` is used for OAuth and business API flows in `setup-guide.md`; it is not the default CAP probe base.

## See Also

- `../SKILL.md` for the dispatcher and read order
- `routes/direct-graph.md` for direct graph flow
- `routes/proxy-routed.md` for proxy-routed flow
- `routes/capability-discovery.md` for live surface inspection
- `grounding-and-labeling.md` for node mapping and answer labels
- `web-grounding.md` for graph-grounded web search
