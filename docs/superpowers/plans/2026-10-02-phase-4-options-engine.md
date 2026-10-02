# Phase 4 Options Engine Implementation Plan

> **For agentic workers:** Implement task-by-task with TDD. Each task ends with verified tests and a git commit.

**Goal:** Implement the covered-call options engine with historical chain provider interface, strict underlying share linkage (100 shares per contract), bid/ask spread & slippage modeling, expiry assignment mechanics, and premium attribution without look-ahead bias.

**Architecture:**
- `src/tactical_engine/options/contracts.py`: Option contract data models (`OptionQuote`, `OptionPosition`, `CoveredCallRecord`).
- `src/tactical_engine/options/chain_provider.py`: Interface and provider for point-in-time option chains.
- `src/tactical_engine/options/covered_calls.py`: Contract selection (strike, DTE, moneyness), sell triggers, and buyback triggers.
- `src/tactical_engine/options/assignment.py`: Expiration evaluation and assignment cashflow settlement.
- Integration with `PortfolioTracker` and `run_backtest` when `config.options.enabled = True`.

**Spec:** [`docs/STRATEGY_SPEC.md` §8-9](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/STRATEGY_SPEC.md), [`docs/DATA_CONTRACT.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/DATA_CONTRACT.md), [`AGENTS.md` §5](file:///c:/Users/riper/Downloads/semiconductor-tactical/AGENTS.md).

---

### Task 1: Option Data Models & Chain Provider

**Files:**
- Create: `src/tactical_engine/options/contracts.py`
- Create: `src/tactical_engine/options/chain_provider.py`
- Test: `tests/test_option_contracts.py`

**Interfaces:**
- Produces: `OptionQuote`, `OptionPosition`, `CoveredCallRecord`, `HistoricalOptionChainProvider`

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

---

### Task 2: Covered-Call Selection, Execution, & Assignment

**Files:**
- Create: `src/tactical_engine/options/covered_calls.py`
- Create: `src/tactical_engine/options/assignment.py`
- Test: `tests/test_covered_calls.py`

**Interfaces:**
- Produces: `select_covered_call_contract(...)`, `evaluate_expiration_assignment(...)`

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**

---

### Task 3: Options Lifecycle Integration into Backtest Engine

**Files:**
- Modify: `src/tactical_engine/backtest/state.py`
- Modify: `src/tactical_engine/backtest/engine.py`
- Modify: `src/tactical_engine/reports/metrics.py`
- Test: `tests/test_options_backtest.py`

**Interfaces:**
- Produces: Full covered-call backtest simulation with premium attribution and share assignment.

- [ ] **Step 1: Write failing test**
- [ ] **Step 2: Run test to verify failure**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Verify test passes**
- [ ] **Step 5: Commit**
