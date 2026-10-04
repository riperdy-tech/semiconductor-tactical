# Gemini Execution Plan — Reddit Behavioral V2 Post-Run Audit & Accounting Correction (Phase L)

## Objective

Audit the completed Phase K V2 historical implementation and correct any research-validity defects exposed by the first V2-A/B/C run.

This is NOT a strategy-improvement phase.

The purpose is to make the existing V2 result economically and statistically interpretable without changing the frozen Reddit-inspired behavioral parameters.

The current historical result remains preserved as evidence. Do not delete, overwrite, or silently regenerate prior artifacts.

## Hard stop / research-integrity rules

For Phase L:

- Do not optimize any signal parameter.
- Do not grid-search impulse lookback, impulse magnitude, pullback depth, stabilization bars, scale-out, stop mode, or tactical sizing.
- Do not change the 60% normalized core allocation to improve the result.
- Do not add or remove symbols to improve P&L.
- Do not alter execution costs to improve P&L.
- Do not force margin usage in the historical strategy merely to make V2-C differ from V2-B.
- Do not fit anything to the reported $550k result or ~1,300 trades.
- July–September 2026 remains POST_HOC_HOLDOUT / NOT_PRISTINE_OOS.
- Covered calls remain blocked.
- True Level-2 replication remains blocked.
- Direct KRX/Tokyo execution remains out of scope.
- Any rerun after correction must use the exact same frozen V2 directional parameters unless a defect requires a mechanically necessary correction.

## 1. Read first

Read:

1. AGENTS.md
2. docs/REDDIT_SOURCE_NOTES.md
3. docs/REDDIT_BEHAVIORAL_V2_EVIDENCE_MATRIX.md
4. docs/REDDIT_V2_DIRECTIONAL_BEHAVIOR.md
5. docs/execution_plan/REDDIT_V2_END_TO_END_IMPLEMENTATION_PLAN.md
6. docs/execution_plan/REDDIT_V2_HISTORICAL_RUN_PROTOCOL.md
7. docs/execution_plan/REDDIT_V2_PARAMETER_REGISTRY.md
8. src/tactical_engine/backtest/v2_engine.py
9. src/tactical_engine/execution/simulator.py
10. src/tactical_engine/portfolio/v2_portfolio.py
11. src/tactical_engine/signals/v2_signals.py
12. src/tactical_engine/research/v2_historical_runner.py
13. reports/V2_HISTORICAL_COMPARISON.md
14. reports/v2_historical_comparison.json
15. the checked-in Massive dataset manifest and prior run artifacts.

Also inspect the exact Phase K commit and git diff used for the historical result.

## 2. Preserve the current Phase K evidence

Before modifying code:

- preserve reports/V2_HISTORICAL_COMPARISON.md;
- preserve reports/v2_historical_comparison.json;
- preserve the Phase K run ID;
- preserve dataset ID and aggregate SHA;
- record the exact pre-audit git SHA;
- record the exact frozen V2 signal configuration;
- record the exact historical period reported by Phase K.

Create an audit note that clearly distinguishes:

PHASE_K_REPORTED_RESULT

from:

PHASE_L_CORRECTED_RESULT

Do not overwrite the original result in place.

## 3. Phase L-A — Audit the true evaluation start and core initialization

Inspect the current V2 core initialization carefully.

The current implementation waits until a timestamp contains all three headline symbols and then initializes the persistent core at that bar's open. This behavior must be made explicit because SKHY has a later historical start than MU/SNDK.

Required outcome:

- determine the first common timestamp where MU, SNDK, and SKHY all have valid bars;
- call this the V2 effective_start_timestamp;
- do not backfill or forward-fill SKHY;
- do not claim the core was active before the common-start timestamp;
- report the pre-core interval as UNINITIALIZED / NOT_IN_SAMPLE or make the effective evaluation start equal to the first common bar;
- report the exact effective start timestamp in JSON and Markdown.

### Core starting-state semantics

Choose and document one consistent interpretation.

Preferred interpretation:

