# Gemini Instruction Package — Phase H Post-Run Research Integrity Correction

## Objective

Correct the research-bookkeeping and interpretation issues identified after Phase H.

**Do not develop a better strategy.**
**Do not tune parameters.**
**Do not rerun experiments for the purpose of improving P&L.**

The current Phase H directional strategy implementation is to remain frozen.

The purpose of this task is to make the research record internally consistent and ensure the reported results mean exactly what the code and preserved artifacts say they mean.

---

# 1. Read first

Read:

1. `AGENTS.md`
2. `docs/REDDIT_SOURCE_NOTES.md`
3. `docs/STRATEGY_SPEC.md`
4. `docs/DECISIONS.md`
5. `docs/execution_plan/REDDIT_STRATEGY_FIDELITY_EXECUTION_PLAN.md`
6. `docs/execution_plan/REDDIT_STRATEGY_FIDELITY_RESULTS_PROTOCOL.md`
7. `docs/CURRENT_MECHANICAL_PULLBACK_BASELINE.md`
8. `docs/REDDIT_STRATEGY_EVIDENCE_MATRIX.md`
9. `docs/execution_plan/REDDIT_STRATEGY_FIDELITY_GAP_AUDIT.md`
10. the Phase H fidelity report and JSON
11. the preserved historical comparison report and JSON
12. `src/tactical_engine/research/fidelity.py`
13. `src/tactical_engine/research/fidelity_runner.py`
14. `src/tactical_engine/backtest/engine.py`
15. `src/tactical_engine/reports/metrics.py`
16. `src/tactical_engine/backtest/state.py`

---

# 2. Hard stop on strategy changes

Before doing anything else:

- Do not change directional signal thresholds.
- Do not change target/stop ATR multiples.
- Do not change trend windows.
- Do not change leverage.
- Do not change trade-frequency controls.
- Do not add new entry/exit predicates.
- Do not add new filters.
- Do not change costs.
- Do not change the sample period.
- Do not search for parameters that improve the reported return.
- Do not search for parameters that better match the reported ~1,300 trades.

The Phase H directional implementation is **frozen for this task**.

The only permitted code changes are those required to correct provenance, experiment labeling, accounting/reporting semantics, or tests proving those semantics.

---

# 3. Correction A — Restore the exact preserved baseline

## Problem

The Phase H runner currently constructs its Experiment 1 baseline from the current config and changes only:

`strategy.variant`

and:

`signals.signal_family`

This means its reported baseline is **not necessarily the exact preserved historical baseline**.

The Phase H report currently labels approximately `-35.69%` as:

`CURRENT_MECHANICAL_PULLBACK_BASELINE`

while `docs/CURRENT_MECHANICAL_PULLBACK_BASELINE.md` preserves the authoritative post-audit risk-controlled result around:

`-92.89%`

with:

- 1.0x leverage;
- 1 layer;
- sector filter disabled;
- exact preserved config hash `0d34835d97140803`;
- run ID `2e9f108d`.

The Phase H result around `-35.69%` is therefore not allowed to overwrite or stand in for the preserved baseline.

## Required action

Create an explicit baseline configuration for the preserved experiment.

The baseline experiment must use the exact economic/strategy assumptions recorded in:

`docs/CURRENT_MECHANICAL_PULLBACK_BASELINE.md`

and must be traceable to the preserved run.

Do not simply copy the current live config and change the variant label.

## Required experiment labels

Use distinct labels:

### `CURRENT_MECHANICAL_PULLBACK_BASELINE`

The immutable preserved historical baseline.

### `MECHANICAL_PULLBACK_SECTOR_FILTERED_DIAGNOSTIC`

Any new diagnostic that happens to use the sector filter but is otherwise mechanical.

### `DIRECTIONAL_FIDELITY_RECONSTRUCTION`

The frozen Phase H directional hypothesis.

Do not conflate these labels.

## Required acceptance test

Add a regression test that verifies the Phase H matrix's baseline configuration exactly matches the preserved baseline configuration.

The test must fail if:

- leverage changes;
- layer count changes;
- sector filter changes;
- costs change;
- universe changes;
- research dates change.

The test should verify the expected config hash or equivalent canonical configuration identity where practical.

---

# 4. Correction B — Reclassify the fidelity conclusion

## Problem

The Phase H report currently says:

> Fidelity Gap Resolved

That wording is too strong.

The source does not disclose a deterministic entry/exit algorithm, exact stop/target values, exact position sizing, or complete option/extended-hours execution details.

## Required wording

