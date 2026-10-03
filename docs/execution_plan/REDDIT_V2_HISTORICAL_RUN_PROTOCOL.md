# Reddit Behavioral Replication V2 — Historical Run Protocol

## 1. Executive Summary & Protocol Objectives

This document establishes the authoritative execution and validation protocol for the **Reddit Behavioral Replication V2 Historical Research Engine**.

The protocol bridges the V2 architectural specifications into an automated, end-to-end historical research workflow while enforcing strict epistemic boundaries:
1. **Scope Integrity**: Execution is strictly confined to verified U.S.-market data for the core trio: `MU`, `SNDK`, and `SKHY`.
2. **Universe Discipline**: Direct Asian equities (`000660.KS`, `285A.T`), generic sector funds (`USD`), candidate 2× leveraged ETFs (`SKUU`, `SKHU`, `SKHL`, `MUU`, etc.), and conditional OTC ADRs (`KXIAY`) are strictly quarantined from the headline source replication.
3. **Data Gating**: Covered calls (`V2-D`) and Level-2 microstructure models (`V2-F`) are data-gated as `UNVALIDATED` until verified primary quotes/order-book archives are integrated.
4. **Evaluation Partition**: The July 1 – September 30, 2026 data period is formally classified as `POST_HOC_HOLDOUT`. Parameter tuning, search grids, or optimization against this sample are strictly prohibited.
5. **Pristine OOS Status**: Declared as `PRISTINE_OOS = UNAVAILABLE` until unseen future chronological data is evaluated.

---

## 2. Default Instrument Universe & Gating Matrix

| Symbol | Description | Venue / Asset Class | Replication Role | Gate / Protocol Status |
|---|---|---|---|---|
| **`MU`** | Micron Technology, Inc. | U.S. Nasdaq (Equity) | Headline Core + Tactical | `SOURCE_IDENTIFIED`, `VALIDATED` |
| **`SNDK`** | SanDisk Corporation | U.S. Nasdaq (Equity) | Headline Core + Tactical | `SOURCE_IDENTIFIED`, `VALIDATED` |
| **`SKHY`** | SK Hynix Inc. ADR | U.S. OTC ADR (1:1 Ratio) | Headline Core + Tactical | `SOURCE_IDENTIFIED`, `VALIDATED` |
| **`KXIAY`** | Kioxia Holdings ADR | U.S. OTC ADR (1:10 Ratio) | Proxy Experiment Only | `QUARANTINED` (`UNVALIDATED` pending OTC feed) |
| **`USD`** | ProShares Ultra Semi (2×) | U.S. NYSE Arca (Leveraged ETF) | Excluded from Headline | `QUARANTINED` (Generic sector ETF, not source holding) |
| **`SKUU` / `SKHU`** | Candidate 2× Hynix ETFs | U.S. Leveraged ETPs | Candidate Proxy Only | `QUARANTINED` (`CANDIDATE_PROXY`, unverified) |
| **`MUU`** | Candidate 2× Micron ETF | U.S. Leveraged ETP | Candidate Proxy Only | `QUARANTINED` (`CANDIDATE_PROXY`, unverified) |
| **`000660.KS`** | SK Hynix Inc. | Korea Exchange (KRX) | Direct Asian Venue | `OUT_OF_SCOPE_FOR_V2` (Reserved for V3) |
| **`285A.T`** | Kioxia Holdings Corp. | Tokyo Stock Exchange (TSE) | Direct Asian Venue | `OUT_OF_SCOPE_FOR_V2` (Reserved for V3) |

---

## 3. Normalized Core Portfolio Research Scenario

Because the primary Reddit source describes holding massive, cycle-long core inventory but does not disclose exact dollar amounts, initial account balances, or exact starting weights:
- **Starting Account Equity**: $100,000 normalized cash base.
- **Core Allocation Ratio**: 60% of total starting equity ($60,000).
- **Epistemic Classification**: `ASSUMPTION` (research scenario assumption).
- **Core Asset Weights**: Equal notional allocation across the validated headline trio:
  - $20,000 notional in `MU`
  - $20,000 notional in `SNDK`
  - $20,000 notional in `SKHY`
- **Initial Core Execution**: Purchased at Bar 0 (Day 1 RTH open) at `open_price * (1 + slippage)`.
- **Static Core Policy**: Monthly rebalancing is removed from default V2 behavior. Core inventory persists statically unless altered by tactical interaction, option assignment, or forced margin liquidation.
- **Tactical Capacity**: The remaining 40% ($40,000) serves as liquidity/collateral for tactical scalps and swings.
- **Core Isolation Invariant**: Tactical reductions and stop orders are routed strictly to the tactical sleeve. **Tactical exits never liquidate or reduce persistent core shares.**

---

## 4. Directional Signal Engine & Frozen Candidate Parameters

