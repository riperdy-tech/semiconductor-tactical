"""Reddit Behavioral Replication V2 End-to-End Backtest Engine.

Wires the complete V2 process:
Historical Bars (MU, SNDK, SKHY)
-> Feature Calculation
-> V2 Signal Generation (6-stage progression)
-> Order Generation (No-Lookahead: signal at t close, fill at t+1 open)
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
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType
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
    entry_reference_price: float = 0.0
    exit_reference_price: float = 0.0
    quantity: float
    pre_slippage_pnl: float
    realized_pnl: float
    commission: float
    slippage: float
    entry_slippage: float = 0.0
    exit_slippage: float = 0.0
    holding_time_minutes: float
    exit_reason: str


ACCOUNTING_TOLERANCE: float = 0.001  # $0.001 (one tenth of a cent)


def is_within_accounting_tolerance(discrepancy: float) -> bool:
    """Check if an accounting discrepancy is strictly within the declared tolerance."""
    return discrepancy <= ACCOUNTING_TOLERANCE


class V2BacktestResult(BaseModel):
    mode: Literal["V2-A", "V2-B", "V2-C"]
    initial_cash: float
    final_equity: float
    total_net_pnl: float
    total_return_pct: float
    max_drawdown_pct: float

    # Core metrics
    effective_start_timestamp: str = ""
    evaluation_end_timestamp: str = ""
    core_starting_value: float
    core_ending_value: float
    core_actual_pct: float = 0.0
    core_residual_cash: float = 0.0
    core_realized_pnl: float = 0.0
    core_unrealized_pnl: float = 0.0

    # Phase L.1 Closed vs Open Attribution Fields
    closed_reference_pnl: float = 0.0
    closed_entry_slippage: float = 0.0
    closed_exit_slippage: float = 0.0
    closed_slippage: float = 0.0
    closed_commissions: float = 0.0
    closed_net_realized_pnl: float = 0.0

    open_reference_mtm: float = 0.0
    open_entry_slippage: float = 0.0
    open_entry_commissions: float = 0.0
    open_net_terminal_contribution: float = 0.0
    total_tactical_economic_contribution: float = 0.0
    tactical_total_economic_contribution: float = 0.0

    # Tactical metrics
    tactical_trade_count: int = 0
    tactical_closed_realized_pnl: float = 0.0
    tactical_terminal_unrealized_pnl: float = 0.0
    tactical_realized_pnl: float = 0.0
    tactical_unrealized_pnl: float = 0.0
    tactical_win_rate_pct: float = 0.0
    tactical_median_holding_minutes: float = 0.0

    # Trade counts breakdown
    signals_generated_count: int = 0
    order_attempts_count: int = 0
    entry_fills_count: int = 0
    reload_fills_count: int = 0
    partial_exit_fills_count: int = 0
    full_exit_fills_count: int = 0
    completed_round_trips_count: int = 0
    open_tactical_lots_count: int = 0
    open_tactical_shares_count: float = 0.0

    # Margin metrics
    peak_margin_debt: float = 0.0
    total_margin_interest: float = 0.0
    margin_call_count: int = 0
    forced_liquidation_count: int = 0
    margin_exercised: bool = False

    # Cost breakdown
    pre_slippage_pnl: float = 0.0
    total_commission_paid: float = 0.0
    total_slippage_paid: float = 0.0
    accounting_tolerance: float = ACCOUNTING_TOLERANCE
    reconciliation_discrepancy: float = 0.0
    reconciles_cleanly: bool = True

    # Backwards compatibility count aliases
    tactical_adds_count: int = 0
    tactical_reloads_count: int = 0
    tactical_partial_exits_count: int = 0
    tactical_full_exits_count: int = 0

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
    filter_to_effective_start: bool = True,
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

    # 2. Build DataFrames for feature / regime checks (full data provides warm-up)
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

    # 4. Determine Effective Common Start Timestamp
    # All headline symbols must have valid bars at the effective start
    common_ts_sets = [set(b.timestamp for b in data[sym]) for sym in headline_symbols]
    common_intersection = set.intersection(*common_ts_sets)
    if not common_intersection:
        raise ValueError(f"No common timestamps found across headline symbols {headline_symbols}")
    effective_start_timestamp = min(common_intersection)
    evaluation_end_timestamp = max(common_intersection)

    # Align simulation timeline: either filtered to common start or full
    all_timestamps = sorted(set.union(*common_ts_sets))
    if filter_to_effective_start:
        timeline = sorted([t for t in common_intersection])
    else:
        timeline = all_timestamps

    bar_map: dict[datetime, dict[str, Bar]] = {}
    for sym in headline_symbols:
        for b in data[sym]:
            if b.timestamp not in bar_map:
                bar_map[b.timestamp] = {}
            bar_map[b.timestamp][sym] = b

    # 5. Core Initialization State Tracking
    core_initialized = False
    core_target_per_symbol = (initial_cash * core_allocation_pct) / len(headline_symbols)
    core_starting_val = 0.0
    core_actual_pct = 0.0
    core_residual_cash = initial_cash

    pending_orders: list[Order] = []
    trade_records: list[V2TradeRecord] = []
    equity_curve: list[float] = []
    timestamp_strings: list[str] = []

    tactical_entry_meta: dict[str, list[dict]] = {sym: [] for sym in headline_symbols}
    signals_generated_count = 0
    order_attempts_count = 0
    entry_fills_count = 0
    reload_fills_count = 0
    partial_exit_fills_count = 0
    full_exit_fills_count = 0
    margin_call_count = 0
    forced_liquidation_count = 0
    peak_margin_debt = 0.0

    last_ts: datetime | None = None
    latest_prices: dict[str, float] = {}

    for t in timeline:
        current_bars = bar_map.get(t, {})

        # Prices available at the open of bar t (for pending order valuation & execution)
        open_prices = {sym: b.open for sym, b in current_bars.items()}
        execution_valuation_prices = {**latest_prices, **open_prices}

        # Initialize persistent core at effective common start (Exogenous starting state)
        if not core_initialized and len(current_bars) == len(headline_symbols):
            core_starting_val = 0.0
            for sym in headline_symbols:
                b = current_bars[sym]
                shares = float(int(core_target_per_symbol / b.open))
                if shares > 0:
                    # Exogenous initial state: 0 commission, 0 slippage
                    portfolio.open_or_add_core(
                        symbol=sym,
                        quantity=shares,
                        price=b.open,
                        commission=0.0,
                        slippage=0.0,
                    )
                    core_starting_val += shares * b.open
            core_initialized = True
            core_actual_pct = (core_starting_val / initial_cash) * 100.0
            core_residual_cash = portfolio.cash

        # Process Pending Orders (No-Lookahead: Signal generated at t-1 filled at t open)
        unfilled_orders: list[Order] = []
        for order in pending_orders:
            bar = current_bars.get(order.symbol)
            if bar is None:
                unfilled_orders.append(order)
                continue

            fill = simulator.execute_order(order=order, bar=bar)
            if fill is not None:
                if fill.side == OrderSide.BUY:
                    # Tactical Add / Reload
                    cost = fill.quantity * fill.price
                    can_buy = True
                    if mode == "V2-B" and (portfolio.cash - cost - fill.commission) < 0:
                        can_buy = False
                    elif (
                        mode == "V2-C"
                        and portfolio.get_buying_power(execution_valuation_prices) < cost
                    ):
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
                                "entry_reference_price": fill.reference_price or fill.price,
                                "quantity": fill.quantity,
                                "orig_quantity": fill.quantity,
                                "commission": fill.commission,
                                "slippage": fill.slippage,
                            }
                        )
                        if "reload" in order.tag:
                            reload_fills_count += 1
                        else:
                            entry_fills_count += 1

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

                            # Unadjusted reference P&L
                            exit_ref = fill.reference_price or fill.price
                            entry_ref = first_entry["entry_reference_price"]
                            pre_pnl = match_qty * (exit_ref - entry_ref)

                            # Proportional slippage & commission
                            prop_entry = match_qty / first_entry["orig_quantity"]
                            prop_exit = match_qty / fill.quantity
                            entry_slip = first_entry["slippage"] * prop_entry
                            exit_slip = fill.slippage * prop_exit
                            trade_comm = (first_entry["commission"] * prop_entry) + (
                                fill.commission * prop_exit
                            )

                            pre_pnl_rounded = round(pre_pnl, 4)
                            entry_slip_rounded = round(entry_slip, 4)
                            exit_slip_rounded = round(exit_slip, 4)
                            trade_slip_rounded = round(entry_slip_rounded + exit_slip_rounded, 4)
                            trade_comm_rounded = round(trade_comm, 4)
                            trade_realized_pnl_rounded = round(
                                pre_pnl_rounded - trade_slip_rounded, 4
                            )

                            trade_records.append(
                                V2TradeRecord(
                                    trade_id=str(uuid.uuid4())[:8],
                                    symbol=fill.symbol,
                                    sleeve="TACTICAL",
                                    entry_time=first_entry["entry_time"],
                                    exit_time=fill.timestamp,
                                    entry_price=first_entry["entry_price"],
                                    exit_price=fill.price,
                                    entry_reference_price=entry_ref,
                                    exit_reference_price=exit_ref,
                                    quantity=match_qty,
                                    pre_slippage_pnl=pre_pnl_rounded,
                                    realized_pnl=trade_realized_pnl_rounded,
                                    commission=trade_comm_rounded,
                                    slippage=trade_slip_rounded,
                                    entry_slippage=entry_slip_rounded,
                                    exit_slippage=exit_slip_rounded,
                                    holding_time_minutes=hold_mins,
                                    exit_reason=order.tag,
                                )
                            )
                            if first_entry["quantity"] <= 1e-6:
                                tactical_entry_meta[fill.symbol].pop(0)

                        if "partial" in order.tag:
                            partial_exit_fills_count += 1
                        else:
                            full_exit_fills_count += 1

        pending_orders = unfilled_orders

        # Prices at close of bar t (for mark-to-market, financing, and signal generation)
        close_prices = {sym: b.close for sym, b in current_bars.items()}
        latest_prices.update(close_prices)

        # Accrue financing interest if cash is negative (mode V2-C)
        if last_ts is not None and mode == "V2-C":
            elapsed = (t - last_ts).total_seconds()
            if elapsed > 0:
                portfolio.accrue_financing(elapsed)

        # Margin maintenance & forced liquidation check at bar close (V2-C)
        if mode == "V2-C" and portfolio.is_margin_call(close_prices):
            margin_call_count += 1
            liq_orders = portfolio.generate_margin_liquidation_orders(close_prices, timestamp=t)
            # Liquidation orders execute at next bar open (no lookahead execution at close)
            pending_orders.extend(liq_orders)

        # Peak margin debt sampled after intra-bar transactions and financing
        debt = portfolio.margin_debt
        if debt > peak_margin_debt:
            peak_margin_debt = debt

        # Generate fresh signals for next bar if tactical sleeve enabled
        if mode in ("V2-B", "V2-C") and core_initialized:
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

                intent = signal_gen.process_bar(
                    bar=b,
                    df=df,
                    current_idx=idx,
                    current_tactical_shares=cur_tact_shares,
                )
                if intent is not None:
                    signals_generated_count += 1
                    if intent.action == "ENTER_LONG":
                        # Tactical size: ~10% of equity (exact Phase K frozen rule)
                        current_eq = max(10_000.0, portfolio.get_equity(latest_prices))
                        target_tact_dollars = current_eq * 0.10 * intent.strength
                        shares = float(int(target_tact_dollars / b.close))
                        if shares > 0:
                            order_attempts_count += 1
                            pending_orders.append(
                                Order(
                                    order_id=str(uuid.uuid4())[:8],
                                    symbol=sym,
                                    timestamp=t,
                                    side=OrderSide.BUY,
                                    order_type=OrderType.MARKET,
                                    quantity=shares,
                                    stop_loss_price=intent.stop_price,
                                    target_price=intent.target_price,
                                    tag=intent.reason,
                                )
                            )
                    elif intent.action == "EXIT_LONG" and cur_tact_shares > 0:
                        raw_exit = float(int(cur_tact_shares * intent.strength))
                        exit_shares = raw_exit or cur_tact_shares
                        order_attempts_count += 1
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

    open_tact_lots = sum(
        1 for lots in tactical_entry_meta.values() for lot in lots if lot["quantity"] > 1e-6
    )
    open_tact_shares = sum(
        sum(lot["quantity"] for lot in lots if lot["quantity"] > 1e-6)
        for lots in tactical_entry_meta.values()
    )

    # Closed tactical totals
    closed_ref_pnl = round(sum(tr.pre_slippage_pnl for tr in trade_records), 4)
    closed_entry_slip = round(sum(tr.entry_slippage for tr in trade_records), 4)
    closed_exit_slip = round(sum(tr.exit_slippage for tr in trade_records), 4)
    closed_slip = round(sum(tr.slippage for tr in trade_records), 4)
    closed_comm = round(sum(tr.commission for tr in trade_records), 4)
    closed_net_realized = round(closed_ref_pnl - closed_slip - closed_comm, 4)

    # Open tactical totals
    open_ref_mtm = 0.0
    open_entry_slip = 0.0
    open_entry_comm = 0.0
    for sym, lots in tactical_entry_meta.items():
        market_p = latest_prices.get(sym, 0.0)
        for lot in lots:
            rem_qty = lot["quantity"]
            if rem_qty <= 1e-6:
                continue
            prop_open = rem_qty / lot["orig_quantity"] if lot["orig_quantity"] > 0 else 1.0
            lot_entry_slip = lot["slippage"] * prop_open
            lot_entry_comm = lot["commission"] * prop_open
            ref_p = lot["entry_reference_price"]
            open_ref_mtm += rem_qty * (market_p - ref_p)
            open_entry_slip += lot_entry_slip
            open_entry_comm += lot_entry_comm

    open_ref_mtm = round(open_ref_mtm, 4)
    open_entry_slip = round(open_entry_slip, 4)
    open_entry_comm = round(open_entry_comm, 4)
    open_net_terminal = round(open_ref_mtm - open_entry_slip - open_entry_comm, 4)

    # Total tactical economic contribution
    tact_total_contrib = round(
        closed_net_realized + open_net_terminal - portfolio.financing_interest_paid, 4
    )

    core_net_contribution = round(recon["core_realized_pnl"] + recon["core_unrealized_pnl"], 4)
    total_calculated_pnl = round(core_net_contribution + tact_total_contrib, 4)
    accounting_pnl = round(ending_equity - initial_cash + portfolio.total_withdrawals, 4)
    discrepancy = abs(accounting_pnl - total_calculated_pnl)

    margin_exercised = peak_margin_debt > 0 or portfolio.financing_interest_paid > 0

    return V2BacktestResult(
        mode=mode,
        initial_cash=initial_cash,
        final_equity=ending_equity,
        total_net_pnl=net_pnl,
        total_return_pct=ret_pct,
        max_drawdown_pct=max_dd_pct,
        effective_start_timestamp=effective_start_timestamp.isoformat(),
        evaluation_end_timestamp=evaluation_end_timestamp.isoformat(),
        core_starting_value=core_starting,
        core_ending_value=core_ending,
        core_actual_pct=core_actual_pct,
        core_residual_cash=core_residual_cash,
        core_realized_pnl=recon["core_realized_pnl"],
        core_unrealized_pnl=recon["core_unrealized_pnl"],
        tactical_trade_count=len(trade_records),
        closed_reference_pnl=closed_ref_pnl,
        closed_entry_slippage=closed_entry_slip,
        closed_exit_slippage=closed_exit_slip,
        closed_slippage=closed_slip,
        closed_commissions=closed_comm,
        closed_net_realized_pnl=closed_net_realized,
        open_reference_mtm=open_ref_mtm,
        open_entry_slippage=open_entry_slip,
        open_entry_commissions=open_entry_comm,
        open_net_terminal_contribution=open_net_terminal,
        total_tactical_economic_contribution=tact_total_contrib,
        tactical_total_economic_contribution=tact_total_contrib,
        tactical_closed_realized_pnl=closed_net_realized,
        tactical_terminal_unrealized_pnl=open_net_terminal,
        tactical_realized_pnl=closed_net_realized,
        tactical_unrealized_pnl=open_net_terminal,
        tactical_win_rate_pct=win_rate,
        tactical_median_holding_minutes=median_hold,
        signals_generated_count=signals_generated_count,
        order_attempts_count=order_attempts_count,
        entry_fills_count=entry_fills_count,
        reload_fills_count=reload_fills_count,
        partial_exit_fills_count=partial_exit_fills_count,
        full_exit_fills_count=full_exit_fills_count,
        completed_round_trips_count=len(trade_records),
        open_tactical_lots_count=open_tact_lots,
        open_tactical_shares_count=open_tact_shares,
        peak_margin_debt=peak_margin_debt,
        total_margin_interest=portfolio.financing_interest_paid,
        margin_call_count=margin_call_count,
        forced_liquidation_count=forced_liquidation_count,
        margin_exercised=margin_exercised,
        tactical_adds_count=entry_fills_count,
        tactical_reloads_count=reload_fills_count,
        tactical_partial_exits_count=partial_exit_fills_count,
        tactical_full_exits_count=full_exit_fills_count,
        pre_slippage_pnl=closed_ref_pnl,
        total_commission_paid=portfolio.commissions_paid,
        total_slippage_paid=portfolio.slippage_paid,
        accounting_tolerance=ACCOUNTING_TOLERANCE,
        reconciliation_discrepancy=discrepancy,
        reconciles_cleanly=is_within_accounting_tolerance(discrepancy),
        timestamps=timestamp_strings,
        equity_curve=equity_curve,
        trades=trade_records,
    )