Replace the conclusion with language equivalent to:

> **Fidelity Gap Partially Addressed — Deterministic Hypothesis Implemented**

The report must state:

- the original z-score/ATR baseline was a poor proxy for the described discretionary process;
- Phase H introduced a structurally closer deterministic hypothesis;
- the directional hypothesis remains a model approximation, not recovered source code;
- covered calls remain unvalidated;
- extended-hours trading remains unvalidated;
- therefore the Reddit trader's actual strategy P&L has **not** been established.

Do not claim that the source strategy has been reproduced.

---

# 5. Correction C — Parameter provenance gate

## Problem

The directional implementation uses explicit values such as:

- `pullback_min_pct = 0.005`
- `pullback_max_pct = 0.030`
- `stabilization_threshold = 0.35`
- `swing_target_atr = 2.5`
- `swing_stop_atr = 1.5`

These are explicitly labeled hypotheses/assumptions, which is correct.

However, the research record must prove that these were **fixed before evaluating the reported July–September performance**, or else classify the result as post-hoc parameter selection.

## Required action

Create:

`docs/execution_plan/REDDIT_FIDELITY_PARAMETER_PROVENANCE.md`

For every directional parameter, record:

| Parameter | Value | Evidence label | First commit containing value | Date/time | Source of value | Was July–Sep performance already observed? |
|---|---:|---|---|---|---|---|

Use actual git history.

Do not infer dates from memory.

Use commit history to determine when each value entered the repository.

## Required classification

For the Phase H directional result:

### `PRE_SPECIFIED`

Use only when evidence proves the parameter was fixed before the relevant performance evaluation was observed.

### `POST_HOC_SPECIFIED`

Use when the parameter was chosen after the July–September data/result had already been inspected.

### `UNKNOWN`

Use when provenance cannot be demonstrated.

Do not convert `UNKNOWN` into `PRE_SPECIFIED` based on narrative claims.

## Important

If any key directional parameter is `POST_HOC_SPECIFIED` or `UNKNOWN`, do **not** rerun the strategy to search for replacements.

Instead, downgrade the interpretation of the Phase H performance result accordingly.

The goal is provenance, not optimization.

---

# 6. Correction D — Fix P&L terminology and reconciliation

## Problem

The execution engine incorporates slippage directly into fill prices.

Therefore:

`TradeRecord.gross_pnl`

is already based on execution prices containing slippage.

This means the report's use of "gross P&L" can be misleading.

## Required semantic definitions

Implement/report these concepts explicitly:

### Signal-price / pre-slippage P&L

The hypothetical P&L using intended signal/fill prices before modeled execution slippage.

### Execution slippage

The difference attributable to the slippage model.

### Commission

Explicit commissions only.

### Financing

Margin interest / financing costs.

### Net realized P&L

The actual simulated P&L after execution and explicit costs, without double-counting slippage.

## Required action

Do not change the underlying accounting model merely to make the results look better.

Instead:

- expose the attribution clearly;
- rename report fields if necessary;
- document formulas;
- preserve the existing no-double-counting rule.

## Required invariants

For each experiment, the report must reconcile:

`pre_slippage_pnl`
→ minus/plus `slippage_attribution`
→ minus `commission`
→ minus `financing`
→ equals the reported net/equity change to the extent applicable.

The exact formula must be documented in code and tests.

Add regression tests proving:

1. slippage is not deducted twice;
2. commissions are deducted exactly once;
3. financing is separate;
4. reported attribution reconciles with portfolio cash/equity.

Do not invalidate the existing economic result merely because the labels change.

---

# 7. Correction E — Stop-limit wording

## Problem

The source states that the trader used stop limits.

The implementation currently uses stop-limit behavior in the directional hypothesis.

That is a reasonable **HYPOTHESIS**, but the source does not establish that every stop-limit was specifically an entry order.

## Required action

Update the evidence classification to distinguish:

### `OBSERVED`

The trader used stop-limit orders.

### `HYPOTHESIS`

The directional reconstruction uses stop-limit entry mechanics as a proxy.

Do not state that stop-limit entry is the recovered source rule.

No strategy-code change is required.

---

# 8. Correction F — Trade-count plausibility wording

The Phase H result of approximately 1,334 trades is close to the source's reported ~1,300+ trades.

This may be a useful descriptive check, but the proximity itself is **not evidence of fidelity** unless the parameter provenance gate proves the values were pre-specified.

## Required action

Retain trade count as a descriptive diagnostic.

The report must explicitly say:

> The observed similarity in trade count is not treated as validation of the strategy. Trade count was not an optimization target.

