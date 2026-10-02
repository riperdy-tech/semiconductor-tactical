# Decisions

## 2026-10-02 — New repository boundary

**Decision:** Create a separate repo instead of extending RS2.

**Reason:** The target strategy is tactical/high-turnover and primarily market-microstructure/price-action driven. RS2 is an equity-analysis/valuation engine. Coupling them would blur test boundaries.

**Integration:** Optional RS2 regime adapter only.

## 2026-10-02 — Deterministic core

**Decision:** No LLM in signal generation or backtest accounting.

**Reason:** We need reproducibility and falsifiability. LLMs may later be used for research summarization, but not to decide simulated orders in the first version.

## 2026-10-02 — Separate literal vs risk-controlled modes

**Decision:** Preserve the source behavior as an experiment rather than silently "fixing" it.

**Reason:** If we only build a safer strategy, we cannot determine which part of the reported result came from leverage/layering versus the underlying signal.

## 2026-10-02 — Slippage and execution accounting separation

**Decision:** Market slippage is incorporated directly into the fill price (`fill.price = intended_price +/- slippage`), and trade P&L is calculated strictly using actual execution prices minus commissions. Slippage is tracked as an attribution metric rather than being deducted twice.

**Reason:** Resolves audit finding C8 where slippage was double-counted against realized P&L. Ensures exact $0.01 mathematical reconciliation between cash flow and portfolio equity.

## 2026-10-02 — Gross leverage constraint in portfolio sizing

**Decision:** Enforce `max_gross_leverage` directly at position sizing time by calculating active aggregate market value of all holdings and capping new orders by remaining gross leverage capacity.

**Reason:** Resolves audit finding C2 where leverage was a dormant configuration parameter. Prevents gross portfolio exposure from exceeding defined risk bounds regardless of symbol count.

## 2026-10-02 — Dual-benchmark regime tracking

**Decision:** Use `BenchmarkRegimeProvider` consuming both semiconductor sector (`SMH`) and broad market (`SPY`) historical series, with configurable regime filter modes (`none`, `sector`, `broad`, `combined`), and provide an optional `ExternalRegimeProvider` for external format compatibility.

**Reason:** Resolves audit finding C5 where single-ticker trend was substituted for genuine sector and broad-market regime evaluation. Keeps the engine completely self-contained.

## 2026-10-02 — Covered-call repurchase mechanics and option attribution

**Decision:** Implement explicit covered-call repurchase rules (`pullback`, `profit_target_50pct`, `expiration`) and segregate option cash flows (`options_premium_collected`, `options_realized_pnl`) from directional equity P&L. Default option simulations to `UNVALIDATED` unless backed by primary historical chain quotes.

**Reason:** Resolves audit finding C7 by accurately modeling the observed Reddit trader behavior (harvesting premium on strength and buying back on pullbacks) while upholding data integrity rules in `AGENTS.md`.

