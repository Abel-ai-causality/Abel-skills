# Methodology

causal-edge owns the metric triangle definition and the "why causal" argument.
See `causal-edge docs/why-causal.md` for the full derivation (Pearl, DGP, regime invariance).

This file covers only what causal-edge doesn't: the axiom/constraint distinction
and production proofs specific to the research loop.
For the current branch-first operating flow, read `experiment-loop.md` and
`discovery-protocol.md` first; this file explains the research logic behind them.

## Axioms (math — cannot be wrong)

**A1. Causal K < blind K → DSR honest.**
Abel gives ~10 justified parents vs ~10,000 blind scan. Same signal at Sharpe 1.8:
causal DSR=97%, blind DSR=41%. Follows from Pearl + DSR formula.

**A2. Temporal illegality = invalid backtest.**
If the strategy reads information it could not have seen at decision time, the
backtest is lying. See `references/constraints.md` for the runtime contract.

## Constraints (empirical — questionable with evidence)

**C1. Multi-dimensional validation > single metric.**
Currently Lo × IC × Omega via causal-edge. The specific metrics could evolve.
The principle is permanent. Proof: xcorr scale sweep, 2.0/0.0 passed Lo+Sharpe but IC
collapsed 29% — only the triangle caught concentration gaming.

**C2. Serial compounding > pre-defined grid.**
Each KEEP updates baseline. 200+ experiments across 6 assets confirm. BNB: 158 serial
→ Sharpe 2.82. Grid search of same space → lower optimum.

**C3. Explore = genuinely new information.**
Removing features = exploit variant. Real explore: new data source, new causal depth,
new relationships. 100 "explore" that only subtracted → 0 keeps.

**C4. Causal-first, correlation-allowed.**
Use Abel-discovered causal structure as the default search prior because it reduces K and is more likely to survive regime change. Correlation-derived signals can still be valid, but they should enter as supplements, not replacements: require orthogonality to the causal core and stronger empirical scrutiny before promoting them.

**C5. Fallback is continuity mode, not equal discovery evidence.**
If Abel is unavailable, heuristic discovery can keep the research loop moving and may still produce tradeable strategies. But the discovery prior is weaker: K is higher in spirit, confidence should be downgraded, and outcomes are not directly comparable to Abel-led causal discovery claims.

## Runtime Consequence

In the current branch workflow, the right burden split is:

- `Abel-alpha` makes the branch world explicit
- `causal-edge` owns temporal/runtime legality
- the strategy owns mechanism design inside that visible world

That is why the branch-default path is now:

- inspect prepared inputs
- write `compute_decisions(self, ctx)`
- use semantic preflight before a recorded run

not:

- hand-assemble raw frames
- cargo-cult a fixed list of shift rules
- trust the backtest because the code "looks lagged"
