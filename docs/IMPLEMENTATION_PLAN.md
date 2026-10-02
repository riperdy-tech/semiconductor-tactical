# Implementation Plan

## Phase 0 — Repository foundation

- [x] Python package + `pyproject.toml`
- [x] pytest + lint/format tooling
- [x] typed configuration loader
- [x] run manifest
- [x] basic data models
- [x] deterministic fixture data

Exit criterion: `pytest` passes on a clean environment.

## Phase 1 — Equity-only engine

- [x] normalized OHLCV provider interface
- [x] feature calculator
- [x] pullback signal family
- [x] exit family
- [x] position sizing
- [x] transaction costs
- [x] slippage
- [x] deterministic backtest loop
- [x] metrics + Markdown report

Exit criterion: can reproduce the same fixture result twice byte-for-byte except for run timestamps.

## Phase 2 — Robustness framework

- [x] walk-forward splits
- [x] parameter sweeps
- [x] regime partitioning
- [x] bootstrap/randomization
- [x] result comparison tables
- [x] parameter stability diagnostics

Exit criterion: one command can generate the full equity-only experiment matrix.

## Phase 3 — Margin model

- [x] financing rate
- [x] maintenance margin
- [x] buying power
- [x] forced liquidation
- [x] liquidation slippage
- [x] intraday/overnight constraints

Exit criterion: synthetic tests cover margin-call and recovery edge cases.

## Phase 4 — Options engine

- [ ] option-chain provider interface
- [ ] covered-call order lifecycle
- [ ] option spread/slippage
- [ ] assignment
- [ ] underlying linkage
- [ ] premium attribution

Exit criterion: a small real historical chain fixture can reconstruct a known call sequence without look-ahead.

## Phase 5 — Strategy comparison

Generate:

- literal clone;
- risk controlled;
- regime adapted.

Each must use the same base data and reporting metrics.

## Phase 6 — Research report

Create:

`reports/strategy_comparison.md`

with:

- headline findings;
- regime dependence;
- cost sensitivity;
- leverage sensitivity;
- options contribution;
- margin-call frequency;
- robustness;
- limitations.

Do not declare an edge until the out-of-sample criteria in the research plan are met.
