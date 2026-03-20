# Probe Usage

Use this file for `cap_probe.py` details and reusable command patterns.

## Bundled Script

Prefer the bundled probe script over ad hoc payload construction.

Primary script:
- `skill/causal-abel/scripts/cap_probe.py`

Deterministic subcommands:
- `capabilities`
- `observe`
- `neighbors`
- `paths`
- `markov-blanket`
- `intervene-do`
- `traverse-parents`
- `traverse-children`
- `validate-connectivity`
- `abel-markov-blanket`
- `counterfactual-preview`
- `intervene-time-lag`
- `verb` for arbitrary CAP verbs
- `route` for arbitrary Abel route aliases

## Common Direct Calls

```bash
BASE_URL="https://cap-sit.abel.ai/api"

python skill/causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" capabilities
python skill/causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" observe NVDA_close
python skill/causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" neighbors NVDA_close --scope children --max-neighbors 5
python skill/causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" paths NVDA_close AMD_close --max-paths 3
python skill/causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" markov-blanket NVDA_close --max-neighbors 10
python skill/causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" intervene-do NVDA_close 0.05 --outcome-node AMD_close
python skill/causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" validate-connectivity NVDA_close AMD_close SOXX_close
python skill/causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" intervene-time-lag NVDA_close 0.05 --outcome-node AMD_close --horizon-steps 24 --model linear
```

Proxy routing still uses the same script. The difference is which anchors you choose and how you compare them.

## Generic Fallbacks

```bash
python skill/causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.validate_connectivity --params-json '{"variables":["NVDA_close","AMD_close","SOXX_close"]}'
python skill/causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" route extensions/abel/counterfactual_preview --params-json '{"intervene_node":"NVDA_close","intervene_time":"2024-01-01T00:00:00Z","observe_node":"AMD_close","observe_time":"2024-01-02T00:00:00Z","intervene_new_value":0.05}'
```

For narrower output, use `--pick-fields` and `--compact`.

## Validation

Probe the live surface first:

```bash
python skill/causal-abel/scripts/cap_probe.py capabilities
python skill/causal-abel/scripts/cap_probe.py observe NVDA_close
python skill/causal-abel/scripts/cap_probe.py paths NVDA_close AMD_close --max-paths 3
```
