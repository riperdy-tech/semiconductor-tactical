# Reddit Behavioral Replication V2 — Directional Trading Behavior

## 1. Overview & Paradigm Shift

In prior iterations (Phase 0 through Phase I), directional trading was modeled as an isolated, single-entry mean-reversion algorithm attempting to capture mathematical pullbacks.

In **V2 (Reddit Behavioral Replication)**, directional trading is explicitly modeled as an **active tactical sleeve operating around a persistent core holding**. The trader does not sit in cash waiting for a magic indicator; the trader already holds a substantial long inventory in semiconductor memory names and tactically adjusts gross exposure based on intraday and multi-day volatility impulses.

---

## 2. The 6-Stage Behavioral Sequence

The primary Reddit source describes an intuitive cyclical process of trading around positions rather than a static mechanical formula. V2 formalizes this sequence:

```
[1. Trend / Regime Context]
           │
           ▼
[2. Strong Directional Impulse]
           │
           ▼
[3. Retreat / Intraday Pullback]
           │
           ▼
[4. Stabilization / VWAP Reclaim]
           │
           ▼
[5. Tactical Add / Reload (Sleeve)]
           │
           ▼
[6. Rebound / Partial or Full Exit]
```

### Stage 1: Trend / Regime Context
- **Source Observation**: The trader operated within a strong multi-month structural bull market in memory semiconductors driven by HBM (High Bandwidth Memory) and NAND pricing cycle inflections.
- **Model Representation**: Regime filter evaluating whether the broader sector (SOXX / SMH) and individual equity are trading above higher-timeframe moving averages (e.g., daily 20/50 SMA).
- **Epistemic Classification**: `OBSERVED` (cyclical thesis) / `HYPOTHESIS` (moving average threshold proxy).

### Stage 2: Strong Directional Impulse
- **Source Observation**: Underlying stock experiences a sharp directional surge, often during market opening or pre-market momentum.
- **Model Representation**: Intraday impulse measured by rolling price change or VWAP expansion exceeding historical volatility norms.
- **Epistemic Classification**: `OBSERVED`.

### Stage 3: Retreat / Intraday Pullback
- **Source Observation**: Following the impulse, price retreats as short-term traders take profit. The source mentioned an approximately **2% move** in discussion.
- **Crucial Clarification**: The **~2% move** cited by the source was an **illustrative economic reference point**, NOT a rigid, hard-coded take-profit or fixed algorithmic parameter.
- **Model Representation**: Intraday retracement measured from local impulse peak toward value areas (VWAP or short-term EMAs).
- **Epistemic Classification**: `OBSERVED` (as an illustrative example) / `HYPOTHESIS` (as a modeled threshold).

### Stage 4: Stabilization / Reclaim
- **Source Observation**: The trader watched Level 2 and intraday order flow to identify where selling pressure subsided and buyers stepped back in.
- **Model Representation**: Consolidation of bars above a local support or reclaim of the session VWAP. Because genuine Level 2 is unavailable in standard OHLCV data, any OHLCV stabilization metric is an engineered proxy.
- **Epistemic Classification**: `DERIVED` proxy for unobserved Level-2 behavior.

### Stage 5: Tactical Add / Reload
- **Source Observation**: The trader added tactical leverage (either additional equity shares on margin or leveraged 2x products) once stabilization was perceived.
- **Crucial Architectural Rule**: This tactical add belongs strictly to the **tactical sleeve**. It does **not** modify or displace the persistent core inventory.
- **Order Mechanism**: Implemented via market or stop-limit orders above the stabilization reclaim level.
- **Epistemic Classification**: `OBSERVED` (tactical add) / `HYPOTHESIS` (stop-limit trigger specification).

### Stage 6: Rebound & Tiered Reduction
- **Source Observation**: As price rebounds into initial strength or previous highs, the trader scaled out of tactical positions ("scalping") while maintaining core long exposure.
- **Model Representation**: Tiered exit:
  - 50% tactical reduction at initial rebound target (e.g., return to session VWAP / impulse high);
  - Remaining 50% trailing stop or multi-day swing hold.
- **Crucial Invariant**: Tactical exits never liquidate core shares. Core position persists through pullbacks.
- **Epistemic Classification**: `OBSERVED` (scaling out of tactical trades).

---

## 3. Quarantining Phase H Post-Hoc Parameters

In Phase H, parameters were calibrated post-hoc on the July 1–September 30, 2026 dataset:
- `impulse_pct_range`: `[0.005, 0.030]`
- `stabilization_ratio`: `0.35`
- `stop_loss_atr_mult`: `1.5`
- `target_atr_mult`: `2.5`
- `max_holding_bars`: `120`

**Strict Integrity Mandate**:
These specific values were discovered after observing the sample and produced an artificial 8-minute median holding period. They must **never** be cited as primary source facts or pre-registered V2 specifications. They remain quarantined in `docs/REDDIT_FIDELITY_PARAMETER_PROVENANCE.md` under `POST_HOC_SPECIFIED`.

---

## 4. Frozen Pre-Registered V2 Candidate Parameter Family

To prevent data-snooping and curve-fitting against the July–September period, V2 pre-registers a disciplined, bounded candidate parameter family established strictly on market-structure rationale prior to any V2 performance evaluation:

| Parameter ID | Parameter Name | Candidate Set | Economic / Behavioral Rationale | Status |
|---|---|---|---|---|
| `V2_DIR_IMP_01` | `impulse_lookback_bars` | `[15, 30, 60]` min | Captures 15-minute to 1-hour morning/session directional thrusts | `PRE_REGISTERED` |
| `V2_DIR_IMP_02` | `min_impulse_magnitude` | `[0.015, 0.020, 0.025]` (1.5%–2.5%) | Centered on the source's illustrative ~2% economic reference | `PRE_REGISTERED` |
| `V2_DIR_PB_01` | `pullback_depth_fraction` | `[0.382, 0.500, 0.618]` | Standard Fibonacci / auction-market retracement fractions of impulse | `PRE_REGISTERED` |
| `V2_DIR_STAB_01`| `stabilization_bars` | `[3, 5, 8]` bars | Minimum bars of consolidation above local low before reload | `PRE_REGISTERED` |
| `V2_DIR_EXIT_01`| `tactical_scale_out_ratio` | `[0.50, 1.00]` | 50% partial scale-out vs 100% full tactical liquidation on rebound | `PRE_REGISTERED` |
| `V2_DIR_STOP_01`| `tactical_stop_mode` | `["LOCAL_LOW", "ATR_TRAILING"]` | Structural stop below stabilization pivot vs ATR volatility band | `PRE_REGISTERED` |

**Rule**: Any future run on July–September using these parameters remains `POST_HOC_HOLDOUT`. True statistical validation requires unseen future data (`PRISTINE_OOS`).
