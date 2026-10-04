# Phase M Frozen Prospective OOS Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and execute the Phase M Frozen Prospective Out-of-Sample (OOS) validation protocol for the Reddit Behavioral V2 strategy, strictly enforcing chronology gates, anti-contamination spec locks across all three post-L.2 research tracks, and deterministic evaluation without parameter tuning.

**Architecture:** A dedicated, isolated research runner (`v2_oos_runner.py`) reads strictly post-2026-09-30 market data, enforces pre-run parameter and configuration fingerprints against historical Run `24a9e783`, executes frozen V2-A/B/C modes, determines sample completeness (>= 20 sessions for conclusive status), assigns pre-registered interpretation classes (`SUPPORTIVE`, `NEUTRAL`, `CONTRADICTORY`, `INVALID`), and archives immutable artifacts under `reports/v2_oos/` and `reports/fidelity_runs/v2_oos_<run_id>/`.

**Tech Stack:** Python 3.12, Pydantic, pytest, ruff, powershell entry points (`run.ps1`, `run.bat`).

**Spec:** [`docs/execution_plan/REDDIT_V2_FROZEN_PROSPECTIVE_OOS_EXECUTION_PLAN.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/execution_plan/REDDIT_V2_FROZEN_PROSPECTIVE_OOS_EXECUTION_PLAN.md) and [`docs/execution_plan/REDDIT_V2_THREE_TRACK_RESEARCH_COORDINATION_PLAN.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/execution_plan/REDDIT_V2_THREE_TRACK_RESEARCH_COORDINATION_PLAN.md).

## Global Constraints

