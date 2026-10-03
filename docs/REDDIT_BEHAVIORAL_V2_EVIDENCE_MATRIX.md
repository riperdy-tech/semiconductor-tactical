# Reddit Behavioral Replication V2 — Evidence Matrix

## Epistemic Hierarchy

All behavioral elements in the V2 research architecture are strictly partitioned by epistemic status per repository rules:

- **`OBSERVED`**: Explicitly stated or documented by the primary Reddit source post and author comments.
- **`DERIVED`**: Direct mechanical or financial deduction necessarily resulting from observed source behavior.
- **`HYPOTHESIS`**: Plausible proxy rule or structural mechanism proposed for research, not asserted as primary truth.
- **`ASSUMPTION`**: Engineering parameter or boundary condition required where the source left the detail unspecified.
- **`UNVERIFIED`**: Claimed or implied behavior that cannot be confirmed with primary data or verifiable execution logs.

---

## 1. Comprehensive Component Evidence Ledger

| # | Behavioral / Structural Component | Source Evidence Citation | Epistemic Label | Deterministic Model Implication | Data Gate Requirement | V2 Validation Status |
|---|---|---|---|---|---|---|
| 1 | **Core Memory Equities (MU, SNDK, SKHY)** | "traded SNDK, MU, and SKHY" (Source post & comments) | `OBSERVED` | Model as primary persistent inventory and tactical trading targets. | 1-minute U.S. RTH intraday equity bars from verified provider. | **VALIDATED** (Ingested & audited) |
| 2 | **Direct KRX SK hynix Trading (000660)** | Mentioned trading Korean market / SK hynix in Seoul | `OBSERVED` | Direct execution on KRX is explicitly quarantined from U.S. V2 scope. | KRX intraday tick/bar data with foreign FX conversion. | **OUT_OF_SCOPE_FOR_V2** (`DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2`) |
| 3 | **Tokyo Kioxia Common Trading (285A.T)** | Mentioned trading Kioxia in Tokyo | `OBSERVED` | Tokyo execution is unmodeled in V2; direct Asia execution out of scope. | Tokyo Stock Exchange tick/bar data with JPY conversion. | **OUT_OF_SCOPE_FOR_V2** (`DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2`) |
| 4 | **KXIAY U.S. OTC ADR Proxy** | Kioxia U.S. OTC ADR (1:10 ratio). Kioxia official release (2026-09-15) confirmed U.S. exchange ADS listing remains undecided. | `HYPOTHESIS` / `DERIVED` | U.S.-market access proxy for Tokyo Kioxia activity. Never describe as Nasdaq-listed. Conditional inclusion only when data is sufficient. | U.S. OTC intraday bar feed with verified liquidity metrics. | **UNVALIDATED** (Data provider pending; zero bars ingested) |
| 5 | **U.S.-Listed 2x Leveraged ETFs** | "traded 2x ETFs on memory names" | `OBSERVED` (generic 2x concept) / `CANDIDATE_PROXY` (specific tickers) | Inventory candidate products (SKUU, SKHU, SKHL, MUU, SNDG, SNDU, SNXX). Exact ticker unconfirmed. | U.S. ETF intraday bars and split/dividend adjustments. | **UNVALIDATED** (Candidate proxy inventory cataloged; data pending) |
| 6 | **Generic USD Semiconductor ETF** | ProShares Ultra Semiconductors (generic sector 2x ETF) | `CANDIDATE_PROXY` | Strictly quarantined from headline replication unless primary evidence proves trader used it. | Validated in Phase 0-H (81.5% coverage; 4,610 zero-trade bars). | **QUARANTINED_FROM_HEADLINE** |
| 7 | **Persistent Core Inventory** | Held massive long positions across cycle; did not exit completely on intraday signals | `OBSERVED` | Portfolio process Layer 1: Core shares held continuously; tactical exits never liquidate core. | Account inventory tracking with separate cost basis. | **VALIDATED** (`src/tactical_engine/portfolio/v2_portfolio.py`) |
| 8 | **Tactical Scalping & Swing Sleeve** | "scalped intraday moves and swung multi-day momentum" | `OBSERVED` | Portfolio process Layer 2: Independent tactical sleeve with add, reload, partial reduction, and re-entry. | Order-level sleeve tag and execution attribution. | **VALIDATED** (`src/tactical_engine/portfolio/v2_portfolio.py`) |
| 9 | **Covered-Call Overlay on Owned Shares** | Sold short-dated calls during sharp upward impulses | `OBSERVED` | Covered calls must be attached to owned, unencumbered core shares. Contracts <= shares / 100. | Historical option chains with bid/ask/volume/OI. | **VALIDATED_MECHANICS** / **DATA_GATED_AS_UNVALIDATED** (Pending chain data) |
| 10 | **Covered-Call Repurchase on Pullbacks** | "bought back calls when the underlying pulled back" | `OBSERVED` | Covered call state machine: strength -> sell call -> underlying pulls back -> buy back call -> unlock shares. | Intraday option bid/ask quotes paired with underlying timestamps. | **VALIDATED_MECHANICS** / **DATA_GATED_AS_UNVALIDATED** |
| 11 | **Theoretical Black-Scholes Options Pricing** | Disallowed by AGENTS.md Section 7 | `HYPOTHESIS` (disallowed) | Never substitute Black-Scholes fills for executable market prices. | Real option chain quotes. | **REJECTED_AS_FICTIONAL** |
| 12 | **Account-Level Margin Debt & Leverage** | Trader maintained large margin debt to finance positions | `OBSERVED` | Margin financing applies at account level across core + tactical positions. Financing interest accrued to cash. | Margin interest calculation (5% annual) and maintenance check. | **VALIDATED** (`src/tactical_engine/portfolio/v2_portfolio.py`) |
| 13 | **Forced Liquidation Prioritization** | Margin call mechanics when equity < maintenance | `DERIVED` | In margin deficit, liquidate tactical sleeve first to protect persistent core holdings. | Account maintenance ratio (25%) monitoring. | **VALIDATED** (`src/tactical_engine/portfolio/v2_portfolio.py`) |
| 14 | **Level 2 / Order-Book Decision Making** | "looked at Level 2 order books to time entries and gauge liquidity" | `OBSERVED` | Level 2 cannot be reproduced by OHLCV. Flagged as explicit data gate. Synthetic order books prohibited. | Historical Level-2 market depth (MBO/ITCH) records. | **UNVALIDATED** (`TRUE_LEVEL2_REPLICATION = UNVALIDATED`) |
| 15 | **Stop-Limit Order Execution** | Mentioned using stop-limit orders | `OBSERVED` (order mechanism) / `HYPOTHESIS` (directional entry rule) | Support trigger, limit price, and gap-through non-fill behavior. Do not assume every stop-limit was an entry. | Tick-level high/low order-book sequencing. | **VALIDATED_MECHANICS** (`stop_limit.py`) |
| 16 | **Impulse Retreat Reference (~2%)** | Source cited ~2% move as an illustrative pullback example | `OBSERVED` (economic example) / `HYPOTHESIS` (fixed entry threshold) | Reference example of magnitude, NOT a hard-coded static take-profit or entry trigger. | Pre-registered parameter family. | **PRE_REGISTERED_CANDIDATE_FAMILY** |
| 17 | **Phase H Post-Hoc Directional Parameters** | 0.5%–3% impulse, 0.35 stabilization, 1.5 ATR stop, 2.5 ATR target | `POST_HOC_SPECIFIED` | Derived post-hoc in Phase H on July–Sept sample. Must NOT be reused as pre-registered V2 parameters. | Explicit parameter provenance ledger. | **QUARANTINED_POST_HOC** |
| 18 | **Profit Withdrawals Tracking** | Mentioned withdrawing profits periodically | `OBSERVED` | Logged as separate capital transfer events. Strictly prohibited from inflating strategy returns. | Account ledger transfer records. | **VALIDATED** (`record_withdrawal` in `v2_portfolio.py`) |
| 19 | **8-Minute Holding Time** | Median duration observed in Phase H backtest | `DERIVED` (Phase H artifact) | Result of tight post-hoc intraday thresholds; does NOT reflect validated swing trading behavior. | Multi-timeframe holding analysis. | **REJECTED_AS_FIDELITY_MEASURE** |
| 20 | **Pristine Out-of-Sample Partition** | Chronological evaluation boundary | `DERIVED` | July–September was evaluated prior to freezing OOS; PRISTINE_OOS remains UNAVAILABLE for July–Sept. | Unseen future chronological dataset. | **PRISTINE_OOS_UNAVAILABLE** |

---

## 2. Research Boundary Status Summary

```
FULL_REDDIT_STRATEGY_REPLICATION = NOT_ESTABLISHED
DIRECT_ASIA_REPLICATION_STATUS    = OUT_OF_SCOPE_FOR_V2
TRUE_LEVEL2_REPLICATION          = UNVALIDATED
HISTORICAL_OPTION_CHAIN_STATUS   = UNVALIDATED
PRISTINE_OOS_STATUS              = UNAVAILABLE
```
