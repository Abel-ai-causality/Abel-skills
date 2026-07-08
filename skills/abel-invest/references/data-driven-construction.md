# Data-Driven Construction

Use this reference for ordinary non-grandma alpha search, especially when the
next idea is drifting toward another hand-written rule.

This is the default construction stance, not a separate workflow. This file
owns candidate-expression choices; `experiment-loop.md` owns sequencing and
first-look scout mechanics, and `guarded-optimization.md` owns hard-target
reportability.

## Default Posture

Build candidates by high-capacity empirical construction over a scoped
universe. Usual ingredients include:

- target history and any validated baseline or catalog strategy
- live graph nodes and graph-derived feeds when available
- selected supplemental cross-asset, volume, liquidity, sector, or regime feeds
  when evidence or the user goal justifies them

The graph bounds and enriches the alpha universe. It does not prescribe one
tradable basket, and it is not satisfied by placing a few nodes into a simple
hand-written rule. The agent owns how to express the data.

## Construction Space

Data-driven construction can use many empirical degrees of freedom:

- deterministic feature factory over target + graph-derived fields
- weak-signal ensemble with diversity-aware member selection
- graph-node subset, lag, sign, transformation, ratio, spread, or rolling-window
  search
- model-family comparison such as linear, tree, GBDT, or hybrid models
- supervised target/graph model when label and horizon are temporally legal
- unsupervised denoise or compression such as PCA/ICA when temporally legal
- regime, sizing, or filter search layered on an otherwise plausible alpha

This list is not a route plan. Use the bounded feature universe most likely to
improve the user's objective, and let observed behavior decide how the search
evolves.

## Disposable Search Workbench

Temporary scripts, feature screens, quick model comparisons, CSV/JSON summaries,
notebook cells, query cells, or one-off shell heredocs are normal Abel Invest
research. Prefer `research/<ticker>/<session_id>/scratch/` for files. Scratch
outputs are not validation evidence; they help choose what is worth formal,
audited validation.

Use scratch to compare construction axes, not to create paperwork. A compact
first-look scout should usually take roughly 5 minutes and should behave as a
quick, broad shortlist builder for candidate directions and coarse variants.
Its job is to produce candidates for recorded branch validation, not to keep
optimizing in scratch. Prefer a ranked table over a prose-only memo, using
objective metrics such as Sharpe, total return, drawdown, and turnover when
feasible.

Keep each ScoutRun about 10,000 candidates or fewer.

When scratch work scores multiple variants to choose a recorded candidate, use
the scout runtime boundary in `experiment-loop.md`.
If a ScoutRun stops after partial rows, treat those rows as that batch's final
scratch evidence. Build from those rows when they support a recorded branch;
do not rerun scratch search just to make the ranking feel more complete.

After a recorded branch fails, treat it as reusable evidence, not a
same-branch tuning target. Prefer another meaningful recorded branch from
existing evidence over more scratch search around the same branch. A strong
lead belongs in the ledger; it is not a place to keep searching locally.

Diagnostic tables are raw material. IC, correlation, or feature-importance
screens can rank inputs, but they do not by themselves show whether a tradable
position rule or model expression works.

For prepared-data ordering, prepare-only scout branches, and promotion into
recorded rounds, follow `experiment-loop.md`.

## What Simple Rules Are For

Simple target-history-only, buy-and-hold, or graph-node rows are useful as:

- reference metrics beside richer candidates
- quick diagnostics of direction, sign, risk, or target-window difficulty

They are not ordinary formal candidates in graph-informed alpha search. Record a
target-history-only strategy only when usable graph, supplement, or other
non-target data cannot support the search, or when the user explicitly asks for
that strategy shape. A branch can be `graph_supported` because it reads prepared
graph inputs and still be a narrow hand-written mechanism.

## Search Accounting

If the submitted branch was selected from a scan, grid, model comparison, HPO
run, node-subset choice, or feature-factory screen, record the effective width.
K is an audit meter, not an exploration brake. `experiment-loop.md` owns the
per-round `--selection-trials` rule; `guarded-optimization.md` owns final-K
reportability.

## Failure Reading

A failed empirical construction says that expression failed. It does not prove
the graph is useless, and it does not prove target-history-only should take
over. Reuse the informative parts in distinct candidates instead of tuning the
same failed branch.

Before claiming no edge, the ledger should show that the search did not collapse
to one hand-written rule or one local lead.