- Historical Run `24a9e783` and its canonical artifacts ([`reports/V2_HISTORICAL_COMPARISON.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/reports/V2_HISTORICAL_COMPARISON.md), [`reports/v2_historical_comparison.json`](file:///c:/Users/riper/Downloads/semiconductor-tactical/reports/v2_historical_comparison.json)) are immutable and must never be overwritten.
- ZERO parameter tuning or optimization based on prospective OOS data.
- Strict chronology gate: every bar evaluated in OOS must be strictly after `2026-09-30T23:59:59Z`.
- Minimum sample constraint: >= 20 complete regular-trading sessions required for `PHASE_M_PRISTINE_OOS_RESULT`; if < 20 complete sessions exist, result is strictly classified as `PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE`.
- Stage 1 Coordination Lock: Freeze all three post-L.2 research specifications (Phase M OOS, Phase N Options, Phase O Level-2) before viewing any prospective performance result.

---

### Task 1: Freeze Stage 1 Research Specifications (Cross-Track Anti-Contamination Lock)

**Files:**
- Create: `docs/research/v2_oos/V2_OOS_FROZEN_SPEC.md`
- Create: `docs/research/options/V2D_FROZEN_OPTION_POLICY.md`
- Create: `docs/research/microstructure/V2F_FROZEN_MICROSTRUCTURE_SPEC.md`

**Interfaces:**
- Consumes: [`docs/execution_plan/REDDIT_V2_FROZEN_PROSPECTIVE_OOS_EXECUTION_PLAN.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/execution_plan/REDDIT_V2_FROZEN_PROSPECTIVE_OOS_EXECUTION_PLAN.md), [`docs/execution_plan/REDDIT_V2_V2D_OPTIONS_EXECUTION_PLAN.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/execution_plan/REDDIT_V2_V2D_OPTIONS_EXECUTION_PLAN.md), [`docs/execution_plan/REDDIT_V2_V2F_LEVEL2_EXECUTION_PLAN.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/execution_plan/REDDIT_V2_V2F_LEVEL2_EXECUTION_PLAN.md)
- Produces: Authoritative, immutable policy documents locking research specifications for all three tracks prior to prospective evaluation.

- [ ] **Step 1: Write `docs/research/v2_oos/V2_OOS_FROZEN_SPEC.md`**
  - Document frozen universe (`MU`, `SNDK`, `SKHY`), initial equity ($100,000), 60% static core, directional impulse/pullback/stabilization/scale-out/stop parameters, 2.0x leverage limit, cost configuration, and parameter hash.
- [ ] **Step 2: Write `docs/research/options/V2D_FROZEN_OPTION_POLICY.md`**
  - Document frozen covered call policy: 3-7 DTE, target delta 0.20-0.30 OTM, 1 contract per 100 owned shares, strength-trigger selling, 50% premium / 50% underlying pullback buyback, physical share delivery on assignment.
- [ ] **Step 3: Write `docs/research/microstructure/V2F_FROZEN_MICROSTRUCTURE_SPEC.md`**
  - Document frozen Level-2 microstructure policy: top 5/10 book depth, order book imbalance, wall detection, queue depletion, and entry gating filter.
- [ ] **Step 4: Verify document integrity**
  - Ensure all parameter values match historical Run `24a9e783` and coordination plan definitions.

---

### Task 2: Create Frozen OOS Configuration (`configs/v2_oos_frozen.yaml`)

**Files:**
- Create: `configs/v2_oos_frozen.yaml`

**Interfaces:**
- Consumes: [`configs/historical_1m.yaml`](file:///c:/Users/riper/Downloads/semiconductor-tactical/configs/historical_1m.yaml)
- Produces: YAML config specifying prospective research boundaries starting after `2026-09-30T23:59:59Z`, identical costs, identical outputs layout.

- [ ] **Step 1: Write `configs/v2_oos_frozen.yaml`**
  - Set `research.start: "2026-10-01T00:00:00Z"`
  - Set `research.end: "2026-10-31T23:59:59Z"`
  - Set `strategy.universe: [MU, SNDK, SKHY]` (no proxies)
  - Keep signals, exits, portfolio, costs, and options sections identical to `historical_1m.yaml`
  - Set `outputs.root: reports/v2_oos`

---

### Task 3: Implement Dedicated OOS Runner (`src/tactical_engine/research/v2_oos_runner.py`)

**Files:**
- Create: `src/tactical_engine/research/v2_oos_runner.py`

**Interfaces:**
- Consumes: `tactical_engine.backtest.v2_engine.run_v2_backtest`, `tactical_engine.data.csv_provider.load_historical_universe`
- Produces: CLI script and library entry point `run_v2_oos_pipeline()` returning path to generated Markdown report and saving JSON + archival bundle.

- [ ] **Step 1: Write the data and parameter validator functions**
  - `validate_oos_chronology(bars: dict[str, list[Bar]])`: asserts all bar timestamps > `2026-09-30T23:59:59Z`.
  - `validate_oos_universe(symbols: list[str])`: asserts symbols match exact headline set `{"MU", "SNDK", "SKHY"}`.
  - `validate_parameter_fingerprint(cfg)`: verifies no Phase H post-hoc parameters or deviation from frozen V2.
  - `evaluate_session_completeness(bars: dict[str, list[Bar]]) -> tuple[int, str]`: counts distinct trading days with >= 300 bars; returns session count and status (`PHASE_M_PRISTINE_OOS_RESULT` if >= 20, else `PHASE_M_PRISTINE_OOS_INSUFFICIENT_SAMPLE`).
  - `evaluate_interpretation_class(res_a, res_b, res_c, session_count) -> str`: returns `SUPPORTIVE`, `NEUTRAL`, `CONTRADICTORY`, or `INVALID`.
- [ ] **Step 2: Write result Pydantic model `V2OOSComparisonResult`**
  - Includes `run_id`, `created_at_utc`, `execution_code_sha`, `data_manifest_id`, `date_range`, `session_count`, `sample_status`, `interpretation_class`, V2-A/B/C results, attribution metrics, and invariant checks.
- [ ] **Step 3: Implement `run_v2_oos_pipeline()` execution & serialization**
  - Loads data, runs validators, executes V2-A, V2-B, V2-C, computes tactical contribution and margin debt, formats Markdown report and JSON.
  - Writes outputs to `reports/v2_oos/<run_id>.json`, `reports/v2_oos/<run_id>.md`, and creates preservation bundle `reports/fidelity_runs/v2_oos_<run_id>/PRESERVATION_NOTE.md`.
  - Verifies that `reports/V2_HISTORICAL_COMPARISON.md` and `reports/v2_historical_comparison.json` are NOT touched.
- [ ] **Step 4: Implement CLI entry point `main()`**
  - Accept `--config`, `--data-dir`, `--execution-code-sha`.

---

### Task 4: Register `fidelity-v2-oos` in `run.ps1` and `run.bat`

**Files:**
- Modify: `run.ps1:1-30, 80-130`
- Modify: `run.bat` (if applicable)

**Interfaces:**
- Consumes: `src/tactical_engine/research/v2_oos_runner.py`
- Produces: CLI command `powershell -ExecutionPolicy Bypass -File .\run.ps1 fidelity-v2-oos`

- [ ] **Step 1: Update `run.ps1`**
  - Add `"fidelity-v2-oos"` to `[ValidateSet(...)]`
  - Add `"fidelity-v2-oos"` to exclusion list for fallback to sample fixtures
  - Add switch branch for `"fidelity-v2-oos"` invoking `tactical_engine.research.v2_oos_runner`
- [ ] **Step 2: Update `run.bat`**
  - Ensure `run.bat` delegates appropriately if passed arguments.

---

### Task 5: Comprehensive Regression Tests (`tests/test_v2_oos_validation.py`)

**Files:**
- Create: `tests/test_v2_oos_validation.py`

**Interfaces:**
- Consumes: `src/tactical_engine/research/v2_oos_runner.py`
- Produces: Pytest test suite covering all 10 requirements in Section 13 of `REDDIT_V2_FROZEN_PROSPECTIVE_OOS_EXECUTION_PLAN.md`.

- [ ] **Step 1: Write test 1 — Rejection of timestamps on or before 2026-09-30**
- [ ] **Step 2: Write test 2 — Rejection of non-headline symbols**
- [ ] **Step 3: Write test 3 — Rejection of missing common bars / unsynchronized data**
- [ ] **Step 4: Write test 4 — Rejection of altered parameter fingerprint**
- [ ] **Step 5: Write test 5 — Enforcement of frozen cost config**
- [ ] **Step 6: Write test 6 — Preservation of no-lookahead execution**
- [ ] **Step 7: Write test 7 — JSON output provenance and hash verification**
- [ ] **Step 8: Write test 8 — Verification of data requirement (refusal on synthetic data without fixture flag)**
- [ ] **Step 9: Write test 9 — Identical core initialization across V2-A/B/C**
- [ ] **Step 10: Write test 10 — Protection against overwriting accepted historical artifacts**
- [ ] **Step 11: Write test 11 — Sample completeness classification (<20 sessions -> INSUFFICIENT_SAMPLE; >=20 -> PRISTINE_OOS_RESULT)**

---

### Task 6: Pre-Evaluation Blindness Verification & Commit

**Files:**
- Repository working tree across Tasks 1–5.

- [ ] **Step 1: Run pytest on new test suite**
  - `.\.venv\Scripts\python.exe -m pytest -v tests/test_v2_oos_validation.py`
- [ ] **Step 2: Run full test suite**
  - `powershell -ExecutionPolicy Bypass -File .\run.ps1 test`
- [ ] **Step 3: Run ruff check**
  - `.\.venv\Scripts\python.exe -m ruff check .`
- [ ] **Step 4: Run doctor**
  - `powershell -ExecutionPolicy Bypass -File .\run.ps1 doctor`
- [ ] **Step 5: Commit pre-evaluation blindness package**
  - Commit message: `feat(research): implement Phase M frozen OOS specifications, runner, and regression tests`
  - Push commit to `origin/main`.
  - Record the commit SHA as the official `EXECUTION_CODE_SHA` for Phase M.

---

### Task 7: Prospective OOS Data Ingestion & Execution

**Files:**
- Create: `reports/data_manifests/v2_oos_<id>_manifest.json`
- Create: `reports/v2_oos/<run_id>.json`
- Create: `reports/v2_oos/<run_id>.md`
- Create: `reports/fidelity_runs/v2_oos_<run_id>/PRESERVATION_NOTE.md`

- [ ] **Step 1: Check available post-2026-09-30 data from Massive API**
  - Query Massive API for available dates starting 2026-10-01 for MU, SNDK, SKHY.
  - Ingest available bars into `data/processed_oos/` and generate `reports/data_manifests/v2_oos_<id>_manifest.json`.
- [ ] **Step 2: Validate OOS data via doctor-data**
  - Run `powershell -ExecutionPolicy Bypass -File .\run.ps1 doctor-data -Config configs/v2_oos_frozen.yaml -DataDir data/processed_oos`
- [ ] **Step 3: Execute frozen OOS runner exactly once**
  - Run `powershell -ExecutionPolicy Bypass -File .\run.ps1 fidelity-v2-oos -Config configs/v2_oos_frozen.yaml -DataDir data/processed_oos`
- [ ] **Step 4: Verify generated artifacts & invariants**
  - Assert historical Run `24a9e783` is untouched.
  - Verify sample count, classification status, and interpretation class.
- [ ] **Step 5: Commit and push OOS research artifacts**
  - Commit message: `feat(research): execute Phase M prospective OOS validation run`
  - Push to `origin/main`.
- [ ] **Step 6: Enforce STOP CONDITION: STOP SOFTWARE CHANGES**
  - Produce final Gemini completion report according to Section 17 of `REDDIT_V2_FROZEN_PROSPECTIVE_OOS_EXECUTION_PLAN.md`.
