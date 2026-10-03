# Reddit Behavioral Replication V2 — Portfolio Architecture & Accounting Model

## 1. Architectural Foundation

The fundamental defect of prior single-signal backtests was assuming an account that begins flat, buys on a signal, holds for minutes, exits back to 100% cash, and evaluates P&L in isolation.

The primary Reddit source describes a completely different reality: a **multi-layered portfolio process** where the trader maintained large persistent core equity inventory, actively traded tactical slices around that inventory on margin, and wrote covered calls against owned shares to harvest premium during surges.

---

## 2. Multi-Layer Portfolio Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   ACCOUNT-LEVEL MARGIN & CASH LEDGER                   │
│  - Total Cash (can be negative = Margin Debt)                          │
│  - Financing Interest Accrual (5% annual, debited to cash)             │
│  - Aggregate Net Equity & Maintenance Margin Requirement (25%)          │
│  - Segregated Profit Withdrawal Tracking Ledger                        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
┌─────────────────────────────────┐         ┌─────────────────────────────────┐
│     LAYER 1: PERSISTENT CORE    │         │    LAYER 2: TACTICAL SLEEVE     │
│ - Long-lived inventory (MU,     │         │ - Intraday / swing scalps       │
│   SNDK, SKHY)                   │         │ - Add / reload on stabilization │
│ - Separate cost basis & P&L     │         │ - Partial / full exits          │
│ - Collateral for margin debt    │         │ - Tactical exits NEVER reduce   │
│ - Collateral for covered calls  │         │   persistent core inventory     │
└────────────────┬────────────────┘         └─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     LAYER 3: COVERED CALLS      │
│ - Attached to owned core shares │
│ - Max contracts = shares / 100  │
│ - Sell on strength              │
│ - Buy back on pullback          │
│ - Gated by real option chains   │
└─────────────────────────────────┘
```

---

## 3. Layer Specifications

### Layer 1: Persistent Core Holdings
- **Behavior**: Long-term structural position in memory leaders reflecting the cyclical bull thesis.
- **Tracking**: Tracks share quantity, average entry price, unrealized P&L, realized P&L from rebalancing, and encumbered shares committed to covered calls.
- **Inventory Protection**: Tactical sell orders are strictly routed to the tactical sleeve and cannot decrement core shares.
- **Allocation Rule**: Exact percentage allocation across symbols was not stated by the source; treated as `UNVERIFIED` / `ASSUMPTION` (modeled in experiments as 50%–70% of initial equity).

### Layer 2: Tactical Trading Sleeve
- **Behavior**: Rapid scalps and swing reloads to exploit short-term volatility around the core position.
- **Operations Supported**:
  - `tactical_add`: expands tactical exposure when a stabilization trigger occurs;
  - `tactical_reduce`: scales out (e.g., 50% partial exit, 100% full exit) on rebound;
  - `re-entry`: allows multiple reloads during a sustained trend.
- **Isolation**: When tactical inventory drops to zero, the core position remains 100% active and unencumbered.

### Layer 3: Covered-Call Overlay State Machine
- **Ownership Constraint**: Calls are strictly written against owned, unencumbered core shares:
  $$\text{Maximum Contracts} = \lfloor \frac{\text{Available Core Shares}}{100} \rfloor$$
- **State Machine**:
  1. `AVAILABLE`: Core shares unencumbered.
  2. `WRITTEN`: Sold short call on underlying surge; premium credited to account cash; shares encumbered.
  3. `BOUGHT_BACK`: Call repurchased at a profit upon underlying retreat; shares unencumbered; realized option P&L locked.
  4. `EXPIRED_OTM`: Underlying closes below strike at expiration; shares unencumbered; full premium realized.
  5. `ASSIGNED`: Underlying closes above strike; core shares delivered at strike price; strike proceeds credited to cash.
- **Hard Validation Gate**: In accordance with `AGENTS.md` Section 7, covered-call P&L cannot be included in headline research results without validated historical option chains.

### Layer 4: Account-Level Margin & Financing
- **Margin Debt**:
  $$\text{Margin Debt} = \max(0.0, -\text{Cash})$$
- **Financing Cost Accrual**:
  $$\text{Interest} = \text{Margin Debt} \times \text{Rate}_{\text{annual}} \times \frac{\Delta t}{365 \times 86400}$$
- **Maintenance Requirement**:
  $$\text{Maintenance} = (\text{Core Market Value} + \text{Tactical Market Value}) \times 0.25$$
- **Forced Liquidation Priority**: If net equity falls below maintenance, forced liquidation orders are generated. To protect long-term core inventory, the engine liquidates tactical positions first before touching unencumbered core holdings.

### Layer 5: Segregated Profit Withdrawals
- **Accounting Rule**: The Reddit trader described withdrawing realized profits periodically.
- **Integrity Constraint**: Withdrawals are logged in a dedicated capital ledger. They are **never** treated as trading performance or used to artificially inflate the strategy's time-weighted return or Sharpe ratio.

---

## 4. Fundamental Accounting Invariant

The V2 portfolio engine enforces an exact, zero-tolerance reconciliation invariant:

$$\Delta \text{Equity} + \text{Withdrawals} - \text{Deposits} = \text{Realized P&L}_{\text{Core}} + \text{Unrealized P&L}_{\text{Core}} + \text{Realized P&L}_{\text{Tactical}} + \text{Unrealized P&L}_{\text{Tactical}} + \text{Option P&L} - \text{Financing} - \text{Commissions} - \text{Slippage}$$

Every V2 test and backtest execution mathematically verifies this invariant (`discrepancy < 1e-4`).
