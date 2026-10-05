# Reddit V2 — Prospective OOS Continuation Execution Plan

**Status:** READY FOR NEXT GENUINE OOS OBSERVATION  
**Precondition:** Phase M.1.4 accepted  
**Control:** Frozen V2 / Run `24a9e783`  
**Prior prospective run:** `bb0887e4`

## 1. Objective

Continue Phase M using genuinely new chronological U.S.-market data after the accepted endpoint of `bb0887e4`.

The question is unchanged:

> Does the already-frozen Reddit Behavioral V2 directional/core/margin hypothesis generalize to unseen U.S.-market data after 2026-09-30?

This is **not** a strategy-development, tuning, or optimization phase.

## 2. Non-negotiable research rules

Do not:

- change any V2 signal parameter;
- change the 60% core allocation;
- change MU/SNDK/SKHY scope;
- change tactical sizing;
- change costs, margin, slippage, or financing;
- change execution semantics;
- add KXIAY, leveraged ETFs, USD, Asia-listed instruments, options, or Level-2 to the headline experiment;
- use new OOS P&L to select parameters;
- rerun `bb0887e4` merely because its result is short or unfavorable;
- overwrite an accepted artifact.

A data-quality or mechanical reproducibility defect may be repaired only if it is demonstrably independent of performance. Preserve the affected run and use a new run ID.

## 3. Chronology gate

The accepted `bb0887e4` endpoint is:

`2026-10-02T19:59:00Z`

Any continuation dataset must satisfy:

`first_eligible_timestamp > 2026-10-02T19:59:00Z`

and, more generally:

`all_bars > prior_accepted_oos_endpoint`

No bar from July–September 2026 may enter the new return calculation.

Do not silently backfill or stitch overlapping bars into the continuation window.

## 4. Minimum-information gate

Phase M's preregistered minimum sample is **20 complete U.S. regular-trading sessions**.

Therefore:

- if the newly available chronology contains fewer than 20 complete sessions beyond the accepted endpoint, perform data acquisition/validation only and **STOP WITHOUT A NEW PERFORMANCE RUN**;
- once at least 20 complete sessions are available, execute one frozen continuation run;
- do not shorten the required sample because the observed result is interesting;
- do not extend or shift the window because the observed result is unfavorable.

The two-session `bb0887e4` result remains preserved and is not retroactively combined into a new backtest.

## 5. Continuation runner requirements

Use the canonical continuation path introduced by M.1.3/M.1.4.

Supply explicit:

- `--prior-oos-run-id bb0887e4`;
- `--prior-oos-end-timestamp 2026-10-02T19:59:00Z`;
- `--start <new-window-start>`;
- `--end <new-window-end>`.

The continuation path must not apply the initial frozen-boundary equality rule to the new start.

The continuation start must nevertheless be strictly after:

- the historical cutoff;
- the prior accepted OOS endpoint.

The continuation end must be strictly after its start.

## 6. Data gate before performance inspection

Before looking at strategy P&L, verify only structural information:

- source and dataset identity;
- MU/SNDK/SKHY availability;
- timestamps and timezone;
- complete-session count;
- RTH coverage;
- missing-bar diagnostics;
- per-symbol and aggregate hashes;
- adjustment policy;
- no duplicated or overlapping chronology;
- no contaminated pre-cutoff bars.

Do not inspect trade-level or P&L output and then alter the data window.

## 7. Frozen strategy gate

Before execution, verify the existing parameter fingerprint and control state:

- impulse lookback = 30 bars;
- impulse magnitude = 2.0%;
- pullback depth = 0.500;
- stabilization = 5 bars;
- tactical scale-out = 50%;
- LOCAL_LOW stop logic;
- frozen stop buffer;
- frozen rebound target;
- frozen 60% core;
- MU/SNDK/SKHY equal-notional core;
- no monthly rebalance;
- exact accepted V2-C margin mechanism;
- exact accepted costs.

If any mismatch appears, **STOP**. Do not repair the mismatch by editing the frozen strategy after seeing data.

## 8. Execution

When the 20-session gate is satisfied:

Run V2-A, V2-B, and V2-C once using the frozen continuation configuration.

