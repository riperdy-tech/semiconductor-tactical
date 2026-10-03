# Current Mechanical Pullback Baseline — Preservation Record

> **IMPLEMENTATION DESIGNATION:** `CURRENT_MECHANICAL_PULLBACK_BASELINE`
> 
> **MANDATORY FIDELITY NOTE:**
> This baseline is a deterministic mean-reversion implementation inspired by the source. It is not a faithful reconstruction of the full Reddit trading process.

---

## 1. Baseline Preservation Overview

This document formally records and preserves the initial historical backtest results and post-audit results produced by the tactical research engine prior to Phase H strategy fidelity reconstruction.

Under no circumstances may these runs be deleted, overwritten, or retroactively relabeled as the Reddit trader's actual strategy. They serve as an immutable benchmark for the mechanical z-score pullback hypothesis.

---

## 2. Preserved Run Records

### Run 1: Post-Audit Run (`2e9f108d`) — Primary Baseline

- **Implementation Label:** `CURRENT_MECHANICAL_PULLBACK_BASELINE`
- **Run ID:** `2e9f108d-768c-4194-a4cf-cd9fa5ecc0eb`
- **Run Timestamp UTC:** `2026-10-02T15:14:05.586399+00:00`
- **Git Commit SHA:** `0d2adbcbc8cd4612342005610ac35e0c36c32886`
- **Dataset ID:** `massive_stocks_1m_51e9b529de55`
- **Aggregate Dataset SHA-256:** `51e9b529de5556002bc3a0e1bc4fd1ee7eef06061b54c11457703d9af39b13e8`
- **Config Hash:** `0d34835d97140803`
- **Scope Classification:** `POST_HOC_HOLDOUT` (`PRISTINE_OOS_UNAVAILABLE`)
- **Report Path:** `reports/historical_comparison_2e9f108d_20261002_151405/report.md`
- **Comparison JSON Path:** `reports/historical_comparison_2e9f108d_20261002_151405/comparison_metrics.json`
- **Run Manifest Path:** `reports/historical_comparison_2e9f108d_20261002_151405/run_manifest.json`

#### Exact Configuration
```yaml
project:
  name: high-beta-tactical-1m
  timezone_report: America/New_York
  random_seed: 42

strategy:
  variant: risk_controlled
  universe:
    - MU
    - SNDK
    - SKHY
    - AMD
  two_x_etfs:
    - USD
  bar_interval: 1m

signals:
  pullback_zscore: -1.5
  trend_window: 60
  sector_filter: true
  relative_volume_filter: true
  event_filter: false

exits:
  family: atr
  target_atr: 1.0
  stop_atr: 1.0
  max_hold_minutes: 120

portfolio:
  max_symbol_weight: 0.25
  max_gross_leverage: 1.5
  max_layers: 2
  risk_per_trade_pct: 0.25

costs:
  equity_commission_bps: 0.0
  equity_slippage_bps: 5.0
  option_slippage_bps: 10.0
  market_impact_bps_per_1pct_volume: 10.0
  margin_rate_annual: 0.05

options:
  enabled: false
  max_dte: 14
  min_dte: 1
  moneyness: otm
  repurchase_rule: pullback

research:
  start: "2026-07-01T00:00:00Z"
  end: "2026-09-30T23:59:59Z"
  train_end: "2026-08-15T00:00:00Z"
  validation_end: "2026-09-01T00:00:00Z"
  test_start: "2026-09-01T00:00:00Z"
```

#### Performance Summary
| Variant | Return % | Max DD % | Trades | Win Rate | Profit Factor | Net P&L | Slippage Paid | Margin Paid |
|---|---|---|---|---|---|---|---|---|
| `literal_clone` | -98.70% | 98.70% | 4,474 | 32.1% | 0.24 | $-98,690.64 | $85,749.36 | $7.96 |
| `risk_controlled` | -92.89% | 92.89% | 5,082 | 31.8% | 0.28 | $-92,887.16 | $84,998.08 | $0.04 |
| `regime_adapted` | -34.88% | 35.10% | 1,114 | 28.8% | 0.32 | $-34,919.97 | $36,584.94 | $0.01 |

---

### Run 2: First Real Historical Run (`fad5c527`) — Pre-Audit Baseline

- **Implementation Label:** `CURRENT_MECHANICAL_PULLBACK_BASELINE` (Pre-Audit)
- **Run ID:** `fad5c527-803f-49b7-98cc-4564b467df09`
- **Run Timestamp UTC:** `2026-10-02T14:11:40.502316+00:00`
- **Git Commit SHA:** `9debeb7116f37ff6482a31fea8eb1be4f411be40` / `8b92171d88a2e302c0ff80f9d5f26b46a8003878`
- **Dataset ID:** `massive_stocks_1m_51e9b529de55`
- **Aggregate Dataset SHA-256:** `51e9b529de5556002bc3a0e1bc4fd1ee7eef06061b54c11457703d9af39b13e8`
- **Config Hash:** `d1967c5f58555c52`
- **Scope Classification:** `FULL_SAMPLE`
- **Report Path:** `reports/historical_comparison_fad5c527_20261002_141140/report.md`
- **Comparison JSON Path:** `reports/historical_comparison_fad5c527_20261002_141140/comparison_metrics.json`
- **Run Manifest Path:** `reports/historical_comparison_fad5c527_20261002_141140/run_manifest.json`

#### Performance Summary
| Variant | Return % | Max DD % | Trades | Win Rate | Profit Factor | Net P&L |
|---|---|---|---|---|---|---|
| `literal_clone` | -98.70% | 98.70% | 4,474 | 32.1% | 0.24 | $-98,690.64 |
| `risk_controlled` | -95.27% | 95.27% | 5,082 | 30.6% | 0.25 | $-95,274.65 |
| `regime_adapted` | -40.16% | 40.16% | 1,114 | 29.8% | 0.31 | $-40,162.74 |

---

## 3. Preservation Declaration

Both runs above remain permanently preserved on disk and in git history. They represent the empirical performance of the mechanical z-score pullback hypothesis under realistic costs, demonstrating that a 2-minute median hold time with fixed 5 bps slippage destroys equity. These results provide the foundation against which all subsequent fidelity reconstructions will be rigorously contrasted.

---

## 4. Separation of Immutable Preserved Baseline from Later Diagnostics

Per `docs/execution_plan/GEMINI_PHASE_H_POST_RUN_CORRECTION.md` Section 3, the repository enforces strict identity separation:

1. **`CURRENT_MECHANICAL_PULLBACK_BASELINE`**: Refers EXCLUSIVELY to the authoritative preserved historical baseline (Run `2e9f108d`, variant `risk_controlled`, leverage 1.0x, 1 layer, sector filter disabled, producing **-92.89% return across 5,082 trades**).
2. **`MECHANICAL_PULLBACK_SECTOR_FILTERED_DIAGNOSTIC`**: Any subsequent diagnostic evaluation that enables the sector filter on the mechanical pullback (producing **-34.88% / -35.69% across ~1,114 / 1,129 trades**) is strictly designated as a mechanical diagnostic. It must NEVER be called or substituted for `CURRENT_MECHANICAL_PULLBACK_BASELINE`.
3. **`DIRECTIONAL_FIDELITY_RECONSTRUCTION`**: Refers strictly to the frozen Phase H directional swing trading hypothesis (**-53.27% return across 1,334 trades**).

