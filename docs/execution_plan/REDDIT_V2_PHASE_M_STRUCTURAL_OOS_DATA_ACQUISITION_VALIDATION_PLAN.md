# Reddit V2 Phase M — Structural OOS Data Acquisition & Validation Only

**Status:** READY  
**Precondition:** Phase M.1.4 accepted / engineering layer frozen  
**Purpose:** Acquire and structurally validate newly available OOS data without executing or inspecting strategy performance  
**Prior accepted prospective run:** `bb0887e4`  
**Prior accepted prospective endpoint:** `2026-10-02T19:59:00Z`

## 1. Objective

Acquire and validate the next genuinely new chronological U.S.-market data block for the frozen Reddit Behavioral V2 experiment.

This phase is **data acquisition and structural validation only**.

It is not a performance run, strategy-development phase, tuning phase, or parameter-selection phase.

The purpose is to establish whether a sufficiently complete, clean, non-overlapping continuation dataset exists for the eventual frozen 20-session Phase M performance run.

## 2. Hard research-integrity rules

Do not:

- execute V2-A;
- execute V2-B;
- execute V2-C;
- inspect trade-level P&L or performance output;
- calculate strategy returns for the new data;
- use the new data to modify any strategy parameter;
- change the frozen OOS config;
- change the 60% core allocation;
- change MU/SNDK/SKHY scope;
- change tactical sizing;
- change cost, slippage, financing, or margin assumptions;
- alter execution semantics;
- rerun `bb0887e4`;
- merge the new data into `bb0887e4`;
- overwrite any accepted artifact.

Allowed work is limited to:

- data acquisition;
- structural validation;
- chronology validation;
- coverage/session validation;
- missing-bar diagnostics;
- duplicate/overlap detection;
- provenance/hash generation;
- deterministic data-manifest creation;
- documentation of validation results.

If a mechanical data defect is discovered, preserve the existing evidence, document the defect, and do not make a performance-driven repair.

## 3. Chronology gate

The prior accepted prospective endpoint is:

`2026-10-02T19:59:00Z`

Every newly acquired OOS bar must satisfy:

`bar.timestamp > 2026-10-02T19:59:00Z`

Reject any bar that is:

- at or before the prior endpoint;
- duplicated;
- chronologically out of order;
- silently stitched across the prior endpoint.

Do not backfill July–September 2026 data into the continuation calculation.

The existing `bb0887e4` dataset and artifacts remain immutable.

## 4. Universe and market-data scope

Structural validation is limited to the frozen headline universe:

- MU
- SNDK
- SKHY

Use the same accepted OOS data conventions:

- U.S. market;
- 1-minute bars;
- America/New_York reporting convention;
- regular trading hours only for the headline validation;
- same adjustment/split policy as the accepted OOS dataset.

Do not add:

- KXIAY;
- leveraged ETFs;
- USD;
- KRX instruments;
- Tokyo-listed instruments;
- options;
- Level-2/order-book data.

Those remain separate research tracks.

## 5. Data acquisition rule

Acquire all **completed and actually available** new sessions from the accepted endpoint onward.

Do not assume a calendar date is complete merely because it is the current date.

A session is considered complete only when the source data itself demonstrates the full expected regular-session coverage for MU, SNDK, and SKHY under the existing data contract.

Therefore:

- partial/in-progress sessions may be acquired for staging if operationally useful;
- partial/in-progress sessions must not count toward the complete-session threshold;
- partial/in-progress sessions must not enter a frozen performance run;
- no performance calculation is permitted in this phase.

## 6. Session-count gate

The Phase M research protocol requires **20 complete U.S. regular-trading sessions** before the next performance run.

Count only sessions that satisfy all three headline symbols' structural completeness requirements.

Interpretation:

- **0–19 complete sessions:** structural validation only; STOP.
- **20+ complete sessions:** the dataset is eligible for the separately authorized frozen continuation performance run, but this package still does **not** authorize that run.
- Do not shorten the threshold.
- Do not combine `bb0887e4`'s two sessions with the new continuation block.
- Do not select a smaller or more favorable sub-window.

## 7. Structural validation checklist

Validate and report:

### Dataset identity

- source/provider;
- dataset ID;
- retrieval timestamp;
- resolution;
- timezone;
- adjustment/split policy;
- source version or manifest identifier when available.

### Symbol coverage

For MU, SNDK, and SKHY:

- first new timestamp;
- last new timestamp;
- row count;
- complete-session count;
- expected-vs-observed RTH coverage;
- missing-bar count;
- duplicate-bar count;
- timestamp monotonicity;
- any session-level gaps.