The 60% core is an exogenous normalized starting state at the effective start timestamp, not a historical trade reconstructed from the first bar.

Under that interpretation:

- initial cash is $100,000;
- 60% of initial equity is converted into equal-notional MU/SNDK/SKHY core positions using the effective-start reference price;
- the remaining 40% is initial tactical/liquidity cash;
- the starting-state establishment itself is not counted as strategy P&L;
- no execution slippage should be charged to creating the normalized initial state;
- any share-rounding residual must be recorded explicitly;
- the report must show actual core starting value and actual residual cash, not merely the nominal 60%.

If the implementation instead chooses to model the initial core as a real transaction, route it through the same execution-cost semantics as every other transaction and document that choice. Do not mix the two interpretations.

### Required diagnostics

Report:

- effective start timestamp;
- per-symbol initial reference price;
- target notional per symbol;
- actual shares;
- actual starting notional per symbol;
- actual core percentage of initial equity;
- residual cash;
- whether starting-state costs were applied;
- whether starting-state P&L is excluded.

Add a regression test proving no data after the effective start can affect initial core quantity or starting allocation.

## 4. Phase L-B — Audit execution-price vs reference-price semantics

Inspect ExecutionSimulator and Fill semantics.

Determine exactly:

- what fill.price represents;
- what fill.slippage represents;
- whether slippage is already embedded in fill.price;
- whether a raw/reference execution price is available;
- how market-order fills are priced at the next bar.

Do not guess.

### Required accounting definitions

The V2 report must distinguish:

1. reference/gross P&L — P&L using the unadjusted execution reference price;
2. execution slippage — explicit slippage cost;
3. commissions;
4. financing;
5. net realized P&L.

If fill.price already includes slippage, then:

- actual realized P&L should use fill.price;
- the pre_slippage_pnl field must not be calculated from fill.price;
- pre_slippage_pnl must use the unadjusted reference price;
- slippage must not be subtracted a second time from actual account equity.

If the simulator does not expose a raw/reference price, add a deterministic field to the fill/execution layer rather than reverse-engineering it from already-adjusted prices.

### Critical invariant

The following relationship must be mechanically testable:

net trade P&L = reference/gross P&L - execution slippage - commissions

and account-level:

ending equity - initial equity + withdrawals = economic net account P&L

with financing separately identified.

Do not double-count slippage.

## 5. Phase L-C — Correct the misleading pre_slippage_pnl metric

The current V2 trade record appears to calculate pre_slippage_pnl from execution prices. Audit this directly.

If confirmed:

- fix the field semantics;
- preserve realized_pnl as execution-price-based net trade P&L with clearly defined cost treatment;
- calculate pre_slippage_pnl from reference prices;
- update report labels and docstrings;
- add a regression test where non-zero slippage makes pre_slippage_pnl differ from execution-price P&L by exactly the slippage amount.

The test must fail under the current misleading implementation and pass after correction.

Do not change the slippage rate.

## 6. Phase L-D — Audit the tactical contribution calculation

The current headline tactical contribution is approximately:

+$902 / +0.90%

with both realized tactical P&L and terminal tactical unrealized P&L contributing to the result.

Report these separately:

- closed tactical round-trip net P&L;
- ending open tactical mark-to-market P&L;
- total tactical economic contribution;
- tactical transaction costs;
- tactical financing, if any.

Do not remove terminal mark-to-market. It is a legitimate component of ending equity.

However, make it impossible to confuse:

closed-trade performance

with:

total tactical sleeve contribution including open inventory.

### Required trade-state diagnostics

Report separately:

- signal count;
- order count;
- order attempts;
- entry fills;
- reload fills;
- partial-exit fills;
- full-exit fills;
- completed FIFO trade records;
- open tactical lots at period end;
- open tactical shares/notional at period end.

Explain any difference between entry fills and completed round trips.

## 7. Phase L-E — Audit no-lookahead in capital and margin checks

Inspect every use of latest_prices, portfolio equity, and buying power around pending-order execution.

The required timing contract is:

bar t close -> signal/order decision -> bar t+1 open execution

Execution-time risk checks must use information available at execution time.

