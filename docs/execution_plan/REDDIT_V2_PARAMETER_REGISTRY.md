# Reddit Behavioral Replication V2 — Pre-Registered Parameter Registry

## 1. Governance & Research Integrity Protocol

To uphold the integrity mandates established in `AGENTS.md` and Phase J:
1. **Pre-Registration Boundary**: All V2 candidate parameters and ranges must be registered, frozen, and committed before executing any V2 backtest simulation.
2. **Contamination Status**: Because the July 1–September 30, 2026 dataset has already been evaluated in prior phases, any parameter evaluated against that period is classified as `POST_HOC_SPECIFIED` with respect to that sample. The July–September sample serves strictly as a **`POST_HOC_HOLDOUT`**.
3. **No Retuning**: Running iterative optimization loops on July–September to maximize return or match the source's $550k claim is strictly prohibited.
4. **Pristine Out-of-Sample Requirement**: True out-of-sample validation requires evaluating these pre-registered parameters against unseen data (e.g., Q4 2026 / 2027) once available (`PRISTINE_OOS = UNAVAILABLE` currently).

---

## 2. Frozen Pre-Registered Parameter Ledger

| Parameter Identifier | Target Component | Registered Value / Candidate Set | Epistemic Label | Technical & Economic Rationale | Pre-Registration Commit SHA | July–Sept 2026 Contamination Status |
|---|---|---|---|---|---|---|
| `V2_CORE_ALLOC_01` | Core Portfolio | `0.60` (60% of equity) | `ASSUMPTION` | Establishes persistent inventory reflecting the bull thesis while reserving 40% margin capacity for tactical sleeve. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_CORE_REBAL_01` | Core Portfolio | `MONTHLY` | `ASSUMPTION` | Periodic rebalancing prevents runaway concentration while keeping turnover minimal. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_TACT_LEVRG_01` | Tactical Sleeve | `2.0` max gross leverage | `OBSERVED` | Reflects source's explicit statement of trading on margin and using 2x leverage. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_TACT_MRGN_01`  | Margin Account | `0.25` maintenance ratio | `DERIVED` | FINRA Rule 4210 standard minimum maintenance requirement for long equity. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_TACT_RATE_01`  | Margin Account | `0.05` (5% annual rate) | `ASSUMPTION` | Realistic institutional/prime broker margin financing benchmark. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_IMP_WIN_01`    | Tactical Impulse| `[15, 30, 60]` minutes | `HYPOTHESIS` | Intraday impulse detection windows spanning opening drive to 1-hour trend surges. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_IMP_MAG_01`    | Tactical Impulse| `[0.015, 0.020, 0.025]` | `HYPOTHESIS` | Centered on the source's illustrative ~2% move reference point. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_PB_DEPTH_01`   | Tactical Pullback| `[0.382, 0.500, 0.618]` | `HYPOTHESIS` | Standard structural auction retracement fractions of the initial impulse. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_STAB_BARS_01`  | Tactical Reclaim| `[3, 5, 8]` bars | `HYPOTHESIS` | Minimum price stabilization duration above local retracement low. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_EXIT_SCALE_01` | Tactical Exit   | `0.50` (50% partial exit)| `OBSERVED` | Scalp initial 50% on rebound to VWAP/high, leave 50% as trailing swing. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_STOP_TYPE_01`  | Tactical Stop   | `LOCAL_LOW_PIVOT` | `HYPOTHESIS` | Structural stop set just below the stabilization low, invalidating the setup. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_OPT_DTE_01`    | Covered Calls   | `[3, 5, 7]` days | `OBSERVED` | Short-dated weekly options described by source. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_OPT_DELTA_01`  | Covered Calls   | `[0.20, 0.30]` (OTM) | `ASSUMPTION` | Out-of-the-money delta targeting premium capture while permitting moderate upside. | `0772574a` | `POST_HOC_SPECIFIED` |
| `V2_OPT_REPUR_01`  | Covered Calls   | `0.50` (50% decay) OR `2% underlying drop` | `OBSERVED` | Source explicitly described repurchasing calls when underlying pulled back. | `0772574a` | `POST_HOC_SPECIFIED` |

---

## 3. Quarantined Phase H Parameters (Do Not Reuse for V2)

The following parameters from Phase H are permanently quarantined as post-hoc artifacts:
- `impulse_pct_range = [0.005, 0.030]`
- `stabilization_ratio = 0.35`
- `stop_loss_atr_mult = 1.5`
- `target_atr_mult = 2.5`
- `max_holding_bars = 120`

These values were fitted post-hoc to the sample, resulted in an unvalidated 8-minute median holding period, and are **NOT** permitted in V2 pre-registered evaluations.