### Chronology integrity

Verify:

- first eligible bar is strictly after `2026-10-02T19:59:00Z`;
- no overlap with `bb0887e4`;
- no duplicate timestamps;
- no backward timestamps;
- no pre-cutoff bars;
- no July–September contamination;
- no silent backfill.

### Cross-symbol integrity

For each completed session:

- MU present;
- SNDK present;
- SKHY present;
- no symbol is selectively omitted because of adverse data;
- synchronized session boundaries remain compatible with the accepted data contract.

### Hashes and provenance

Generate:

- per-symbol SHA256;
- aggregate SHA256;
- manifest identifier;
- validation execution commit SHA;
- exact data paths used.

## 8. Required artifact

Create or update a structural manifest under:

`reports/data_manifests/`

Use a new identifier, for example:

`v2_oos_structural_<id>_manifest.json`

The manifest must contain at minimum:

- source;
- dataset ID;
- symbols;
- resolution;
- timezone;
- adjustment policy;
- prior accepted OOS endpoint;
- first eligible timestamp;
- last validated timestamp;
- per-symbol row counts;
- complete-session count;
- missing-bar diagnostics;
- duplicate diagnostics;
- per-symbol SHA256;
- aggregate SHA256;
- retrieval timestamp;
- validation commit SHA;
- explicit statement that **no performance calculation was performed**.

Do not overwrite the historical `bb0887e4` manifest.

## 9. Required validation commands

Run only the deterministic structural checks required by the repository, including as applicable:

`run.ps1 doctor-data -DataDir data/processed_oos -Config configs/v2_oos_frozen.yaml`

and any existing non-performance dataset/manifest integrity checks required by the repository.

Also verify:

- frozen YAML SHA remains
  `be21c7dc0f998cf21310ffb5ffeae39fe039046d80aaa4ee4c656189f44f502a`;
- no strategy parameter file was modified;
- no accepted report was overwritten;
- git working tree is clean after documentation/manifest commit.

Do **not** run:

- `fidelity-v2-oos`;
- any V2-A/B/C performance command;
- the historical performance runner;
- any optimization/grid-search command.

## 10. Blindness requirement

The operator must not use strategy performance to determine:

- which dates to include;
- which sessions to exclude;
- which symbols to exclude;
- whether to stop at a particular date;
- whether to repair the dataset;
- which configuration to run later.

Data inclusion decisions must be based only on deterministic structural rules defined above.

## 11. Completion classifications

Use exactly one of these structural classifications:

### `PHASE_M_STRUCTURAL_OOS_INSUFFICIENT_SAMPLE`

Use when fewer than 20 complete sessions are available.

Required conclusion:

> Structural OOS data is valid/usable for continued accumulation, but the preregistered 20-session minimum has not been met. No performance run was executed.

### `PHASE_M_STRUCTURAL_OOS_PERFORMANCE_GATE_READY`

Use when at least 20 complete sessions are available and all structural/provenance gates pass.

Required conclusion:

> Structural OOS data satisfies the preregistered performance-entry gate. No performance run was executed in this phase. A separate frozen continuation execution is required.

### `PHASE_M_STRUCTURAL_OOS_INVALID`

Use when chronology, provenance, universe, coverage, or data-quality gates fail.

Required conclusion:

> Structural OOS data failed validation. No performance run was executed.

## 12. Gemini completion report

Return:

1. structural validation classification;
2. dataset/source;
3. dataset ID;
4. exact validated date range;
5. first eligible timestamp;
6. last validated timestamp;
7. complete-session count;
8. MU row count and coverage;
9. SNDK row count and coverage;
10. SKHY row count and coverage;
11. missing/duplicate diagnostics;
12. chronology/overlap result;
13. per-symbol SHA256;
14. aggregate SHA256;
15. frozen-config SHA;
16. validation commit SHA;
17. exact manifest path;
18. explicit statement: **NO PERFORMANCE RUN EXECUTED**;
19. explicit statement: **NO PARAMETERS OR STRATEGY LOGIC CHANGED**.

Do not report V2-A/B/C returns because they are not to be calculated in this phase.

## 13. Final stop state

After structural validation:

**STOP.**

Do not automatically continue into the performance phase even if the 20-session gate is satisfied.

The structural-validation artifact must be preserved first.

If fewer than 20 complete sessions exist, wait for genuinely new completed chronology before repeating this structural gate.

If 20+ complete sessions exist and all gates pass, report `PHASE_M_STRUCTURAL_OOS_PERFORMANCE_GATE_READY` and stop. The separate frozen continuation performance package must then be explicitly executed once.
