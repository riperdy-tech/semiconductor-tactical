# OOS and Provenance Reconciliation Gate

## Purpose

The first real-data research run used the verified Massive 1-minute dataset, followed by an implementation audit.

The audit fixed the ATR exit-geometry problem and added explicit train/validation/test boundaries. However, two research-integrity issues remain before any result can be presented as a clean final OOS result:

1. The declared September TEST_OOS period was already exposed to the research process by the earlier full-period run.
2. The post-audit report contains configuration and dataset-hash claims that do not match the currently checked-in configuration and manifest.

This document is a reconciliation task, not a strategy-optimization task.

## Problem 1 — September is not a pristine untouched OOS dataset

### What happened

The first genuine Massive comparison was run across the full observed window:

- 2026-07-01 through 2026-09-30

That first run generated the initial historical comparison and performance results.

Only after that run did the repository freeze:

- Start: 2026-07-01
- Train end: 2026-08-15
- Validation end: 2026-09-01
- Test start: 2026-09-01
- End: 2026-09-30

### Why this matters

The September observations are structurally separated from training/validation in the new configuration, but they were not previously unseen by the research process. The full July-September run already exposed the experimenter to September performance before the formal partition was frozen.

Therefore:

> The September segment may be used as a post-hoc holdout / confirmatory analysis, but it must not be described as a pristine, previously unseen final OOS test.

Do not rewrite history to claim otherwise.

### Required action

Gemini must:

1. preserve the original full-period run as historical evidence;
2. preserve the post-audit September result as a POST_HOC_HOLDOUT;
3. update report wording so September is never described as untouched or previously unseen;
4. add an explicit scope label: POST_HOC_HOLDOUT / NOT_PRISTINE_OOS;
5. document that the split was frozen after the full-period result had already been observed;
6. do not use September performance to tune parameters.

### New pristine-OOS requirement

A clean final OOS result requires a period that was not exposed to the experiment before the methodology and parameters were frozen.

The cleanest path is to define a future chronological holdout that occurs after the frozen research specification.

Do not choose the future holdout dates based on observed performance.

If no additional historical period is available, state explicitly:

PRISTINE_OOS_UNAVAILABLE

Do not manufacture a pristine test by relabeling September.

## Problem 2 — Configuration/provenance mismatch

### Reported configuration

The post-audit report states that the formal run used:

- 1-minute resolution
- MU, SNDK, SKHY, AMD, USD
- SMH/SPY benchmarks
- 5.0 bps slippage
- $0.005/share commission
- 8.0% annual margin rate

### Current checked-in configuration

The checked-in configs/historical_1m.yaml currently specifies:

- 1-minute resolution
- MU, SNDK, SKHY, AMD
- USD
- 5.0 bps slippage
- 0.0 bps equity commission
- 5.0% annual margin rate

These are not the same economic assumptions.

### Required action

Gemini must determine which configuration was actually used by the post-audit run.

Do not guess.

Reconstruct the exact run from:

- run_manifest.json
- git commit recorded by the run
- configuration file at that commit
- configuration hash
- local run artifacts if they still exist
- current checked-in configuration

Then document:

1. exact config file;
2. exact config contents;
3. config hash;
4. git commit;
5. economic assumptions actually used.

### Required outcome

There must be exactly one authoritative statement of the run configuration.

If the report was wrong, correct the report/documentation.
If the configuration changed after the run, preserve the historical configuration and explain the change.
Do not silently regenerate a different run and present it as the original run.

## Problem 3 — Dataset aggregate-hash mismatch

### Existing Massive manifest

The committed Massive manifest identifies dataset:

massive_stocks_1m_51e9b529de55

with aggregate SHA-256:

51e9b529de5556002bc3a0e1bc4fd1ee7eef06061b54c11457703d9af39b13e8

### Post-audit report

The post-audit report states the same dataset ID but reports a different aggregate SHA-256:

e0287562eeffad85be361051568548e566ae1e6a01757547dd9ae6c4ad8dc4eb

Those cannot both be the hash of the same exact ordered dataset under the same hashing procedure.

### Required action

Gemini must reconcile the discrepancy.

Inspect:

- data/processed/*.csv
- reports/data_manifests/massive_stocks_1m_51e9b529de55.json
- the post-audit run_manifest.json
- the code that computes aggregate hashes;
- the exact commit used by the post-audit run.

Determine whether:

1. the CSV files changed after the original manifest was generated;
2. the aggregate-hash algorithm changed;
3. the report copied the wrong hash;
4. different files were used;
5. another dataset was accidentally given the same dataset ID.

### Required outcome

There must be one unambiguous mapping:

dataset_id -> exact files -> per-file hashes -> aggregate hash -> research run

If the files changed, create a new immutable dataset ID rather than silently reusing the old ID.

If only the hash algorithm changed, document the algorithm/version and regenerate provenance consistently.

Never overwrite historical evidence.

## Problem 4 — Run-manifest completeness

The current RunManifest stores config/data hashes, symbols, timeframe, seed, and git commit, but the research audit also needs exact OOS boundary metadata.

Gemini should verify whether the actual run manifest contains:

- research start;
- train end;
- validation end;
- test start;
- research end;
- OOS scope classification;
- dataset ID;
- aggregate dataset hash;
- config hash;
- git commit.

If these are missing, add them to the manifest schema and tests.

## Problem 5 — Report terminology must match research history

The final reports must distinguish:

### FULL_SAMPLE

A run across the complete available dataset.

### POST_HOC_HOLDOUT

A later partition that was defined after the full dataset had already been inspected.

### PRISTINE_OOS

A chronological period that was not exposed to strategy evaluation or parameter selection before the research specification was frozen.

Do not use 'untouched OOS' for a period already included in an earlier full-sample run.

## Required implementation sequence

### Step 1 — Freeze evidence

Before modifying code or deleting anything:

- preserve the first full-period report;
- preserve the post-audit report;
- preserve relevant run manifests;
- record current git SHA;
- record current dataset manifest;
- confirm no secrets are tracked.

### Step 2 — Reconcile provenance

Produce a machine-readable reconciliation record containing:

- run ID;
- dataset ID;
- per-file hashes;
- aggregate hash;
- config path;
- config hash;
- git SHA;
- economic assumptions;
- research boundaries;
- scope classification.

### Step 3 — Correct terminology

Change reports/docs so September is explicitly classified as POST_HOC_HOLDOUT unless evidence proves it was genuinely unseen before the research methodology was frozen.

### Step 4 — Resolve configuration mismatch

Either prove that the report's $0.005/share and 8% margin assumptions were the actual run settings and preserve them as the historical configuration, or correct the report to match the actual run.

Do not modify the historical run retroactively.

### Step 5 — Resolve dataset-hash mismatch

Prove exactly which data files produced each hash.

If there is more than one real dataset under the same dataset ID, assign immutable distinct IDs.

### Step 6 — Strengthen manifest/report schema

Ensure formal research artifacts carry:

- exact config hash;
- exact git SHA;
- dataset ID;
- aggregate hash;
- explicit research boundaries;
- explicit OOS classification.

### Step 7 — Test

Run:

.\run.ps1 test

and:

.\.venv\Scripts\python.exe -m ruff check .

Then run data validation against the authoritative dataset.

Do not run parameter optimization.
Do not select a new holdout based on which period performs best.

## Acceptance criteria

- [ ] September is explicitly classified as POST_HOC_HOLDOUT rather than pristine OOS.
- [ ] A genuinely unseen future holdout exists, or the system explicitly states PRISTINE_OOS_UNAVAILABLE.
- [ ] The exact post-audit configuration is proven from run artifacts.
- [ ] Reported commission and margin assumptions reconcile with the actual run.
- [ ] Dataset ID maps to one exact set of files and hashes.
- [ ] Aggregate-hash discrepancy is resolved and documented.
- [ ] Run manifests contain explicit research boundaries.
- [ ] Reports contain explicit scope terminology.
- [ ] First-run evidence remains preserved.
- [ ] No strategy parameters are changed to improve performance.
- [ ] pytest passes.
- [ ] ruff passes.
- [ ] no API key or .env is committed.

## Stop condition

After these reconciliation requirements pass:

STOP SOFTWARE CHANGES.

Do not optimize the strategy.
Do not alter signal thresholds.
Do not alter leverage.
Do not alter costs to improve results.
Do not choose a holdout based on performance.

The next research action is a formally documented OOS experiment using a genuinely unseen chronological period, if one is available.