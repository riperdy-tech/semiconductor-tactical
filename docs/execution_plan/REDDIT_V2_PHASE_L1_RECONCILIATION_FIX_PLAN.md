# Gemini Execution Plan — Phase L.1 V2 Accounting Reconciliation & Reproducibility Fix

## Objective

Correct the remaining research-accounting and reproducibility defects discovered during review of Phase L.

This is a narrowly scoped follow-up to Phase L.

It is NOT a strategy change, optimization pass, parameter search, robustness search, or new behavioral experiment.

The only permitted changes are those required to make:
1. the tactical P&L layers mathematically self-consistent;
2. open-position costs distinguishable from closed-trade costs;
3. the canonical report/JSON internally consistent;
4. the automated tests actually prove the no-lookahead and margin-timing claims;
5. the Gemini completion report exactly match the checked-in artifacts.

## Hard rules

Do NOT:
- change any V2 directional parameter;
- change the 60% core allocation;
- change MU/SNDK/SKHY universe;
- change tactical sizing;
- change slippage or commission assumptions;
- change margin rate or leverage assumptions;
- add covered calls;
- add Level-2;
- add KRX/Tokyo execution;
- search for a better historical result;
- select an accounting interpretation because it improves P&L;
- overwrite the preserved Phase K artifact.

Any historical rerun is permitted only after a mechanically necessary accounting/reporting correction, using the exact same frozen behavioral configuration and cost configuration.

## 1. Read first

Read:
- docs/execution_plan/REDDIT_V2_POST_RUN_AUDIT_AND_ACCOUNTING_PLAN.md
- docs/execution_plan/GEMINI_POST_FIRST_RUN_HANDOFF.md
- src/tactical_engine/backtest/v2_engine.py
- src/tactical_engine/execution/simulator.py
- src/tactical_engine/data/models.py
- src/tactical_engine/portfolio/v2_portfolio.py
- src/tactical_engine/research/v2_historical_runner.py
- tests/test_v2_post_run_audit.py
- reports/V2_HISTORICAL_COMPARISON.md
- reports/v2_historical_comparison.json
- reports/fidelity_runs/phase_k_baseline_1eda7cc/
- commit 0ce2208 and the exact Phase L run artifacts.

## 2. Preserve Phase L exactly before editing

Before any correction:
- record the current Phase L commit SHA;
- preserve the current Phase L Markdown report and JSON;
- preserve the Phase K archive;
- create a Phase L.1 preservation note identifying the current report as the pre-correction artifact.

Required labels:
- PHASE_K_REPORTED_RESULT
- PHASE_L_REPORTED_RESULT
- PHASE_L1_CORRECTED_RESULT

Do not overwrite the historical Phase L evidence without preserving it.

## 3. Primary defect — closed vs open slippage attribution

The current report contains an internal mismatch:
- gross reference P&L for completed tactical trades;
- total reported execution slippage;
- closed realized P&L;
- terminal open tactical positions.

The total slippage figure may include entry slippage on tactical positions that remain open at the evaluation end, while the closed-trade reference P&L only covers completed FIFO round trips.

Required accounting model:

### A. Closed tactical inventory

closed_reference_pnl - closed_entry_slippage - closed_exit_slippage - closed_commissions = closed_net_realized_pnl

### B. Open tactical inventory at period end

open_reference_mtm - open_entry_slippage - open_entry_commissions = open_net_terminal_contribution

Do not subtract open-entry slippage from closed-trade P&L.
Do not subtract the same open-entry slippage again when reconciling final account equity.

### Required implementation behavior

Expose separate totals for at least:
- closed_reference_pnl;
- closed_entry_slippage;
- closed_exit_slippage;
- closed_commissions;
- closed_net_realized_pnl;
- open_reference_mtm;
- open_entry_slippage;
- open_entry_commissions;
- open_net_terminal_contribution;
- total_tactical_economic_contribution.

If a simpler equivalent formulation is used, prove exact algebraic equivalence in tests and documentation.

