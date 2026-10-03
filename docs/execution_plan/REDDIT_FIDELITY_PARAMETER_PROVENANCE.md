# Directional Fidelity Parameter Provenance Record

> **STATUS:** Phase I — Post-Run Research Integrity Correction  
> **CLASSIFICATION REQUIREMENT:** Per `docs/execution_plan/GEMINI_PHASE_H_POST_RUN_CORRECTION.md` Section 5.  
> **OVERALL PARAMETER PROVENANCE STATUS:** `POST_HOC_SPECIFIED`  
> **RESEARCH VALIDITY IMPLICATION:** Directional performance cannot be treated as a forward-tested or out-of-sample validated strategy.

---

## 1. Parameter Provenance Ledger

The following table records the exact git history, evidence classification, and provenance status for every parameter governing the `DIRECTIONAL_FIDELITY_RECONSTRUCTION` strategy.

| Parameter | Value | Evidence Label | First Commit | Commit Date / Time (Local) | Source of Value | Was July–Sep Data Already Observed? | Provenance Classification |
|---|---:|---|---|---|---|:---:|:---:|
| `pullback_min_pct` | 0.005 (0.5%) | `[HYPOTHESIS]` | `3a5228b` | 2026-10-03 11:06:47 +09:00 | Mechanical proxy for minimum dip depth | **YES** (observed in run `2e9f108d` on 2026-10-02) | `POST_HOC_SPECIFIED` |
| `pullback_max_pct` | 0.030 (3.0%) | `[HYPOTHESIS]` | `3a5228b` | 2026-10-03 11:06:47 +09:00 | Mechanical proxy to avoid knife-catching | **YES** (observed in run `2e9f108d` on 2026-10-02) | `POST_HOC_SPECIFIED` |
| `stabilization_threshold` | 0.35 (35%) | `[HYPOTHESIS]` | `3a5228b` | 2026-10-03 11:06:47 +09:00 | Proxy for intraday bar bottoming wick | **YES** (observed in run `2e9f108d` on 2026-10-02) | `POST_HOC_SPECIFIED` |
| `swing_target_atr` | 2.5x ATR | `[HYPOTHESIS]` | `3a5228b` | 2026-10-03 11:06:47 +09:00 | Discretionary swing target proxy | **YES** (observed in run `2e9f108d` on 2026-10-02) | `POST_HOC_SPECIFIED` |
| `swing_stop_atr` | 1.5x ATR | `[HYPOTHESIS]` | `3a5228b` | 2026-10-03 11:06:47 +09:00 | Discretionary swing stop proxy | **YES** (observed in run `2e9f108d` on 2026-10-02) | `POST_HOC_SPECIFIED` |
| `order_execution_style` | `"stop_limit"` | `[HYPOTHESIS]` | `3a5228b` | 2026-10-03 11:06:47 +09:00 | Entry stop-limit simulation proxy | **YES** (observed in run `2e9f108d` on 2026-10-02) | `POST_HOC_SPECIFIED` |
| `trend_window` | 60 bars (1 hour) | `[DERIVED]` | `0d2adbc` | 2026-10-02 15:14:05 UTC | Rolling trend alignment proxy | **YES** (observed in run `fad5c527` on 2026-10-02) | `POST_HOC_SPECIFIED` |
| `sector_filter` | `True` | `[DERIVED]` | `0d2adbc` | 2026-10-02 15:14:05 UTC | Semiconductor cycle alignment | **YES** (observed in run `fad5c527` on 2026-10-02) | `POST_HOC_SPECIFIED` |
| `relative_volume_filter` | `True` (>= 0.5) | `[ASSUMPTION]` | `0d2adbc` | 2026-10-02 15:14:05 UTC | Intraday liquidity proxy | **YES** (observed in run `fad5c527` on 2026-10-02) | `POST_HOC_SPECIFIED` |
| `event_filter` | `False` | `[ASSUMPTION]` | `0d2adbc` | 2026-10-02 15:14:05 UTC | Inactive event blackout filter | **YES** (observed in run `fad5c527` on 2026-10-02) | `POST_HOC_SPECIFIED` |

---

## 2. Evaluation Against Epistemic Standards

### 2.1 Why `PRE_SPECIFIED` Cannot Be Claimed
A parameter may only be classified as `PRE_SPECIFIED` if indisputable git commit or cryptographic hash evidence demonstrates that the value was locked into the repository prior to observing performance on the evaluation dataset. 
Because the July 1 – September 30, 2026 dataset was ingested and evaluated in runs `fad5c527` and `2e9f108d` on 2026-10-02, any parameter introduced or refined in Phase H (commits `3a5228b` and later) is by definition `POST_HOC_SPECIFIED`.

### 2.2 Strict Prohibition on Re-Tuning
Per Section 5 of `GEMINI_PHASE_H_POST_RUN_CORRECTION.md`:
> *"If any key directional parameter is `POST_HOC_SPECIFIED` or `UNKNOWN`, do **not** rerun the strategy to search for replacements. Instead, downgrade the interpretation of the Phase H performance result accordingly. The goal is provenance, not optimization."*

Consequently:
1. No parameter tuning was or will be performed.
2. The directional parameters are frozen as documented.
3. The research conclusion explicitly acknowledges that these parameters represent post-hoc deterministic hypotheses.

---

## 3. Impact on Research Conclusions

1. **Trade Count Plausibility:** The fact that the directional fidelity model generated 1,334 trades (closely matching the source's reported ~1,300+ trades) is a descriptive plausibility check only. Because parameters are `POST_HOC_SPECIFIED`, trade count similarity **does not constitute validation** of the strategy.
2. **Holding Time Diagnostics:** The increase in median hold time from 2.0 minutes to 8.0 minutes represents reduced high-frequency churn relative to the z-score baseline, but does **not** prove that the Reddit trader held positions for similar durations.
3. **Research Status:**
   - `FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED`
   - `PRISTINE_OOS = UNAVAILABLE`
