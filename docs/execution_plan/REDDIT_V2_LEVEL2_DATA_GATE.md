# Reddit Behavioral Replication V2 — Level-2 / Order-Book Data Gate

## 1. Primary Source Evidence

The Reddit trader explicitly stated in primary post and comment threads that they:
> *"looked at Level 2 order books to time entries, spot bid walls, and gauge market liquidity before executing."*

This is an **`OBSERVED`** behavioral factor of the trader's actual decision process.

---

## 2. Hard Data Gate Mandate

Level-2 market microstructure consists of full limit-order book depth, real-time bid/ask queue sizes across price levels, order cancellations, and queue replenishment (Market-by-Order / Market-by-Price). 

Standard 1-minute OHLCV bars do **not** contain order-book depth.

**Repository Rule**:
```
TRUE_LEVEL2_REPLICATION = UNVALIDATED
```

Until genuine historical Level-2/order-book depth data (e.g., NASDAQ TotalView-ITCH / Direct Edge BookFeed) is acquired and audited:
1. **No backtest may claim to execute the trader's Level-2 decision logic.**
2. **Fabricating or synthesizing pseudo-Level-2 features from OHLCV bars is strictly prohibited.**
3. Any algorithmic rule operating solely on OHLCV data (such as bar range, volume spikes, or candle stabilization) is an engineered proxy and must be explicitly labeled **`HYPOTHESIS` / `DERIVED_PROXY`**.
4. Research reports must conspicuously disclose that the Level-2 component remains unvalidated.

---

## 3. Data Specification for Level-2 Historical Acquisition

If Level-2 data is acquired in a future phase, it must satisfy the following contract:

| Field | Description | Type / Resolution | Requirement |
|---|---|---|---|
| `timestamp` | High-precision event timestamp | Microsecond / Nanosecond UTC | Mandatory |
| `symbol` | Eligible U.S. instrument (MU, SNDK, SKHY) | Ticker string | Mandatory |
| `event_type` | Add, Cancel, Execute, Replace | Order-book event enum | Mandatory |
| `side` | Bid or Ask | Enum (`BUY`, `SELL`) | Mandatory |
| `price` | Order price level | 4-decimal float | Mandatory |
| `size` | Aggregate share depth at level | Integer share count | Mandatory |
| `depth_levels` | Visible book depth | Minimum top 5 price levels | Strongly Preferred |

---

## 4. Analytical Separation in Research Results

All research ablation results must report:
- **`V2_OHLCV_BASELINE`**: Results generated strictly from validated 1-minute OHLCV equity bars with explicit caveat that Level 2 is unmodeled.
- **`V2_LEVEL2_MICROSTRUCTURE`**: Gated as `UNVALIDATED` until verified depth data is acquired. Under no circumstances may synthetic depth metrics be substituted into the headline replication report.
