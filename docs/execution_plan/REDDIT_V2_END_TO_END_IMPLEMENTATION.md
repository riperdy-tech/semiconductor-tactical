# Reddit Behavioral Replication V2 — End-to-End Implementation

## 1. Architectural Synthesis

Phase K connects the modular V2 architecture into a runnable, reproducible research pipeline. Rather than testing isolated formulaic entry signals, the pipeline models the integrated portfolio process described by the Reddit source:

```
Historical 1m Bars (MU, SNDK, SKHY)
             │
             ▼
Feature & Moving Average Computation
             │
             ▼
V2 Directional Signal Generator (6-Stage Sequence)
             │
             ▼
Pending Orders (No-Lookahead: Signal at t close -> Execution at t+1)
             │
             ▼
ExecutionSimulator (Slippage, Commissions, Liquidity Capping)
             │
             ▼
V2PortfolioEngine
 ├── Layer 1: Persistent Core (60% Normalized Scenario, Static Hold)
 ├── Layer 2: Tactical Sleeve (Add, Reload, 50% Scale-Out, LOCAL_LOW Stop)
 ├── Layer 3: Covered-Call Overlay (Gated as UNVALIDATED without chains)
 ├── Layer 4: Account-Level Margin (Debt, 5% Annual Interest, Maintenance)
 └── Layer 5: Segregated Profit Withdrawals
             │
             ▼
Equity Curve & Zero-Tolerance P&L Reconciliation Invariant
             │
             ▼
Canonical Machine-Readable JSON & Human-Readable Markdown Reports
```

---

## 2. Research Scope & Universe Discipline

### A. Strict Headline Universe
- **`MU`**: Micron Technology, Inc. (`SOURCE_IDENTIFIED`, `VALIDATED`).
- **`SNDK`**: SanDisk Corporation (`SOURCE_IDENTIFIED`, `VALIDATED`).
- **`SKHY`**: SK Hynix Inc. U.S. ADR (`SOURCE_IDENTIFIED`, `VALIDATED`).

### B. Quarantined & Excluded Instruments
- **Direct Asian Venues**: Korea Exchange (`000660.KS`) and Tokyo Stock Exchange (`285A.T`) are explicitly `OUT_OF_SCOPE_FOR_V2`.
- **Generic Sector ETF (`USD`)**: Strictly quarantined from headline replication.
- **Candidate Leveraged ETFs (`SKUU`, `SKHU`, `SKHL`, `MUU`, etc.)**: Cataloged as `CANDIDATE_PROXY` and excluded from headline replication until primary-source confirmation.
- **Conditional OTC ADR (`KXIAY`)**: Active U.S. OTC ADR (1:10 ratio) proxying Tokyo Kioxia activity; never described as Nasdaq-listed (Kioxia Sep 15, 2026 release confirmed U.S. listing details remain undecided); gated as `UNVALIDATED`.

---

## 3. Normalized Core Research Methodology

- **Starting Equity**: $100,000 normalized capital base.
- **Core Allocation**: 60% ($60,000) allocated across persistent core holdings on Day 1 ($20,000 equal notional in each of MU, SNDK, SKHY).
- **Epistemic Classification**: `ASSUMPTION` for a research scenario. The source describes holding massive core inventory across cycle swings but does not disclose exact starting weights or allocations.
- **Static Core Policy**: Monthly rebalancing is removed from default V2 behavior. Core inventory persists statically unless altered by tactical interaction, option assignment, or forced margin liquidation.
- **Core Isolation Invariant**: All tactical reduction and stop-loss orders are routed strictly to the tactical sleeve. **Tactical exits never liquidate or reduce persistent core shares.**

---

## 4. Frozen Directional Signal Engine & Exit Semantics

The directional model (`src/tactical_engine/signals/v2_signals.py`) implements the 6-stage sequence using frozen pre-registered parameters:
1. **Regime Context**: Price above 60-bar SMA with positive slope (`HYPOTHESIS`).
2. **Directional Impulse**: Rolling surge $\ge 2.0\%$ over 30-minute lookback (`HYPOTHESIS`, centered on source's illustrative ~2% reference).
3. **Retreat / Pullback**: 50% retracement of the impulse range (`HYPOTHESIS`).
4. **Stabilization**: 5 consecutive bars consolidating above the local trough (`HYPOTHESIS`).
5. **Tactical Add / Reload**: Market / stop-limit entry in tactical sleeve (~10% equity unit size).
6. **Rebound & Stop Exits**:
   - **Partial Exit (50%)**: When price achieves 50% rebound of pullback distance toward impulse peak (`HYPOTHESIS`).
   - **Stop Invalidation**: `LOCAL_LOW` stop set 0.2% below stabilization trough (`HYPOTHESIS`).
   - **Reload**: If partially reduced and price stabilizes above initial entry, reloads second unit.

---

## 5. Account Margin & Financing Model

In tier V2-C, the account operates under full margin financing:
- **Max Gross Leverage**: 2.0x (`ASSUMPTION / HYPOTHESIS`).
- **Margin Financing Rate**: 5% annual rate accrued continuously on negative cash debt.
- **Maintenance Requirement**: 25% of total market value (FINRA Rule 4210 broker model).
- **Forced Liquidation Priority**: Liquidates tactical sleeve positions first to preserve core equity.

---

## 6. Execution Runner & CLI

Canonical runner implemented in `src/tactical_engine/research/v2_historical_runner.py` and exposed in `run.ps1`:
```powershell
.\run.ps1 fidelity-v2-historical
```
Outputs:
- Machine-readable: `reports/v2_historical_comparison.json`
- Human-readable: `reports/V2_HISTORICAL_COMPARISON.md`
- Run archive: `reports/fidelity_runs/v2_comparison_<run_id>_<timestamp>/`
