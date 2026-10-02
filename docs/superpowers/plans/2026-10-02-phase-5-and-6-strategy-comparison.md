# Phase 5 & Phase 6 Strategy Comparison & Research Report Implementation Plan

> **For agentic workers:** Implement task-by-task with TDD. Each task ends with verified tests and a git commit.

**Goal:** Implement the multi-variant strategy comparison framework (`literal_clone`, `risk_controlled`, `regime_adapted`) and produce the authoritative research report `reports/strategy_comparison.md` covering all 10 required falsification questions from `STRATEGY_SPEC.md` §12.

**Architecture:**
- `src/tactical_engine/research/comparison.py`: Orchestrates running the three variants against identical underlying data and option chains. Computes comparative metrics, cost sensitivity, leverage sensitivity, and options attribution.
- `src/tactical_engine/research/report_generator.py`: Renders the comprehensive markdown research report `reports/strategy_comparison.md`.
- Extension of CLI: `python -m tactical_engine.research.comparison --config configs/base.yaml`

**Spec:** [`docs/STRATEGY_SPEC.md` §2, §11, §12, §13](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/STRATEGY_SPEC.md), [`docs/IMPLEMENTATION_PLAN.md` Phase 5 & 6](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/IMPLEMENTATION_PLAN.md), [`AGENTS.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/AGENTS.md).

---

### Task 1: Multi-Variant Strategy Comparison Runner

**Files:**
- Create: `src/tactical_engine/research/comparison.py`
- Test: `tests/test_strategy_comparison.py`

**Interfaces:**
- Produces: `StrategyComparisonResult`, `run_strategy_comparison(...) -> StrategyComparisonResult`

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

---

### Task 2: Comparative Research Report Generator & CLI

**Files:**
- Create: `src/tactical_engine/research/report_generator.py`
- Test: `tests/test_report_generator.py`

**Interfaces:**
- Produces: `render_comparison_report(comparison: StrategyComparisonResult) -> str` and runnable CLI.

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

---

### Task 3: Execution of Full Research Report

- [ ] **Step 1: Execute comparison runner to generate `reports/strategy_comparison.md`**
- [ ] **Step 2: Verify all 37+ tests pass and ruff check is clean**
- [ ] **Step 3: Mark Phase 5 and Phase 6 complete in `docs/IMPLEMENTATION_PLAN.md` and commit**