The directional model (`src/tactical_engine/signals/v2_signals.py`) evaluates market structure across 6 deterministic stages:
1. **Regime Context**: Price above 60-bar SMA with positive 5-bar SMA slope (`HYPOTHESIS`).
2. **Directional Impulse**: Rolling price change $\ge 2.0\%$ over 30-minute lookback (`HYPOTHESIS`).
3. **Retreat / Pullback**: Retracement of 50% of the impulse range (`HYPOTHESIS`).
4. **Stabilization**: 5 consecutive bars consolidating above the local retracement trough (`HYPOTHESIS`).
5. **Tactical Add / Reload**: Market / stop-limit order sizing ~10% equity unit in the tactical sleeve.
6. **Tactical Exits**:
   - **Partial Exit (50%)**: When price achieves 50% rebound of pullback distance toward impulse peak (`HYPOTHESIS`).
   - **Stop Invalidation**: `LOCAL_LOW` stop set 0.2% below stabilization trough (`HYPOTHESIS`).
   - **Reload**: If partially reduced and price stabilizes above initial entry, reloads a second unit.

### Frozen Parameter Registry

| Parameter ID | Parameter Name | Frozen Default Value | Epistemic Status |
|---|---|---|---|
| `V2_DIR_IMP_01` | `impulse_lookback_bars` | 30 minutes | `HYPOTHESIS` |
| `V2_DIR_IMP_02` | `min_impulse_magnitude` | 0.020 (2.0%) | `HYPOTHESIS` |
| `V2_DIR_PB_01` | `pullback_depth_fraction` | 0.500 (50%) | `HYPOTHESIS` |
| `V2_DIR_STAB_01`| `stabilization_bars` | 5 bars | `HYPOTHESIS` |
| `V2_DIR_EXIT_01`| `tactical_scale_out_ratio` | 0.50 (50%) | `HYPOTHESIS` |
| `V2_DIR_STOP_01`| `tactical_stop_mode` | `"LOCAL_LOW"` (0.2% buffer) | `HYPOTHESIS` |

**Zero-Tuning Mandate**: These values are pre-registered hypotheses. They must not be modified or fitted against July–September backtest results.

---

## 5. End-to-End Execution Pipeline

The execution architecture enforces strict no-lookahead ordering and full cost accounting:

```
[Historical 1m Bars: MU, SNDK, SKHY]
              │
              ▼
[Feature & Regime Computation at Bar t]
              │
              ▼
[V2 Directional Signal Generator: Bar t Close]
              │
              ▼
[Pending Orders Generated for Bar t+1]
              │
              ▼
[ExecutionSimulator: Fill at Bar t+1 Open/Range +/- Slippage & Fees]
              │
              ▼
[V2PortfolioEngine: Update Core, Tactical Sleeve, Margin Debt]
              │
              ▼
[End of Bar t+1: Margin Interest Accrual & Equity Mark-to-Market]
              │
              ▼
[Performance Metrics & Component P&L Attribution Reconciliation]
```

### Execution Invariants
1. **No-Lookahead**: Signal generated at timestamp $t$ close is filled at timestamp $t+1$ open.
2. **Cost Simulation**: Fixed 5 bps slippage and $0.005/share commissions applied to all fills.
3. **Margin Model (V2-C)**: 2.0x gross leverage cap (`ASSUMPTION/HYPOTHESIS`), 5% annual interest accrued on cash debt, 25% FINRA maintenance margin requirement.
4. **P&L Attribution Reconciliation Invariant**:
   $$\text{Pre-Slippage Gross P\&L} - \text{Slippage} - \text{Commissions} - \text{Margin Interest} = \text{Portfolio Net P\&L} = \text{Ending Equity} - \text{Initial Cash}$$

---

## 6. Historical Runner CLI & Verification

The canonical Windows entry point is wired into `run.ps1`:

```powershell
.\run.ps1 fidelity-v2-historical
```

### Generated Artifacts
1. **Machine-Readable**: `reports/v2_historical_comparison.json`
2. **Human-Readable**: `reports/V2_HISTORICAL_COMPARISON.md`
3. **Run Archive**: `reports/fidelity_runs/v2_comparison_<run_id>_<timestamp>/` containing configuration snapshot, execution logs, and full performance metrics.

---

## 7. Mandatory Verification Suite

Prior to marking Phase K complete, the following commands must execute cleanly with zero errors:

```powershell
.\run.ps1 test
.\run.ps1 doctor
.\run.ps1 doctor-data -Config configs/historical_1m.yaml -DataDir data/processed
.\.venv\Scripts\python.exe -m ruff check .
```

---

## 8. Mandatory Research Stop Condition

Following the successful execution of `fidelity-v2-historical` and verification passes:
**ALL SOFTWARE CHANGES MUST STOP.**

Under no circumstances may:
- Directional parameters be recalibrated to improve return;
- Core weights be altered to match historical price trends;
- Leveraged ETFs or OTC ADRs be added to boost P&L;
- Trade count or holding period be optimized toward Reddit claims.