Preserve:

- run ID;
- execution code SHA;
- artifact-content commit SHA;
- provenance-finalization SHA;
- dataset manifest and aggregate SHA;
- exact start/end;
- prior-run lineage;
- config/fingerprint hashes.

Do not perform a second performance run to improve the result.

## 9. Required outputs

The continuation artifact must report at minimum:

### Performance
- start/end equity;
- net return;
- maximum drawdown;
- daily return series;
- volatility;
- Sharpe;
- Sortino;
- profit factor.

### Core
- core starting value;
- ending value;
- realized/unrealized P&L.

### Tactical
- closed P&L;
- terminal open P&L;
- total tactical contribution;
- trade count;
- win rate;
- expectancy;
- holding times;
- entries/reloads/exits;
- open inventory.

### Margin
- peak debt;
- financing;
- margin calls;
- liquidations.

### Behavior
- trades/day;
- trades/symbol/day;
- simultaneous exposure;
- turnover;
- gross exposure;
- average position size.

## 10. Scientific comparisons

Primary comparison A:

**V2-B minus V2-A**

Does tactical trading add value beyond the same static core?

Primary comparison B:

**V2-C minus V2-B**

Does the existing margin mechanism add value or risk?

Behavioral comparison:

Compare the continuation period with accepted historical V2 and `bb0887e4` on:

- tactical contribution;
- trade frequency;
- holding time;
- drawdown;
- exposure;
- symbol concentration.

Similarity is descriptive, not an optimization target.

## 11. Interpretation discipline

Use the existing preregistered classes:

- **SUPPORTIVE** — positive evidence from genuinely unseen data while remaining behaviorally plausible;
- **NEUTRAL / INCONCLUSIVE** — insufficient or ambiguous evidence;
- **CONTRADICTORY** — material evidence against the tactical hypothesis;
- **INVALID** — provenance, data-quality, configuration, or no-lookahead gate failure.

Do not declare the Reddit strategy validated from one continuation window.

## 12. Required preservation

Create:

- `reports/data_manifests/v2_oos_<new_id>_manifest.json`;
- `reports/v2_oos/<new_run_id>.json`;
- `reports/v2_oos/<new_run_id>.md`;
- a preservation note under `reports/fidelity_runs/v2_oos_<new_run_id>/`.

Never overwrite `bb0887e4` or the historical control `24a9e783`.

## 13. Verification

Before execution:

- `python -m pytest`;
- Ruff;
- `run.ps1 test`;
- `run.ps1 doctor`;
- `run.ps1 doctor-data -DataDir data/processed_oos -Config configs/v2_oos_frozen.yaml`.

After execution, verify:

- new run ID differs from `bb0887e4`;
- continuation chronology is strictly forward;
- frozen config remains byte-identical;
- parameter fingerprint remains unchanged;
- prior artifacts remain byte-identical;
- machine-readable JSON and Markdown agree.

Do not run the old historical-performance command.

## 14. Stop conditions

STOP immediately if:

- fewer than 20 complete sessions are available;
- any continuation bar overlaps the prior accepted endpoint;
- configuration fingerprint differs;
- a headline symbol is missing or structurally invalid;
- provenance is incomplete;
- a performance-driven window change is proposed;
- any parameter is changed after OOS data exposure;
- an attempt is made to overwrite an accepted artifact.

## 15. Gemini completion report

Return:

1. new run ID;
2. exact OOS start/end;
3. complete-session count;
4. data source and dataset ID;
5. per-symbol coverage;
6. aggregate SHA;
7. config/fingerprint hashes;
8. execution code SHA;
9. artifact-content commit SHA;
10. provenance-finalization SHA;
11. V2-A/B/C results;
12. tactical contribution;
13. peak margin debt;
14. behavioral comparison;
15. interpretation class;
16. exact test/Ruff/doctor results;
17. explicit statement that no performance tuning occurred;
18. exact artifact paths.

## 16. Final stop state

After one valid continuation performance run:

**STOP SOFTWARE CHANGES.**

Preserve the observation before any cross-track interpretation.

Do not use the continuation result to tune Phase N or Phase O.