## 4. Preserve the correct meaning of realized_pnl

Keep a clear distinction between:
- trade-record pre_slippage_pnl;
- trade-record execution-price P&L;
- account-level commission/financing costs.

Do not silently redefine fields.

Recommended semantics:
- pre_slippage_pnl = quantity × (exit_reference_price − entry_reference_price)
- realized_pnl = quantity × (exit_execution_price − entry_execution_price)
- slippage = explicit execution-price deviation attributable to entry + exit
- commission = entry + exit commissions attributable to that matched quantity

Account-level economic P&L then includes commissions and financing exactly once.

## 5. Prove the exact algebra

Add a deterministic reconciliation test with:
- non-zero entry slippage;
- non-zero exit slippage;
- non-zero commission;
- at least one closed trade;
- at least one still-open tactical lot.

The test must prove separately:
- closed_reference_pnl - closed_slippage - closed_commissions = closed_net_realized_pnl;
- open_reference_mtm - open_entry_slippage - open_entry_commissions = open_net_terminal_contribution;
- closed_net_realized_pnl + open_net_terminal_contribution - financing = tactical/account economic contribution;
- final account-equity reconciliation closes to machine precision.

The expected test must fail if open-entry slippage is incorrectly included in the closed-trade layer.

## 6. Reconcile the exact historical mismatch

Do not hard-code any expected historical number before computing it.

Use the current Phase L artifacts to identify exactly why:

gross closed reference P&L - total reported slippage != closed realized P&L

if that mismatch exists.

Produce a diagnostic showing:
- total slippage;
- closed-trade slippage;
- open-position entry slippage;
- any remaining discrepancy.

The report must state which component explains the difference.
Do not simply relabel the numbers.

## 7. Canonical report / JSON consistency

The checked-in Markdown report and JSON must describe the same exact run.

Every one of these values must agree between report and JSON:
- run ID;
- git SHA;
- effective start;
- evaluation end;
- initial cash;
- starting core value;
- residual cash;
- final equity;
- V2-A/B/C returns;
- tactical closed P&L;
- tactical terminal P&L;
- total tactical contribution;
- reference P&L;
- closed/open slippage;
- commissions;
- financing;
- signals;
- order attempts;
- entry fills;
- reload fills;
- exits;
- completed round trips;
- open lots;
- open shares;
- margin status.

Add a test that loads the canonical JSON and verifies the key Markdown-rendered values against the underlying result object or canonical calculation source.

## 8. Remove contradictory completion-summary claims

The final Gemini completion text must not say that terminal open positions are zero if the canonical artifact says there are open positions.

The final completion summary must be generated from, or manually checked against, the final JSON artifact.

Required rule:
THE CHECKED-IN MACHINE-READABLE ARTIFACT IS AUTHORITATIVE.

Do not report stale values from an earlier diagnostic run.

## 9. Strengthen no-lookahead test — buying power

The existing test named test_next_open_buying_power_no_lookahead does not actually exercise the buying-power accept/reject decision.

Replace or extend it so that:
1. create two scenarios differing only in bar t close;
2. hold bar t+1 open constant;
3. create a V2-C pending buy whose acceptance depends materially on available buying power;
4. execute the pending order on bar t+1;
5. prove that changing bar t close does not change buying-power calculation at execution, accept/reject result, or fill quantity.

The assertion must exercise run_v2_backtest() or an equivalent execution-time portfolio decision path, not merely compare two identical simulator fills.

## 10. Strengthen no-lookahead test — margin liquidation

The existing test named test_next_open_margin_liquidation_semantics must prove execution timing, not merely order generation.

Required synthetic sequence:
- bar t close creates a margin call;
- liquidation orders are created at bar t close;
- bar t close must not execute the liquidation;
- bar t+1 open executes the queued liquidation;
- the resulting inventory/cash change first appears at bar t+1 execution.

