# Phase 2 Robustness Framework Implementation Plan

> **For agentic workers:** Implement task-by-task with TDD. Each task ends with verified tests and a git commit.

**Goal:** Build the complete Phase 2 robustness framework supporting walk-forward splitting, parameter sweeps, trade bootstrap / Monte Carlo resampling, stability diagnostics, and experiment matrix report generation.

**Architecture:** Research modules under `tactical_engine.research` that operate on existing deterministic engine pipelines:
- `walk_forward.py`: Dataset temporal splitting and walk-forward runner.
- `sweeps.py`: Grid generator for parameter perturbations and multi-parameter backtest executor.
- `bootstrap.py`: Monte Carlo trade bootstrap and randomized entry benchmark.
- `diagnostics.py`: Stability metrics (neighborhood Sharpe/expectancy decay, max drop-off) and tabular summarizers.
- `cli.py`: Unified CLI command to run the full experiment matrix.

**Spec:** [`docs/BACKTEST_PROTOCOL.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/BACKTEST_PROTOCOL.md), [`docs/EXPERIMENT_MATRIX.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/EXPERIMENT_MATRIX.md), [`docs/IMPLEMENTATION_PLAN.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/IMPLEMENTATION_PLAN.md).

---

### Task 1: Walk-Forward Dataset Splitting & Evaluation

**Files:**
- Create: `src/tactical_engine/research/walk_forward.py`
- Test: `tests/test_walk_forward.py`

**Interfaces:**
- Produces: `split_data_by_time(...) -> dict[str, dict[str, list[Bar]]]`, `WalkForwardResult`

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

---

### Task 2: Parameter Sweeps & Grid Evaluation

**Files:**
- Create: `src/tactical_engine/research/sweeps.py`
- Test: `tests/test_sweeps.py`

**Interfaces:**
- Produces: `ParameterGrid`, `run_parameter_sweep(...) -> list[SweepResult]`

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

---

### Task 3: Bootstrap & Monte Carlo Resampling

**Files:**
- Create: `src/tactical_engine/research/bootstrap.py`
- Test: `tests/test_bootstrap.py`

**Interfaces:**
- Produces: `bootstrap_trade_returns(...) -> BootstrapDistribution`, `run_random_entry_control(...) -> BacktestResult`

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

---

### Task 4: Stability Diagnostics & Comparison Tables

**Files:**
- Create: `src/tactical_engine/research/diagnostics.py`
- Test: `tests/test_diagnostics.py`

**Interfaces:**
- Produces: `calculate_stability_score(...) -> float`, `render_sweep_table(...) -> str`

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

---

### Task 5: Robustness CLI & Experiment Matrix Generator

**Files:**
- Create: `src/tactical_engine/research/cli.py`
- Test: `tests/test_research_cli.py`

**Interfaces:**
- Produces: Runnable CLI: `python -m tactical_engine.research.cli --config configs/base.yaml`

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Full verification & Commit**
