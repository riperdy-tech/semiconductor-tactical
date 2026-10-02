# Gemini Final Handoff

Execute `docs/execution_plan/FINAL_GATE_FIX.md`.

After that, stop software implementation unless a failing acceptance test exposes a real defect.

## Do not

- acquire market data;
- fabricate market data;
- fabricate option chains;
- change strategy parameters for performance;
- optimize against the Reddit result;
- declare historical research complete.

## Then prepare the repository for data ingestion

Use `docs/execution_plan/DATA_ACQUISITION.md` as the data contract and operator guide.

The software endpoint is:

```
Verified 1-minute equity data
        |
        v
Data manifest + hashes
        |
        v
Data doctor / cadence / corporate-action checks
        |
        v
Train / validation / untouched OOS split
        |
        v
3 variants:
  literal_clone
  risk_controlled
  regime_adapted
        |
        v
Final OOS robustness + falsification
        |
        v
Research report
```

## Human handoff after software fix

Tell the human exactly:

1. which commands pass;
2. which historical commands correctly refuse and their exit codes;
3. that genuine 1-minute market data is now the only remaining equity-research input;
4. which seven equity/ETF symbols are required;
5. that options remain separately unvalidated.

Do not include synthetic performance as evidence.

## Definition of done for this handoff

- CLI refusal is non-zero;
- strategy daily bootstrap has an explicit complete observation unit;
- final OOS diagnostics identify their evaluation period;
- pytest passes;
- ruff passes;
- CI passes;
- documentation is synchronized.

After that, wait for genuine market data rather than inventing a substitute.


## Next phase — Massive data ingestion

Once the final gate fix is complete, continue with:

- `docs/execution_plan/GEMINI_MASSIVE_INGESTION_HANDOFF.md`
- `docs/execution_plan/MASSIVE_DATA_INGESTION.md`
- `docs/execution_plan/MASSIVE_DATA_MANIFEST_SCHEMA.md`

The human may provide `MASSIVE_API_KEY` at runtime. Never request that the key be committed to the repository.

The Massive phase is strictly data acquisition, normalization, provenance, and verification. Do not optimize the strategy or interpret performance during this phase.

## Current phase after first real-data run

The Massive ingestion phase has now produced a genuine 1-minute dataset and a first historical comparison. Before any further research interpretation, execute:

1. docs/execution_plan/POST_FIRST_REAL_RUN_AUDIT.md
2. docs/execution_plan/POST_FIRST_RUN_ACCEPTANCE_TESTS.md
3. docs/execution_plan/GEMINI_POST_FIRST_RUN_HANDOFF.md

Do not tune the strategy to improve the first-run result. The current task is to correct implementation fidelity, freeze exit geometry, reconcile provenance, add diagnostics, and establish explicit train/validation/test boundaries.

After the audit acceptance criteria pass, stop software changes and wait for the formal OOS research run.
