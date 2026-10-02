# Phase 3 Margin Model Implementation Plan

> **For agentic workers:** Implement task-by-task with TDD. Each task ends with verified tests and a git commit.

**Goal:** Implement realistic margin simulation including financing rates, maintenance margin requirements, buying power calculations, margin call detection, forced liquidation ordering with liquidation slippage, and overnight leverage constraints.

**Architecture:**
- `src/tactical_engine/portfolio/margin.py`: Pure margin math, maintenance requirement calculations, margin interest accrual, and forced liquidation order generation.
- Integrate margin accounting into `PortfolioTracker` ([`state.py`](file:///c:/Users/riper/Downloads/semiconductor-tactical/src/tactical_engine/backtest/state.py)) and event loop ([`engine.py`](file:///c:/Users/riper/Downloads/semiconductor-tactical/src/tactical_engine/backtest/engine.py)).
- Update `CostConfig` / `PortfolioConfig` to support margin rates, maintenance ratios, and liquidation penalties.
- Track margin statistics: margin interest paid, peak margin debt, margin call count, and forced liquidation count.

**Spec:** [`docs/STRATEGY_SPEC.md` §11](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/STRATEGY_SPEC.md), [`docs/IMPLEMENTATION_PLAN.md` Phase 3](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/IMPLEMENTATION_PLAN.md).

---

### Task 1: Pure Margin Calculations & Interest Accrual

**Files:**
- Create: `src/tactical_engine/portfolio/margin.py`
- Test: `tests/test_margin_math.py`

**Interfaces:**
- Produces: `calculate_margin_interest(...) -> float`, `calculate_maintenance_requirement(...) -> float`, `is_margin_call(...) -> bool`

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

---

### Task 2: Forced Liquidation Logic & Penalties

**Files:**
- Modify: `src/tactical_engine/portfolio/margin.py`
- Test: `tests/test_forced_liquidation.py`

**Interfaces:**
- Produces: `generate_forced_liquidation_orders(...) -> list[Order]`

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

---

### Task 3: Portfolio & Backtest Engine Margin Integration

**Files:**
- Modify: `src/tactical_engine/backtest/state.py`
- Modify: `src/tactical_engine/backtest/engine.py`
- Modify: `src/tactical_engine/reports/metrics.py`
- Test: `tests/test_margin_backtest.py`

**Interfaces:**
- Produces: Complete event-loop margin handling with margin calls, liquidations, interest accrual, and metrics.

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**
