# Post-First-Real-Run Audit

## Purpose

The first genuine Massive 1-minute historical run produced strongly negative results.

Those results are evidence about the current mechanical implementation. They are not yet a final verdict on the source trader's behavior.

This phase is a methodology and implementation-correction gate, not a strategy-optimization exercise.

## Observed first-run result

Reported first-run outputs:

| Variant | Return | Max DD | Trades | Win rate | Profit factor |
|---|---:|---:|---:|---:|---:|
| literal_clone | about -99% | about 99% | about 4,571 | about 26.8% | about 0.22 |
| risk_controlled | about -95% | about 95% | about 5,450 | about 26.7% | about 0.24 |
| regime_adapted | about -40% | about 40% | about 1,283 | about 23.2% | about 0.30 |

These values are preserved here as the first-run diagnostic. Do not tune to improve them.

## Non-negotiable rule

Do not respond to the negative P&L by changing thresholds, leverage, symbols, cost assumptions, OOS dates, or exit parameters.

First correct implementation fidelity and research protocol.

## Gate 1 — Preserve first-run evidence

Before any code change:

1. Preserve the completed report and machine-readable comparison output.
2. Record dataset ID and aggregate SHA-256.
3. Record exact git commit.
4. Record exact config path and config hash.
5. Record whether USD was included.
6. Confirm the report scope is FULL SAMPLE when no OOS boundaries were configured.
7. Confirm .env and API credentials are not tracked.

Never overwrite the first-run evidence.

## Gate 2 — Fix ATR exit geometry

Current issue:

Position sizing uses ATR at entry to determine risk, while exit checking can use the current bar's ATR.

This makes the actual stop risk change after entry and breaks the relationship between the configured risk budget and the stored position.

Required correction:

- Calculate initial ATR at entry.
- Calculate and store the initial stop price and target price.
- Persist that exit geometry for the active position/layer.
- Use the stored values throughout the trade.
- Do not introduce trailing/dynamic ATR behavior unless explicitly specified by the strategy.

Tests required:

- later ATR expansion does not move the stop;
- later ATR contraction does not move the stop;
- later ATR changes do not move the target;
- position sizing uses the same stop stored for the trade.

## Gate 3 — Clarify signal semantics

Current comparison code disables the sector filter for literal_clone and risk_controlled.

With sector_filter disabled, the entry logic is largely pullback-zscore plus relative-volume filtering, with the event filter depending on configuration.

This is a mechanical hypothesis, not a recovered copy of the discretionary Reddit behavior.

Required:

- Keep the current behavior intact unless a real defect requires change.
- Explicitly document sector-filter state for every variant.
- Explicitly document trend-confirmation state.
- Label unsupported details as OBSERVED, DERIVED, HYPOTHESIS, ASSUMPTION, or UNVERIFIED.
- Do not silently add trend rules and call them observed behavior.
- Do not replace the canonical variants with a better-looking variant.

## Gate 4 — Trade-frequency diagnostics

The source notes report roughly 1,300+ trades over 90 days. The first implementation generated roughly 4,500–5,500 trades.

Do not force the backtest to match 1,300 trades.

Add reporting for:

- total trades;
- trades/day;
- trades/symbol/day;
- median holding time;
- signal count;
- filled-entry count;
- simultaneous positions;
- repeated entries/re-entries;
- time in market.

The source trade count is an OBSERVED reference point, not a tuning target.

## Gate 5 — Explicit train / validation / test

The first run did not have explicit OOS boundaries.

Before the next formal result, define:

- start;
- train_end;
- validation_end;
- test_start;
- end.

Requirements:

- chronological order;
- pairwise-disjoint partitions;
- documented in docs/DECISIONS.md;
- stored in config;
- stored in run_manifest;
- visible in the report.

Do not choose boundaries based on performance.

Do not use TEST_OOS to tune parameters.

## Gate 6 — Provenance reconciliation

Verify and report:

- dataset manifest;
- run manifest;
- comparison JSON;
- report;
- git SHA;
- config hash;
- per-file hashes;
- aggregate data hash;
- symbols;
- date coverage;
- 1m resolution;
- source/provider;
- adjustment policy;
- USD inclusion.

## Gate 7 — Separate signal weakness from execution drag

Report both:

1. zero-slippage/pre-cost mechanical result;
2. realistic-cost result.

Also report:

- gross P&L;
- commission;
- slippage;
- market-impact proxy;
- financing;
- net P&L;
- costs as percentage of gross P&L.

Do not claim that costs alone explain the first-run failure if the zero-slippage result is already negative.

## Gate 8 — Interpret regime adaptation carefully

The first run showed regime_adapted losing less than the other variants.

Treat this only as an observation.

For formal interpretation, inspect:

- train/validation/TEST_OOS;
- trade-count changes;
- time-in-market;
- regime distribution;
- identical cost assumptions;
- prescribed robustness diagnostics.

## Acceptance criteria

- [ ] First-run evidence preserved.
- [ ] ATR stop/target frozen per trade/layer.
- [ ] ATR regression tests pass.
- [ ] Current signal semantics explicitly documented.
- [ ] Trade-frequency diagnostics added.
- [ ] Explicit OOS boundaries exist.
- [ ] Provenance reconciled.
- [ ] Cost decomposition explicit.
- [ ] pytest passes.
- [ ] ruff passes.
- [ ] CI passes.
- [ ] No API key or .env committed.
- [ ] No strategy parameter was changed to improve performance.

## Stop condition

After these corrections, stop software changes unless a test exposes a real defect.

The next step is a clean, pre-declared OOS research run.
