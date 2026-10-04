# Gemini Coordination Plan — Three Post-L.2 Research Tracks

## Purpose

The engineering/audit freeze is complete.

The next work is research, not additional strategy engineering.

Three tracks now exist:

- Phase M: Frozen prospective OOS validation
- Phase N: V2-D historical covered-call reconstruction
- Phase O: V2-F genuine Level-2 information-set ablation

Detailed execution plans:

1. docs/execution_plan/REDDIT_V2_FROZEN_PROSPECTIVE_OOS_EXECUTION_PLAN.md
2. docs/execution_plan/REDDIT_V2_V2D_OPTIONS_EXECUTION_PLAN.md
3. docs/execution_plan/REDDIT_V2_V2F_LEVEL2_EXECUTION_PLAN.md

## 1. Global research freeze

The accepted historical V2 result is frozen:

- Run ID: 24a9e783
- V2-A: +6.48%
- V2-B: +7.93%
- V2-C: +7.93%
- tactical contribution: +$1,446.69
- historical V2-C peak debt: $0.00

Do not modify these artifacts.

July–September 2026 remains:

POST_HOC_HOLDOUT / NOT_PRISTINE_OOS

Global gates remain:

FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED
TRUE_LEVEL2_REPLICATION = UNVALIDATED
HISTORICAL_OPTION_CHAIN_STATUS = UNVALIDATED
DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2
PRISTINE_OOS = UNAVAILABLE until a genuinely unseen chronological period is executed.

## 2. Dependency/order model

### Stage 1 — Freeze all three research specifications

Before viewing any new performance result, freeze:

- Phase M OOS specification;
- Phase N V2-D option policy;
- Phase O V2-F microstructure policy.

This prevents sequential contamination.

The implementation work for data pipelines may proceed independently.

### Stage 2 — Data acquisition and validation

These can run in parallel:

Phase M:
- future 1-minute MU/SNDK/SKHY data after 2026-09-30.

Phase N:
- authentic historical point-in-time option quotes.

Phase O:
- authentic historical order-book/Level-2 data.

Data-quality validation is allowed before performance evaluation.

Performance-driven parameter selection is not.

### Stage 3 — Pipeline validation

Use the already exposed July–September period only for:

- parsing;
- schema validation;
- deterministic replay;
- event-lifecycle tests;
- no-lookahead tests;
- accounting tests;
- provenance tests.

Do not use its performance to choose parameters.

### Stage 4 — New-data performance

Use the same frozen unseen chronological period wherever the required data exists.

Do not choose the period after seeing returns.

Preferred relationship:

- Phase M = frozen V2 baseline OOS.
- Phase N = same frozen OOS window, V2-C control versus V2-D treatment.
- Phase O = same frozen OOS window, V2-OHLCV control versus V2-Level2 treatment.

If a data source cannot cover the chosen OOS window:
- do not silently switch periods;
- do not mix periods without a separate label;
- report the data gate as incomplete.

## 3. Track ownership

### Phase M — Frozen OOS

Primary question:
Does the existing V2 directional hypothesis generalize?

This is the first result that should influence research interpretation.

Do not use Phase M results to modify V2-D or V2-F rules.

### Phase N — Options

Primary question:
How much economic contribution is plausibly supplied by the covered-call behavior described in the source?

The option policy must be frozen before evaluating the OOS window.

No synthetic option prices.

### Phase O — Level 2

Primary question:
Does actual order-book information add predictive/decision information to the already-frozen V2 sequence?

Primary experiment must be an information-set ablation.

Do not modify the execution cost model in the primary comparison.

## 4. Cross-track contamination rule

Once final OOS performance for any track has been viewed:

- do not change that track's parameters;
- do not use its result to select another track's parameters;
- do not redefine the common OOS window;
- do not retroactively remove unfavorable days;
- do not change cost assumptions.

If a genuine implementation defect is found:
1. preserve the failed run;
2. document the defect;
3. repair it;
4. create a new frozen execution commit;
5. rerun with a new run ID;
6. never overwrite the failed run.

## 5. Cross-track comparison matrix

When all three tracks are complete, produce a single analysis table:

| Track | Control | Treatment | Primary Increment | Status |
|---|---|---|---|---|
| M | V2-A / V2-B / V2-C historical reference | same V2 on unseen data | OOS generalization | SUPPORTIVE / NEUTRAL / CONTRADICTORY / INVALID |
| N | V2-C | V2-D | covered-call contribution | GATED / PARTIAL / VALIDATED |
| O | V2_OHLCV_BASELINE | V2_LEVEL2_MICROSTRUCTURE | information-set contribution | UNVALIDATED / DATA_VALIDATED / ABLATION_VALIDATED |

Do not combine them into a single "full replication" performance number.

## 6. What constitutes meaningful progress

Meaningful progress is not simply a higher return.

The research objective is to identify which of the source-described components have evidence:

1. directional tactical trading;
2. margin/capital rotation;
3. covered calls;
4. Level-2 information.

The correct outcome may be that one or more components do not help.

Negative results must remain preserved.

## 7. Final interpretation gate

Only after M, N, and O are independently preserved may the research team answer:

- Does the directional V2 mechanism generalize?
- Does the covered-call layer add meaningful economics?
- Does genuine Level-2 information add decision value?
- Which source components remain unvalidated?
- Is a partial U.S.-market replication defensible?
- Is the original Reddit trader's reported outcome plausibly explained by the tested components?

Even then:

FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED

remains unchanged unless all required source components and scope have been genuinely validated.

## 8. Final stop condition

After each individual research track:
- preserve artifacts;
- publish completion report;
- stop engineering changes for that track.

After all three:
STOP SOFTWARE CHANGES.

The next step is synthesis and falsification analysis, not further tuning.
