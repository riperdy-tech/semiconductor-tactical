# Reddit Behavioral Replication V2 — U.S. Instrument Universe Specification

## 1. Scope & Architecture Mandate

Phase J explicitly confines V2 execution to the **U.S. market**. Direct execution on Asian exchanges (Korea Exchange and Tokyo Stock Exchange) is strictly **out of scope** for this phase:

```
DIRECT_ASIA_REPLICATION_STATUS = OUT_OF_SCOPE_FOR_V2
```

Direct Korean and Japanese market mechanics involve distinct trading hours, currency FX (KRW/JPY), foreign market access rules, and local settlement conventions that cannot be faithfully merged into a U.S. trading session without creating fictional overnight or synthetic fills.

---

## 2. Core Observed U.S. Equities

These instruments were explicitly named by the Reddit source ("traded SNDK, MU, and SKHY") and represent the primary assets for persistent core inventory and tactical swing trading:

| Ticker | Company / Issuer | Instrument Type | Exchange / Venue | Source Status | Data Provider Status | Notes |
|---|---|---|---|---|---|---|
| **MU** | Micron Technology, Inc. | Common Stock | NASDAQ | `SOURCE_IDENTIFIED` | **VALIDATED** | Core U.S. memory bellwether (DRAM & NAND). Full 1-min RTH data verified. |
| **SNDK** | SanDisk Corporation | Common Stock | NASDAQ | `SOURCE_IDENTIFIED` | **VALIDATED** | Core NAND flash memory equity. Full 1-min RTH data verified. |
| **SKHY** | SK Hynix Inc. American Depositary Receipt | Sponsored ADR (1:1) | OTC US (Pink/OTCQX) | `SOURCE_IDENTIFIED` | **VALIDATED** | Primary U.S.-traded vehicle for SK hynix exposure named by source. Verified U.S. intraday data. |

---

## 3. Conditional U.S. ADR Proxy: KXIAY

The Reddit trader mentioned trading Kioxia in Tokyo. For the U.S.-only research scope, **KXIAY** is evaluated as a potential access proxy:

- **Instrument**: Kioxia Holdings Corporation ADR
- **Exchange Venue**: **U.S. Over-the-Counter (OTC)**
- **Depositary Receipt Ratio**: **1:10** (1 ADR = 10 Ordinary Japanese Shares)
- **Official Listing Status Confirmation**: Kioxia Holdings Corporation officially confirmed in a press release on **September 15, 2026** that while an American Depositary Shares (ADS) listing on a U.S. national securities exchange had been contemplated, all specific details (including exchange venue, timing, and terms) **remained undecided**.
- **Research Rules & Constraints**:
  1. **Never describe KXIAY as Nasdaq-listed or NYSE-listed**. It is strictly an OTC ADR.
  2. KXIAY is a `CANDIDATE_PROXY` / `HYPOTHESIS` for the source's Tokyo Kioxia activity, not primary evidence that the Reddit trader traded KXIAY.
  3. **Data Gate**: Ingestion and coverage for KXIAY are currently `UNVALIDATED` (0 bars ingested). KXIAY must be excluded from backtest executions until a certified historical U.S. OTC intraday dataset with verified liquidity is acquired.

---

## 4. U.S.-Listed 2x Leveraged ETF Candidates

The source stated they traded "2x ETFs on memory names." In the U.S. market, multiple leveraged single-stock products exist. V2 inventories all candidates and enforces strict evidence separation:

| Ticker | Product Name | Underlying Asset | Leverage | Exchange | Inception Date | Epistemic Status | Data Status |
|---|---|---|---|---|---|---|---|
| **SKUU** | Direxion Daily SK hynix Bull 2X Shares | SK hynix (SKHY) | +2.0x | NYSE Arca | 2024-03-15 | `CANDIDATE_PROXY` | `UNVALIDATED` |
| **SKHU** | GraniteShares 2x Long SK hynix Daily ETF | SK hynix | +2.0x | NASDAQ | 2024-05-20 | `CANDIDATE_PROXY` | `UNVALIDATED` |
| **SKHL** | Tradr 2X Long SK Hynix Daily ETF | SK hynix | +2.0x | BATS | 2024-06-11 | `CANDIDATE_PROXY` | `UNVALIDATED` |
| **MUU** | Direxion Daily Micron Bull 2X Shares | Micron (MU) | +2.0x | NYSE Arca | 2024-04-10 | `CANDIDATE_PROXY` | `UNVALIDATED` |
| **SNDG** | Leverage Shares 2x Long SanDisk Daily ETF | SanDisk (SNDK) | +2.0x | NASDAQ | 2024-08-01 | `CANDIDATE_PROXY` | `UNVALIDATED` |
| **SNDU** | GraniteShares 2x Long SanDisk Daily ETF | SanDisk (SNDK) | +2.0x | NASDAQ | 2024-08-15 | `CANDIDATE_PROXY` | `UNVALIDATED` |
| **SNXX** | Tradr 2X Long SanDisk Daily ETF | SanDisk (SNDK) | +2.0x | BATS | 2024-08-20 | `CANDIDATE_PROXY` | `UNVALIDATED` |

### Classification Invariant:
None of the above 2x products are explicitly confirmed by ticker in the primary source. Therefore, they are classified as **`CANDIDATE_PROXY`**. No candidate proxy may be promoted to `SOURCE_IDENTIFIED` without verifiable primary source documentation.

---

## 5. Quarantining the Generic USD Semiconductor ETF

- **Ticker**: **USD** (ProShares Ultra Semiconductors)
- **Underlying**: Dow Jones U.S. Semiconductors Index (broad sector basket, heavily weighted to NVDA, AVGO, QCOM, etc.)
- **Leverage**: +2.0x Daily
- **Data Status**: Ingested in Phase 0-H with 81.53% bar coverage and 4,610 zero-trade minutes during RTH.
- **Strict Protocol Mandate**:
  **USD is NOT a memory single-stock product.** It is a generic semiconductor ETF. The Reddit trader specifically discussed single-stock memory plays (MU, SNDK, SK hynix). USD is strictly **QUARANTINED** from the headline source-replication research results. It may only be evaluated as an auxiliary ablation benchmark.

---

## 6. Excluded Direct Asian Venues

To eliminate any ambiguity regarding international execution, the following instruments are formally registered as excluded:

| Ticker | Issuer | Listing Exchange | Local Currency | V2 Replication Status |
|---|---|---|---|---|
| **000660.KS** | SK hynix Inc. | Korea Exchange (KRX) | KRW | `OUT_OF_SCOPE_FOR_V2` |
| **285A.T** | Kioxia Holdings Corporation | Tokyo Stock Exchange (TSE) | JPY | `OUT_OF_SCOPE_FOR_V2` |

These venues represent the unmodeled international component of the source's behavior and are reserved for a potential future multi-currency research engine (V3).