### Specific audit target

The current V2 engine updates latest_prices with the current bar's close before executing pending orders. If buying-power or capacity checks for a pending order use those close prices, that is lookahead because the order is filled at the current bar open.

Required correction:

- execution-time buying-power checks must use prices available at the actual fill timestamp;
- for next-bar-open market fills, use the execution/reference open/fill price or an equivalent non-lookahead valuation;
- do not use the current bar's closing price for an order that is being filled at that same bar's open.

Add a regression test that changes the current bar's close while holding the current bar's open fixed and proves the accept/reject decision for a next-open order is unchanged.

## 8. Phase L-F — Audit margin-call timing

Review V2-C margin-call detection and forced liquidation.

Required no-lookahead semantics:

- margin status may be evaluated using a completed bar close;
- a liquidation decision made at bar t close must not execute against bar t's already-known close;
- liquidation should be scheduled for the next eligible execution timestamp under the defined execution model.

Do not engineer a historical margin call.

Add a synthetic unit test proving that a margin call detected on bar t results in execution no earlier than the permitted next execution point.

## 9. Phase L-G — V2-C margin result interpretation

Do not alter the historical V2-C sizing just to force debt.

The fact that:

V2-C = V2-B

with:

- peak margin debt = $0;
- margin interest = $0;

is a legitimate historical outcome if the tactical sleeve never required borrowing.

Report V2-C as:

MARGIN CAPABILITY PRESENT / HISTORICAL MARGIN NOT EXERCISED

not as evidence that leverage had no strategic effect in general.

### Separate capability test

Add a synthetic unit/integration test that deliberately creates a cash-constrained V2-C purchase and verifies:

- margin debt increases correctly;
- financing interest accrues;
- buying power is respected;
- maintenance ratio is respected;
- forced liquidation logic preserves tactical-first priority.

This synthetic test is for engine validation only.

Do not use it to create or justify a different historical strategy result.

## 10. Phase L-H — Audit margin debt accounting timing

Confirm peak_margin_debt is sampled after all transactions and financing effects that can change debt on a timestamp, not only before pending-order execution.

Add a regression test where a transaction creates debt at time t and assert that reported peak debt includes that amount.

No performance-related behavior may change.

## 11. Phase L-I — Audit core isolation and attribution

Preserve the invariant:

tactical exits cannot reduce persistent core inventory

unless a separately documented margin liquidation rule is triggered.

Verify:

- tactical stop/partial/full reductions only touch tactical inventory;
- core P&L is never contaminated by tactical entry/exit accounting;
- V2-A and V2-B use the same frozen core path;
- core ending value is independently reconstructable from core shares and terminal prices.

Report:

- core realized P&L;
- core unrealized P&L;
- tactical realized P&L;
- tactical unrealized P&L;
- total costs;
- final equity.

## 12. Phase L-J — Accounting reconciliation must be explicit

Replace ambiguous documentation with an explicit layered reconciliation.

Recommended reporting structure:

### Reference layer
gross_reference_PnL

### Execution layer
less_slippage
less_commissions

### Financing layer
less_margin_interest

### Economic net layer
net_realized_PnL
plus_terminal_unrealized_PnL
equals_total_net_account_PnL

The implementation may use a slightly different algebra if it is mathematically equivalent, but every component must be counted exactly once.

Add a reconciliation test with non-zero slippage, non-zero commission, and non-zero margin interest.

## 13. Phase L-K — Historical report corrections

Update reports/V2_HISTORICAL_COMPARISON.md and JSON output so that they explicitly include:

- Phase K original result;
- Phase L corrected result;
- effective evaluation start;
- actual starting core percentage;
- residual cash after integer-share rounding;
- reference/gross P&L;
- slippage;
- commissions;
- financing;
- closed tactical P&L;
- open tactical terminal P&L;
- total tactical contribution;
- entry/order/fill/round-trip counts;
- ending open tactical inventory;
- margin status: exercised or not exercised.

Do not suppress the original Phase K numbers.

If the corrected accounting changes the +6.48% / +7.38% result, show both values and explain exactly why.

