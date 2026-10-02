# Agent Instructions — High-Beta Tactical Research Engine

## 0. Read this first

Before writing code, read:

1. `README.md`
2. `docs/STRATEGY_SPEC.md`
3. `docs/BACKTEST_PROTOCOL.md`
4. `docs/DATA_CONTRACT.md`
5. `docs/ARCHITECTURE.md`
6. `docs/IMPLEMENTATION_PLAN.md`

Do not begin by inventing implementation details that are already specified in those documents.

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

## 3. No hidden leverage tricks

Never use unconstrained averaging down or martingale sizing in the default risk-controlled strategy.

Literal replication may simulate averaging/layering as a separate experimental mode, but it must have explicit maximum layers, capital limits, and margin-call logic.

Never omit margin interest, financing, option assignment, or forced liquidation merely because they reduce performance.

## 4. No look-ahead

Signals at timestamp `t` may only use information available at or before `t`.

If a bar closes at `t`, an order derived from that close cannot fill at that same bar's unknown close unless the data source and execution semantics explicitly justify it. Default behavior: signal at bar close -> earliest fill is next eligible trade/bar.

If both stop and target are touched inside one bar and the data cannot resolve sequence, use the conservative fill assumption documented in `BACKTEST_PROTOCOL.md`.

## 5. Options

Covered calls must be backed by actual historical option-chain data where possible. Do not use theoretical Black-Scholes prices as if they were executable market prices.

If historical option data is unavailable, mark the options experiment `UNVALIDATED` and run the equity-only engine separately. Never substitute fictional options fills into the headline result.

## 6. Data provenance

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

## 7. Testing

Minimum expectation for each implementation slice:

- unit tests for formulas and state transitions;
- at least one no-lookahead regression test;
- at least one cost/slippage regression test;
- at least one margin/forced-liquidation test once leverage exists;
- deterministic fixture test where repeated runs produce the same result.

Use `pytest`. Prefer small pure functions over stateful magic.

## 8. Output discipline

Every experiment must produce both:

1. machine-readable result (`JSON` or Parquet/CSV as appropriate);
2. human-readable report (`Markdown`).

Reports must include the configuration, sample sizes, caveats, and all major metrics. Do not publish only CAGR/return.

## 9. Scope control

Do not add:

- brokerage order submission;
- credential management;
- automated live trading;
- Telegram/Discord execution alerts;
- a web UI;
- LLM strategy selection;

until a separate specification explicitly requests them.

The first implementation milestone is historical research.

## 10. Completion standard

A task is not complete because code runs once. It is complete when:

- tests pass;
- the documented command reproduces the result;
- the result contains provenance;
- assumptions are documented;
- the implementation does not contradict the strategy/backtest specs;
- no new hidden dependency or network requirement was introduced without documentation.
