# Post-First-Run Acceptance Tests

## A — Evidence integrity

- [ ] First real-data report preserved.
- [ ] Dataset ID matches dataset_manifest.
- [ ] Aggregate hash matches run evidence.
- [ ] Exact git SHA recorded.
- [ ] Exact config path/hash recorded.
- [ ] No .env or API key tracked.

## B — ATR exit correctness

- [ ] Entry ATR/stop/target stored at entry.
- [ ] Later ATR expansion cannot move fixed stop.
- [ ] Later ATR contraction cannot move fixed stop.
- [ ] Later ATR changes cannot move fixed target.
- [ ] Position sizing uses the same stored stop.
- [ ] Regression tests cover volatility expansion and contraction.

## C — Signal semantics

- [ ] Variant sector-filter state documented.
- [ ] Trend-confirmation state documented.
- [ ] Pullback threshold documented.
- [ ] Relative-volume threshold documented.
- [ ] Event-filter state documented.
- [ ] Current implementation labeled as mechanical hypothesis where appropriate.
- [ ] No silent strategy substitution.

## D — Trade-frequency diagnostics

- [ ] Total trades.
- [ ] Trades/day.
- [ ] Trades/symbol/day.
- [ ] Median holding time.
- [ ] Signal count versus filled-entry count.
- [ ] Simultaneous positions.
- [ ] Re-entry count.

## E — OOS protocol

- [ ] Start date explicit.
- [ ] Train end explicit.
- [ ] Validation end explicit.
- [ ] Test start explicit.
- [ ] End date explicit.
- [ ] Partitions disjoint.
- [ ] Test period untouched during parameter selection.
- [ ] Boundaries appear in report and run manifest.

## F — Cost decomposition

- [ ] Gross P&L.
- [ ] Commission.
- [ ] Slippage.
- [ ] Market-impact proxy.
- [ ] Financing.
- [ ] Net P&L.
- [ ] Costs divided by gross P&L.

## G — Software quality

- [ ] pytest passes.
- [ ] ruff passes.
- [ ] CI passes.
- [ ] Historical data gate still refuses unverified datasets.
- [ ] Canonical runner remains deterministic.
- [ ] No secret committed.
