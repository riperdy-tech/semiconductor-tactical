# Agent Instructions — High-Beta Tactical Research Engine

## 0. Read this first

Before writing code, read:

1. `README.md`
2. `AGENTS.md`
3. `docs/REDDIT_SOURCE_NOTES.md`
4. `docs/STRATEGY_SPEC.md`
5. `docs/BACKTEST_PROTOCOL.md`
6. `docs/DATA_CONTRACT.md`
7. `docs/ARCHITECTURE.md`
8. `docs/IMPLEMENTATION_PLAN.md`
9. `docs/EXPERIMENT_MATRIX.md`
10. `docs/AUDIT_20261002.md`

Do not skip documents because the repository is small. The purpose of these documents is to prevent implementation drift.

## 1. Role

You are the implementation agent. The human decides whether a research finding is useful. Your job is to produce reproducible software and clearly documented evidence.

Do not turn an observed Reddit trader's claims into facts. Use labels:

- `OBSERVED`: directly described by the source post/comments.
- `DERIVED`: a mechanical inference from observed behavior.
- `HYPOTHESIS`: a proposed signal/rule that has not been validated.
- `ASSUMPTION`: required because the source does not specify the detail.
- `UNVERIFIED`: information that cannot yet be checked from primary data.

## 2. Strategy integrity

The strategy specification is authoritative. If you think a rule is poor, do not silently replace it. Add a decision entry in `docs/DECISIONS.md`, explain why the change is needed, and add a separate experiment where appropriate.

Do not optimize directly against the headline $550k result. The target is to explain whether the **mechanics** can create positive expectancy after realistic costs and across out-of-sample periods.

## 3. User workflow is part of correctness

Do not make the human run a sequence of undocumented Python commands just to validate the repository.

The repository must provide:

- `run.ps1` as the canonical Windows entry point;
- `run.bat` as a double-click launcher;
- GitHub Actions CI that runs tests and smoke checks automatically.

When adding a new required manual step, update the runner and README in the same change.

The runner must bootstrap the local virtual environment and dependencies when practical, and must stop on the first failed check.

## 4. Synthetic fixtures must never masquerade as research

Synthetic data exists only for deterministic software validation.

Any command that runs synthetic fixtures must say so in its console output and report.

Do not call fixture output a historical backtest, strategy result, market result, or evidence of an edge.

A historical research command should refuse to run when the required real-data contract is missing.

## 5. No hidden leverage tricks

Never use unconstrained averaging down or martingale sizing in the default risk-controlled strategy.

Literal replication may simulate averaging/layering as a separate experimental mode, but it must have explicit maximum layers, capital limits, and margin-call logic.

Never omit margin interest, financing, option assignment, or forced liquidation merely because they reduce performance.

When leverage is exposed as a parameter, it must actually constrain gross exposure. Configuration-only leverage is not considered implemented.

## 6. No look-ahead

Signals at timestamp `t` may only use information available at or before `t`.

If a bar closes at `t`, an order derived from that close cannot fill at that same bar's unknown close unless the data source and execution semantics explicitly justify it. Default behavior: signal at bar close -> earliest fill is next eligible trade/bar.

If both stop and target are touched inside one bar and the data cannot resolve sequence, use the conservative fill assumption documented in `BACKTEST_PROTOCOL.md`.

## 7. Options

Covered calls must be backed by actual historical option-chain data where possible. Do not use theoretical Black-Scholes prices as if they were executable market prices.

If historical option data is unavailable, mark the options experiment `UNVALIDATED` and run the equity-only engine separately. Never substitute fictional options fills into the headline result.

Options must support the actual source behavior being tested, including repurchase-on-pullback, before the option experiment can be presented as a replication.

## 8. Data provenance

Every research run must persist:

- data provider / file source;
- symbols;
- date range;
- bar resolution;
- timezone;
- corporate-action treatment;
- option data source, if any;
- transaction-cost model;
- slippage model;
- parameter configuration hash;
- git commit hash.

For historical runs, include hashes or immutable identifiers for the actual input data.

## 9. Testing

Minimum expectation for each implementation slice:

- unit tests for formulas and state transitions;
- at least one no-lookahead regression test;
- at least one cost/slippage regression test;
- at least one margin/forced-liquidation test once leverage exists;
- deterministic fixture test where repeated runs produce the same result.

Use `pytest`. Prefer small pure functions over stateful magic.

Every user-visible CLI path must have a smoke test in CI.

## 10. Output discipline

Every experiment must produce both:

1. machine-readable result (`JSON` or Parquet/CSV as appropriate);
2. human-readable report (`Markdown`).

Reports must include the configuration, sample sizes, caveats, and all major metrics.

Do not publish only CAGR/return.

## 11. Scope control

Do not add:

- brokerage order submission;
- credential management;
- automated live trading;
- Telegram/Discord execution alerts;
- a web UI;
- LLM strategy selection;

until a separate specification explicitly requests them.

The first implementation milestone is historical research.

## 12. Completion standard

A task is not complete because code runs once. It is complete when:

- tests pass;
- the documented one-command runner reproduces the result;
- CI passes;
- the result contains provenance;
- assumptions are documented;
- the implementation does not contradict the strategy/backtest specs;
- no new hidden dependency or network requirement was introduced without documentation;
- the README tells the human exactly what is real research and what is only fixture validation.