If the result does not change, state:

PHASE_L_ACCOUNTING_CORRECTION_DID_NOT_CHANGE_ENDING_EQUITY

and show the audit evidence.

## 14. Phase L-L — Provenance and reproducibility

The corrected report must persist:

- git SHA;
- dataset ID;
- dataset aggregate SHA;
- V2 manifest/hash;
- exact V2 signal parameters;
- effective start timestamp;
- historical period;
- evaluation classification;
- universe;
- cost configuration;
- margin configuration;
- runner/config hash.

Never silently mutate the Phase K artifact.

## 15. Phase L-M — Tests

Add focused tests for:

1. effective common-start initialization;
2. no-lookahead core initialization;
3. raw/reference price vs execution price;
4. pre_slippage_pnl correctness;
5. slippage counted exactly once;
6. commission counted exactly once;
7. financing counted exactly once;
8. tactical closed vs open attribution;
9. entry/fill/round-trip/open-lot count reconciliation;
10. next-open buying-power no-lookahead;
11. next-open margin liquidation semantics;
12. peak margin debt sampled after transactions;
13. core isolation;
14. V2-A/B same core path;
15. synthetic V2-C margin activation.

## 16. Phase L-N — Verification commands

Run at minimum:

.\\run.ps1 test

.\\run.ps1 doctor

.\\run.ps1 doctor-data -Config configs/historical_1m.yaml -DataDir data/processed

.\\.venv\\Scripts\\python.exe -m ruff check .

Then run the same frozen historical command:

.\\run.ps1 fidelity-v2-historical

Only rerun because of implementation/accounting correction.

Do not change the V2 candidate parameters.

## 17. Phase L-O — Acceptance criteria

Phase L passes only if all of the following are true:

- [ ] Phase K artifacts preserved.
- [ ] Effective evaluation start is explicit and reproducible.
- [ ] No pre-common-SKHY period is silently treated as active three-symbol core exposure.
- [ ] Core starting-state semantics are explicit and internally consistent.
- [ ] pre_slippage_pnl is based on unadjusted reference prices.
- [ ] Slippage is not double-counted.
- [ ] Commissions are not double-counted.
- [ ] Financing is not double-counted.
- [ ] Tactical closed P&L and terminal open P&L are separately reported.
- [ ] Entry fills, exit fills, round trips, and open lots are separately reported.
- [ ] Pending-order buying-power checks contain no close-price lookahead.
- [ ] Margin liquidation contains no same-bar close-to-fill lookahead.
- [ ] Peak margin debt includes intra-timestamp transaction effects.
- [ ] Core inventory remains isolated from ordinary tactical exits.
- [ ] Synthetic margin activation test passes.
- [ ] Full test suite passes.
- [ ] Ruff passes.
- [ ] fidelity-v2-historical reproduces deterministically under the frozen configuration.
- [ ] No strategy parameter was tuned.
- [ ] No universe was expanded for performance.
- [ ] Global epistemic statuses remain unchanged.

## 18. Required final Gemini report

Return:

1. exact files changed;
2. exact Phase K SHA preserved;
3. exact Phase L corrected commit SHA;
4. tests added;
5. tests passed;
6. exact effective start timestamp;
7. exact core initialization semantics;
8. exact reference-price/slippage semantics;
9. whether pre_slippage_pnl was wrong and how it was corrected;
10. Phase K vs Phase L performance comparison;
11. whether V2-C margin was actually exercised historically;
12. synthetic margin test result;
13. exact accounting reconciliation;
14. dataset ID and aggregate SHA;
15. exact frozen signal parameters;
16. confirmation that no strategy parameter was optimized;
17. remaining blockers.

## 19. Stop condition

When Phase L acceptance criteria pass:

STOP SOFTWARE CHANGES.

Do not proceed to parameter sweeps, robustness optimization, covered calls, Level-2 replication, or strategy redesign in this phase.

The next step is a separately approved research-analysis phase that interprets the corrected V2 result and decides whether a genuine unseen OOS experiment is worth constructing.
