# Erratum — Phase L Preservation Note Metadata Correction

- **Erratum Date:** 2026-10-04T19:00:00Z
- **Subject Document:** [`PHASE_L_PRESERVATION_NOTE.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/reports/fidelity_runs/phase_l_baseline_0ce2208/PHASE_L_PRESERVATION_NOTE.md)
- **Preserved Phase L Commit SHA:** `0ce2208`
- **Preserved Phase L Run ID:** `bc19e12e`
- **Authoritative Preserved Artifacts:** 
  - [`v2_historical_comparison.json`](file:///c:/Users/riper/Downloads/semiconductor-tactical/reports/fidelity_runs/phase_l_baseline_0ce2208/v2_historical_comparison.json)
  - [`V2_HISTORICAL_COMPARISON.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/reports/fidelity_runs/phase_l_baseline_0ce2208/V2_HISTORICAL_COMPARISON.md)

---

## 1. Purpose of this Erratum

The original historical document [`PHASE_L_PRESERVATION_NOTE.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/reports/fidelity_runs/phase_l_baseline_0ce2208/PHASE_L_PRESERVATION_NOTE.md) is preserved intact as historical evidence. However, its summary text contains several stale/pre-run planning draft numbers that contradict the actual metrics in the preserved canonical Phase L report and JSON.

This erratum corrects the human-readable metadata record without altering the preserved Phase L run or its underlying data artifacts.

---

## 2. Reconciled Fields

| Field Name | Stale Value in Note | Actual Preserved Phase L Value | Authoritative Source Artifact | Root Cause / Explanation |
|---|---|---|---|---|
| **Tactical Realized P&L** | `+$1,446.69` | **`-$3,830.14`** (`-3830.1411`) | `v2_historical_comparison.json` (`tactical_closed_realized_pnl`) | The stale note conflated total tactical net economic contribution (`+$1,446.69`) with closed realized P&L (`-$3,830.14`). In Phase L, closed round-trips realized `-$3,830.14` while terminal open positions contributed `+$5,276.83`. |
| **Total Portfolio Slippage** | `$1,563.81` | **`$659.07`** (`659.0697`) | `v2_historical_comparison.json` (`total_slippage_paid`) | `$1,563.81` was a preliminary placeholder from the pre-run planning outline. The actual slippage paid across the Phase L historical run was `$659.07` (`$644.47` closed trades + `$14.60` open position entry slippage). |
| **Closed Reference P&L** | `$3,010.50` | **`-$3,185.67`** (`-3185.6737`) | `v2_historical_comparison.json` (`pre_slippage_pnl`) | `$3,010.50` was a placeholder from earlier brainstorming notes. The actual unadjusted reference P&L across all closed round-trips was `-$3,185.67`. |

---

## 3. Preserved Historical Run Confirmation

This erratum applies exclusively to the metadata description in [`PHASE_L_PRESERVATION_NOTE.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/reports/fidelity_runs/phase_l_baseline_0ce2208/PHASE_L_PRESERVATION_NOTE.md). 

The archived backtest run `bc19e12e` (generated under Git SHA `0ce2208`) remains completely unchanged, with:
- **Ending Equity:** `$106,482.16` (V2-A) / `$107,928.85` (V2-B) / `$107,928.85` (V2-C)
- **Net Return:** `+6.48%` (V2-A) / `+7.93%` (V2-B) / `+7.93%` (V2-C)
- **Tactical Net Contribution:** `+$1,446.69` (+1.45% return spread)