If parameter provenance is `POST_HOC_SPECIFIED` or `UNKNOWN`, make the caveat stronger.

Do not alter the strategy to move the trade count.

---

# 9. Correction G — Do not describe 8-minute median holding time as verified swing behavior

The directional result increased median holding time from 2 minutes to approximately 8 minutes.

This is an improvement in the mechanical behavior relative to the old baseline, but it does not establish that the source trader held positions for similar durations.

## Required action

Change wording such as:

> "natural swing frequency"

to:

> "reduced high-frequency churn relative to the baseline"

or equivalent evidence-safe wording.

The source describes scalping and swing trading, but it does not provide a deterministic holding-time distribution.

---

# 10. Correction H — Preserve all existing historical artifacts

Do not delete or overwrite:

- `reports/historical_comparison_fad5c527_20261002_141140/`
- `reports/historical_comparison_2e9f108d_20261002_151405/`
- `reports/fidelity_matrix_5cf918f0_20261003_020151/`
- `docs/CURRENT_MECHANICAL_PULLBACK_BASELINE.md`
- provenance reconciliation artifacts.

If a report is corrected, preserve the prior artifact and write a new corrected report/version.

Do not rewrite historical evidence.

---

# 11. Required documentation changes

Update:

### `docs/CURRENT_MECHANICAL_PULLBACK_BASELINE.md`

Clarify that the preserved baseline remains the authoritative baseline and that later diagnostic baselines are separate.

### `docs/REDDIT_STRATEGY_FIDELITY_RESULTS_PROTOCOL.md`

Add the baseline identity rule, parameter provenance rule, and P&L accounting terminology.

### `docs/REDDIT_STRATEGY_EVIDENCE_MATRIX.md`

Clarify stop-limit entry as a hypothesis rather than observed source behavior.

### `docs/DECISIONS.md`

Add a dated decision documenting:

- baseline identity correction;
- parameter provenance requirement;
- P&L attribution terminology;
- partial rather than complete fidelity status.

---

# 12. Required tests

At minimum add tests for:

1. exact preserved-baseline configuration identity;
2. baseline label separation;
3. parameter provenance metadata presence;
4. slippage attribution reconciliation;
5. no double-counting of slippage;
6. commission reconciliation;
7. financing separation;
8. stop-limit evidence labeling metadata;
9. report terminology / scope classification.

Run:

```
.\\run.ps1 test
.\\run.ps1 doctor
.\\run.ps1 doctor-data -Config configs/historical_1m.yaml -DataDir data/processed
.\\.venv\\Scripts\\python.exe -m ruff check .
```

---

# 13. Required final report from Gemini

Return:

1. files changed;
2. tests added;
3. tests passed;
4. exact preserved-baseline identity and config hash;
5. Phase H parameter provenance table;
6. classification of each key parameter: `PRE_SPECIFIED`, `POST_HOC_SPECIFIED`, or `UNKNOWN`;
7. corrected P&L terminology/formulas;
8. confirmation that no strategy parameters were changed;
9. confirmation that no performance rerun was used to search for better parameters;
10. remaining limitations.

---

# 14. Definition of done

This task is complete when:

- [ ] the original preserved baseline is the only experiment labeled `CURRENT_MECHANICAL_PULLBACK_BASELINE`;
- [ ] the Phase H diagnostic result is not mislabeled as the preserved baseline;
- [ ] parameter provenance is established from git history;
- [ ] any post-hoc/unknown provenance is explicitly disclosed;
- [ ] P&L/slippage/commission/financing terminology reconciles mathematically;
- [ ] stop-limit entry is classified as a hypothesis, not an observed source rule;
- [ ] 8-minute holding time is not described as validated swing behavior;
- [ ] all historical artifacts remain preserved;
- [ ] no strategy parameters were changed;
- [ ] no optimization rerun was performed;
- [ ] tests pass;
- [ ] ruff passes.

---

# 15. Mandatory stop condition

After these corrections pass:

**STOP SOFTWARE CHANGES.**

Do not:

- tune the directional strategy;
- search for alternative thresholds;
- optimize trade count;
- search for parameters that produce positive P&L;
- use September performance as tuning data;
- claim the Reddit strategy has been reproduced.

The next research step, if any, is external data acquisition for the currently unvalidated components:

1. historical option-chain data;
2. verified extended-hours / foreign-session data.

Until those data gates are satisfied, the repository must continue to state:

`FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED`

and:

`PRISTINE_OOS = UNAVAILABLE`