Add an explicit assertion that the liquidation order is still pending at the end of bar t and is consumed at the next execution point.

## 11. Strengthen peak-margin-debt test

The existing test named test_peak_margin_debt_sampled_after_transactions does not prove that peak debt actually captures a newly created debt balance.

Replace/extend it with a synthetic transaction where:
- the account has enough initial cash for core;
- a tactical transaction creates a known positive margin debt;
- reported peak_margin_debt equals or exceeds that known debt;
- the debt is observed after the transaction on the same timestamp.

Do not merely assert reconciles_cleanly.

## 12. Verify report arithmetic using the actual current result

After implementing the attribution correction, calculate:
1. V2-A final equity;
2. V2-B final equity;
3. V2-C final equity;
4. core contribution;
5. closed tactical contribution;
6. open tactical terminal contribution;
7. financing;
8. total account P&L.

Use the actual final JSON as the single source for the Markdown report.

If ending equity does not change, state:
PHASE_L1_ACCOUNTING_RECONCILIATION_DID_NOT_CHANGE_ENDING_EQUITY

If ending equity changes because the prior report was accounting-only wrong, preserve both Phase L and Phase L.1 results and explain the exact mechanical cause.

Do not describe an accounting correction as strategy improvement.

## 13. Historical rerun policy

A historical rerun is allowed only if required to produce the corrected accounting artifacts.

Before rerunning, record:
- Phase L.1 frozen parameters;
- exact cost config;
- exact dataset ID and hash;
- exact effective start;
- exact code commit used.

The rerun must use:
- MU/SNDK/SKHY only;
- same frozen V2 signal configuration;
- same 60% normalized core assumption;
- same cost model;
- same margin model;
- same July–September dataset;
- same POST_HOC_HOLDOUT / NOT_PRISTINE_OOS status.

No strategy selection may change.

## 14. Phase L.1 acceptance criteria

Phase L.1 passes only if:
- [ ] Phase K artifacts remain preserved.
- [ ] Phase L pre-correction artifacts are preserved.
- [ ] Closed and open slippage are separated.
- [ ] Closed reference P&L reconciles exactly to closed net realized P&L.
- [ ] Open reference MTM reconciles exactly to open terminal contribution.
- [ ] Commission is counted exactly once.
- [ ] Financing is counted exactly once.
- [ ] Total tactical economic contribution reconciles to account equity.
- [ ] The historical slippage mismatch is explicitly explained.
- [ ] Markdown and JSON agree on all headline metrics.
- [ ] No stale contradictory completion-summary numbers remain.
- [ ] Buying-power no-lookahead test actually exercises execution-time acceptance.
- [ ] Margin liquidation test proves next-bar execution.
- [ ] Peak-margin test proves post-transaction debt capture.
- [ ] Full pytest passes.
- [ ] Ruff passes.
- [ ] Historical rerun, if required, is deterministic under the same frozen strategy.
- [ ] No signal parameter changed.
- [ ] No universe or cost parameter changed.
- [ ] Global epistemic statuses remain unchanged.

## 15. Required Gemini final report

Return exactly:
1. Phase K preserved SHA and artifact path.
2. Phase L preserved SHA and artifact path.
3. Phase L.1 corrected commit SHA.
4. Exact accounting defect identified.
5. Exact closed/open slippage decomposition.
6. Exact explanation of the historical mismatch.
7. Before vs after final equity and tactical contribution.
8. Whether ending equity changed.
9. Exact no-lookahead test behavior.
10. Exact margin timing test behavior.
11. Exact peak-margin test behavior.
12. Test count and lint result.
13. Confirmation that no strategy parameter, universe, or cost assumption changed.
14. Remaining research blockers.

## 16. Stop condition

When all Phase L.1 acceptance criteria pass:

STOP SOFTWARE CHANGES.

Do not proceed to parameter sweeps, strategy optimization, covered calls, Level-2 reconstruction, leveraged-product selection, or robustness research.

The next step is a separately approved research-analysis phase.