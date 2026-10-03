"""Reddit Behavioral Replication V2 End-to-End Backtest Engine.

Wires the complete V2 process:
Historical Bars (MU, SNDK, SKHY)
-> Feature Calculation
-> V2 Signal Generation (6-stage progression)
-> Order Generation (No-Lookahead: signal at t close, fill at t+1)
-> ExecutionSimulator (Slippage, commissions, liquidity limits, stop-limits)
-> V2PortfolioEngine (Persistent core + tactical sleeve + margin debt/interest)
-> Equity curve & Component Attribution Reconciliation
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from tactical_engine.config import CostConfig
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType, SignalIntent
from tactical_engine.execution.simulator import ExecutionSimulator
from tactical_engine.portfolio.v2_portfolio import V2PortfolioEngine
from tactical_engine.signals.v2_signals import (
    V2DirectionalConfig,
    V2SignalGenerator,
)


class V2TradeRecord(BaseModel):
    trade_id: str
    symbol: str
    sleeve: str  # "CORE" or "TACTICAL"
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    pre_slippage_pnl: float
    realized_pnl: float
    commission: float
    slippage: float
    holding_time_minutes: float
    exit_reason: str


class V2BacktestResult(BaseModel):
    mode: Literal["V2-A", "V2-B", "V2-C"]
    initial_cash: float
    final_equity: float
    total_net_pnl: float
    total_return_pct: float
    max_drawdown_pct: float

    # Core metrics
    core_starting_value: float
    core_ending_value: float
    core_realized_pnl: float
    core_unrealized_pnl: float

    # Tactical metrics
    tactical_trade_count: int = 0
    tactical_adds_count: int = 0
    tactical_partial_exits_count: int = 0
    tactical_full_exits_count: int = 0
    tactical_reloads_count: int = 0
    tactical_realized_pnl: float = 0.0
    tactical_unrealized_pnl: float = 0.0
    tactical_win_rate_pct: float = 0.0
    tactical_median_holding_minutes: float = 0.0

    # Margin metrics
    peak_margin_debt: float = 0.0
    total_margin_interest: float = 0.0
    margin_call_count: int = 0
    forced_liquidation_count: int = 0

    # Cost breakdown
    pre_slippage_pnl: float = 0.0
    total_commission_paid: float = 0.0
    total_slippage_paid: float = 0.0
    reconciliation_discrepancy: float = 0.0
    reconciles_cleanly: bool = True

    # Series
    timestamps: list[str] = Field(default_factory=list)
    equity_curve: list[float] = Field(default_factory=list)
    trades: list[V2TradeRecord] = Field(default_factory=list)


def run_v2_backtest(
    data: dict[str, list[Bar]],
    mode: Literal["V2-A", "V2-B", "V2-C"] = "V2-B",
    initial_cash: float = 100_000.0,
    core_allocation_pct: float = 0.60,
    signal_config: V2DirectionalConfig | None = None,
    cost_config: CostConfig | None = None,
    margin_interest_rate_annual: float = 0.05,
    max_leverage: float = 2.0,
) -> V2BacktestResult:
    """Runs end-to-end V2 simulation across historical bars.

    Modes:
    - V2-A: Core Only (60% normalized core held static, 0 tactical trades, unlevered).
    - V2-B: Core + Tactical (60% core + tactical scalps/reloads, cash funded).
    - V2-C: Core + Tactical + Margin (same as V2-B with 2.0x leverage and margin financing).
    """
    signal_cfg = signal_config or V2DirectionalConfig()
    cost_cfg = cost_config or CostConfig(equity_commission_bps=0.0, equity_slippage_bps=5.0)

    # 1. Enforce Clean Headline Universe: Strictly MU, SNDK, SKHY
    disallowed = [s for s in data if s not in {"MU", "SNDK", "SKHY"}]
    if disallowed:
        raise ValueError(
            f"Input data contains non-headline symbols {disallowed}. "
            "Default V2 headline universe is strictly MU, SNDK, SKHY. "
            "USD, candidate 2x ETFs, KXIAY, and Asian tickers are strictly excluded."
        )
    headline_symbols = [s for s in ["MU", "SNDK", "SKHY"] if s in data]
    if not headline_symbols:
        raise ValueError("No eligible core symbols (MU, SNDK, SKHY) found in input data")

    # 2. Build DataFrames for feature / regime checks
    dfs: dict[str, pd.DataFrame] = {}
    for sym in headline_symbols:
        bars = data[sym]
        records = [
            {
                "timestamp": b.timestamp,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
            }
            for b in bars
        ]
        df = pd.DataFrame(records)
        df.sort_values("timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)
        dfs[sym] = df

    # Map timestamps to index in DataFrame
    ts_to_idx: dict[str, dict[datetime, int]] = {}
    for sym, df in dfs.items():
        ts_to_idx[sym] = {ts: idx for idx, ts in enumerate(df["timestamp"])}

    # 3. Initialize V2 Portfolio Engine
    actual_max_leverage = max_leverage if mode == "V2-C" else 1.0
    portfolio = V2PortfolioEngine(
        initial_cash=initial_cash,
        margin_interest_rate_annual=margin_interest_rate_annual if mode == "V2-C" else 0.0,
        maintenance_ratio=0.25,
        max_leverage=actual_max_leverage,
    )
    simulator = ExecutionSimulator(cost_config=cost_cfg)
    signal_gen = V2SignalGenerator(config=signal_cfg)

    # 4. Chronological Timeline Alignment
    timeline_set: set[datetime] = set()
    for sym in headline_symbols:
        for b in data[sym]:
            timeline_set.add(b.timestamp)
    timeline = sorted(timeline_set)

    bar_map: dict[datetime, dict[str, Bar]] = {}
    for sym in headline_symbols:
        for b in data[sym]:
            if b.timestamp not in bar_map:
                bar_map[b.timestamp] = {}
            bar_map[b.timestamp][sym] = b

    # 5. Core Initialization (Normalized 60% Core Scenario)
    core_initialized = False
    core_target_per_symbol = (initial_cash * core_allocation_pct) / len(headline_symbols)

    pending_orders: list[Order] = []
    trade_records: list[V2TradeRecord] = []
    equity_curve: list[float] = []
    timestamp_strings: list[str] = []

    tactical_entry_meta: dict[str, list[dict]] = {sym: [] for sym in headline_symbols}
    tactical_adds_count = 0
    tactical_partial_exits_count = 0
    tactical_full_exits_count = 0
    tactical_reloads_count = 0
    margin_call_count = 0
    forced_liquidation_count = 0
    peak_margin_debt = 0.0

    last_ts: datetime | None = None
    latest_prices: dict[str, float] = {}

    for t in timeline:
        current_bars = bar_map.get(t, {})
        for sym, b in current_bars.items():
            latest_prices[sym] = b.close

        # Accrue financing interest if cash is negative (mode V2-C)
        if last_ts is not None and mode == "V2-C":
            elapsed = (t - last_ts).total_seconds()
            if elapsed > 0:
                portfolio.accrue_financing(elapsed)

        debt = portfolio.margin_debt
        if debt > peak_margin_debt:
            peak_margin_debt = debt

        # Day 1: Initialize Persistent Core at Open
        if not core_initialized and len(current_bars) == len(headline_symbols):
            for sym in headline_symbols:
                b = current_bars[sym]
                shares = float(int(core_target_per_symbol / b.open))
                if shares > 0:
                    comm = shares * b.open * (cost_cfg.equity_commission_bps / 10_000.0)
                    portfolio.open_or_add_core(
                        symbol=sym,
                        quantity=shares,
                        price=b.open,
                        commission=round(comm, 4),
                    )
            core_initialized = True

        # Process Pending Orders (No-Lookahead: Signal generated at t-1 filled at t)
        unfilled_orders: list[Order] = []
        for order in pending_orders:
            bar = current_bars.get(order.symbol)
            if bar is None:
                unfilled_orders.append(order)
                continue

            fill = simulator.execute_order(order=order, bar=bar)
            if fill is not None:
                if fill.side == OrderSide.BUY:
                    # Tactical Add
                    cost = fill.quantity * fill.price
                    # Check cash constraint if unlevered mode
                    can_buy = True
                    if mode == "V2-B" and (portfolio.cash - cost - fill.commission) < 0:
                        can_buy = False
                    elif mode == "V2-C" and portfolio.get_buying_power(latest_prices) < cost:
                        can_buy = False

                    if can_buy:
                        portfolio.tactical_add(
                            symbol=fill.symbol,
                            quantity=fill.quantity,
                            price=fill.price,
                            commission=fill.commission,
                            slippage=fill.slippage,
                        )
                        tactical_entry_meta[fill.symbol].append(
                            {
                                "entry_time": fill.timestamp,
                                "entry_price": fill.price,
                                "quantity": fill.quantity,
                                "commission": fill.commission,
                                "slippage": fill.slippage,
                            }
                        )
                        tactical_adds_count += 1
                        if "reload" in order.tag:
                            tactical_reloads_count += 1

                elif fill.side == OrderSide.SELL:
                    # Tactical Reduce / Exit
                    tact_pos = portfolio.tactical_positions.get(fill.symbol)
                    if tact_pos and tact_pos.quantity > 0:
                        qty_to_reduce = min(fill.quantity, tact_pos.quantity)
                        portfolio.tactical_reduce(
                            symbol=fill.symbol,
                            quantity=qty_to_reduce,
                            price=fill.price,
                            commission=fill.commission,
                            slippage=fill.slippage,
                        )
                        # FIFO matching for trade record
                        remaining_reduce = qty_to_reduce
                        while remaining_reduce > 0 and tactical_entry_meta[fill.symbol]:
                            first_entry = tactical_entry_meta[fill.symbol][0]
                            match_qty = min(remaining_reduce, first_entry["quantity"])
                            first_entry["quantity"] -= match_qty
                            remaining_reduce -= match_qty

                            td = fill.timestamp - first_entry["entry_time"]
                            elapsed_sec = td.total_seconds()
                            hold_mins = elapsed_sec / 60.0
                            diff_p = fill.price - first_entry["entry_price"]
                            pre_pnl = match_qty * diff_p
                            trade_records.append(
                                V2TradeRecord(
                                    trade_id=str(uuid.uuid4())[:8],
                                    symbol=fill.symbol,
                                    sleeve="TACTICAL",
                                    entry_time=first_entry["entry_time"],
                                    exit_time=fill.timestamp,
                                    entry_price=first_entry["entry_price"],
                                    exit_price=fill.price,
                                    quantity=match_qty,
                                    pre_slippage_pnl=pre_pnl,
                                    realized_pnl=diff_p * match_qty,
                                    commission=fill.commission * (match_qty / fill.quantity),
                                    slippage=fill.slippage * (match_qty / fill.quantity),
                                    holding_time_minutes=hold_mins,
                                    exit_reason=order.tag,
                                )
                            )
                            if first_entry["quantity"] <= 1e-6:
                                tactical_entry_meta[fill.symbol].pop(0)

                        if "partial" in order.tag:
                            tactical_partial_exits_count += 1
                        else:
                            tactical_full_exits_count += 1

        pending_orders = []  # Discard or update orders

        # Margin maintenance & forced liquidation check in V2-C
        if mode == "V2-C" and portfolio.is_margin_call(latest_prices):
            margin_call_count += 1
            liq_orders = portfolio.generate_margin_liquidation_orders(latest_prices, timestamp=t)
            for lo in liq_orders:
                lbar = current_bars.get(lo.symbol)
                if lbar:
                    lfill = simulator.execute_order(order=lo, bar=lbar)
                    if lfill:
                        forced_liquidation_count += 1
                        if lo.symbol in portfolio.tactical_positions:
                            portfolio.tactical_reduce(
                                lo.symbol,
                                lfill.quantity,
                                lfill.price,
                                lfill.commission,
                                lfill.slippage,
                            )
                        elif lo.symbol in portfolio.core_positions:
                            portfolio.reduce_core(
                                lo.symbol,
                                lfill.quantity,
                                lfill.price,
                                lfill.commission,
                                lfill.slippage,
                            )

        # Generate fresh signals for next bar if tactical sleeve enabled
        if mode in ("V2-B", "V2-C"):
            for sym in headline_symbols:
                b = current_bars.get(sym)
                if b is None:
                    continue
                df = dfs[sym]
                idx = ts_to_idx[sym].get(t, -1)
                if idx < 0:
                    continue

                tact_pos = portfolio.tactical_positions.get(sym)
                cur_tact_shares = tact_pos.quantity if tact_pos else 0.0

                intent: SignalIntent | None = signal_gen.process_bar(
                    bar=b,
                    df=df,
                    current_idx=idx,
                    current_tactical_shares=cur_tact_shares,
                )

                if intent is not None:
                    if intent.action == "ENTER_LONG":
                        # Tactical size: ~10% of equity
                        current_eq = max(10_000.0, portfolio.get_equity(latest_prices))
                        target_tact_dollars = current_eq * 0.10 * intent.strength
                        order_shares = float(int(target_tact_dollars / b.close))
                        if order_shares > 0:
                            pending_orders.append(
                                Order(
                                    order_id=str(uuid.uuid4())[:8],
                                    symbol=sym,
                                    timestamp=t,
                                    side=OrderSide.BUY,
                                    order_type=OrderType.MARKET,
                                    quantity=order_shares,
                                    stop_loss_price=intent.stop_price,
                                    target_price=intent.target_price,
                                    tag=intent.reason,
                                )
                            )

                    elif intent.action == "EXIT_LONG" and cur_tact_shares > 0:
                        raw_exit = float(int(cur_tact_shares * intent.strength))
                        exit_shares = raw_exit or cur_tact_shares
                        pending_orders.append(
                            Order(
                                order_id=str(uuid.uuid4())[:8],
                                symbol=sym,
                                timestamp=t,
                                side=OrderSide.SELL,
                                order_type=OrderType.MARKET,
                                quantity=exit_shares,
                                tag=intent.reason,
                            )
                        )

        # Mark-to-Market Record
        cur_eq = portfolio.get_equity(latest_prices)
        equity_curve.append(cur_eq)
        timestamp_strings.append(t.isoformat())
        last_ts = t

    # 6. Reconcile P&L and Calculate Summary Performance
    recon = portfolio.reconcile_pnl_attribution(latest_prices)

    ending_equity = portfolio.get_equity(latest_prices)
    net_pnl = ending_equity - initial_cash
    ret_pct = (net_pnl / initial_cash) * 100.0

    # Drawdown
    eq_arr = np.array(equity_curve)
    peaks = np.maximum.accumulate(eq_arr)
    drawdowns = (peaks - eq_arr) / peaks
    max_dd_pct = float(np.max(drawdowns)) * 100.0 if len(drawdowns) > 0 else 0.0

    core_starting = sum(p.quantity * p.avg_price for p in portfolio.core_positions.values())
    core_ending = sum(
        p.market_value(latest_prices.get(sym, p.avg_price))
        for sym, p in portfolio.core_positions.items()
    )

    tact_wins = [tr for tr in trade_records if tr.realized_pnl > 0]
    win_rate = (len(tact_wins) / len(trade_records) * 100.0) if trade_records else 0.0
    hold_times = [tr.holding_time_minutes for tr in trade_records]
    median_hold = float(np.median(hold_times)) if hold_times else 0.0

    return V2BacktestResult(
        mode=mode,
        initial_cash=initial_cash,
        final_equity=ending_equity,
        total_net_pnl=net_pnl,
        total_return_pct=ret_pct,
        max_drawdown_pct=max_dd_pct,
        core_starting_value=core_starting,
        core_ending_value=core_ending,
        core_realized_pnl=recon["core_realized_pnl"],
        core_unrealized_pnl=recon["core_unrealized_pnl"],
        tactical_trade_count=len(trade_records),
        tactical_adds_count=tactical_adds_count,
        tactical_partial_exits_count=tactical_partial_exits_count,
        tactical_full_exits_count=tactical_full_exits_count,
        tactical_reloads_count=tactical_reloads_count,
        tactical_realized_pnl=recon["tactical_realized_pnl"],
        tactical_unrealized_pnl=recon["tactical_unrealized_pnl"],
        tactical_win_rate_pct=win_rate,
        tactical_median_holding_minutes=median_hold,
        peak_margin_debt=peak_margin_debt,
        total_margin_interest=portfolio.financing_interest_paid,
        margin_call_count=margin_call_count,
        forced_liquidation_count=forced_liquidation_count,
        pre_slippage_pnl=sum(tr.pre_slippage_pnl for tr in trade_records),
        total_commission_paid=portfolio.commissions_paid,
        total_slippage_paid=portfolio.slippage_paid,
        reconciliation_discrepancy=recon["discrepancy"],
        reconciles_cleanly=recon["reconciles"],
        timestamps=timestamp_strings,
        equity_curve=equity_curve,
        trades=trade_records,
    )
