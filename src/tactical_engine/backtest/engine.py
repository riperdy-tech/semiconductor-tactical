import uuid
from collections import defaultdict
from datetime import date

import numpy as np
from pydantic import BaseModel

from tactical_engine.backtest.state import PortfolioTracker, TradeRecord
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType
from tactical_engine.execution.simulator import ExecutionSimulator
from tactical_engine.options.assignment import evaluate_expiration_assignment
from tactical_engine.options.chain_provider import OptionChainProvider
from tactical_engine.options.contracts import CoveredCallRecord, OptionContractType, OptionPosition
from tactical_engine.options.covered_calls import select_covered_call_contract
from tactical_engine.options.repurchase import should_repurchase_covered_call
from tactical_engine.portfolio.margin import (
    calculate_maintenance_requirement,
    generate_forced_liquidation_orders,
    is_margin_call,
)
from tactical_engine.portfolio.sizing import calculate_position_size
from tactical_engine.signals.directional_fidelity import (
    check_strength_predicate,
    generate_directional_fidelity_signals,
)
from tactical_engine.signals.exits import check_exit_condition
from tactical_engine.signals.features import compute_bar_features
from tactical_engine.signals.pullback import generate_pullback_signals
from tactical_engine.signals.regime import BenchmarkRegimeProvider, RegimeProvider


class BacktestResult(BaseModel):
    initial_cash: float
    final_equity: float
    total_trades: int
    implementation_label: str = "CURRENT_MECHANICAL_PULLBACK_BASELINE"
    trades: list[TradeRecord]
    equity_curve: list[float]
    timestamps: list[str]
    margin_interest_paid: float = 0.0
    peak_margin_debt: float = 0.0
    margin_call_count: int = 0
    forced_liquidation_count: int = 0
    options_premium_collected: float = 0.0
    options_realized_pnl: float = 0.0
    options_validation_status: str = "NONE"
    # Trade-frequency diagnostics
    total_signals_generated: int = 0
    filled_entries_count: int = 0
    max_simultaneous_positions: int = 0
    reentry_count: int = 0
    time_in_market_pct: float = 0.0
    trades_per_day: float = 0.0
    trades_per_symbol_per_day: float = 0.0
    median_holding_time_minutes: float = 0.0
    # Cost decomposition
    commission_paid: float = 0.0
    slippage_paid: float = 0.0
    total_cost_paid: float = 0.0
    costs_as_pct_of_gross_pnl: float = 0.0


def run_backtest(
    data: dict[str, list[Bar]],
    config: EngineConfig,
    option_chain_provider: OptionChainProvider | None = None,
    regime_provider: RegimeProvider | None = None,
) -> BacktestResult:
    # 1. Validation status per AGENTS.md rule 5
    if not config.options.enabled:
        validation_status = "NONE"
    elif option_chain_provider is None:
        validation_status = "UNVALIDATED"
    else:
        validation_status = "VALIDATED"

    # 2. Setup regime provider if benchmarks are present in data
    if regime_provider is None:
        sec_bars = data.get("SMH", [])
        brd_bars = data.get("SPY", [])
        if sec_bars or brd_bars:
            regime_provider = BenchmarkRegimeProvider(
                sector_bars=sec_bars,
                broad_bars=brd_bars,
                trend_window=config.signals.trend_window,
                filter_mode=config.signals.regime_filter_mode,
            )

    # 3. Feature & Signal generation for TRADABLE symbols only
    configured_universe = set(
        s.upper() for s in config.strategy.universe + (config.strategy.two_x_etfs or [])
    )
    if configured_universe:
        tradable_symbols = configured_universe
    else:
        tradable_symbols = set(k.upper() for k in data.keys() if k.upper() not in ("SMH", "SPY"))

    features_by_sym = {}
    signals_by_sym = {}
    is_fidelity = (
        config.signals.signal_family == "directional_fidelity"
        or config.strategy.variant == "directional_fidelity_reconstruction"
    )
    variant_str = config.strategy.variant.lower()
    if is_fidelity:
        implementation_label = "DIRECTIONAL_FIDELITY_RECONSTRUCTION"
    elif variant_str in (
        "mechanical_pullback_sector_filtered_diagnostic",
        "regime_adapted",
    ) or (not is_fidelity and config.signals.sector_filter):
        implementation_label = "MECHANICAL_PULLBACK_SECTOR_FILTERED_DIAGNOSTIC"
    elif variant_str in ("current_mechanical_pullback_baseline", "risk_controlled"):
        implementation_label = "CURRENT_MECHANICAL_PULLBACK_BASELINE"
    elif variant_str == "literal_clone":
        implementation_label = "LITERAL_CLONE_MECHANICAL_PULLBACK"
    else:
        implementation_label = variant_str.upper()

    for sym, bars in data.items():
        if sym.upper() in tradable_symbols:
            df_feat = compute_bar_features(bars, trend_window=config.signals.trend_window)
            features_by_sym[sym] = df_feat
            if is_fidelity:
                signals_by_sym[sym] = generate_directional_fidelity_signals(
                    df_feat, config.signals, regime_provider=regime_provider
                )
            else:
                signals_by_sym[sym] = generate_pullback_signals(
                    df_feat, config.signals, regime_provider=regime_provider
                )

    all_timestamps = sorted(list(set(b.timestamp for bars in data.values() for b in bars)))
    bars_by_sym_ts = {sym: {b.timestamp: b for b in bars} for sym, bars in data.items()}
    atr_by_sym = {
        sym: df["atr"].to_dict() if "atr" in df.columns else {}
        for sym, df in features_by_sym.items()
    }
    entry_signals_by_sym_ts = {
        sym: {s.timestamp: s for s in sigs if s.action == "ENTER_LONG"}
        for sym, sigs in signals_by_sym.items()
    }

    tracker = PortfolioTracker(initial_cash=config.portfolio.initial_cash)
    simulator = ExecutionSimulator(cost_config=config.costs)
    pending_orders: list[Order] = []
    equity_curve: list[float] = []
    time_index: list[str] = []

    filled_entries_count = 0
    max_simultaneous_positions = 0
    time_in_market_bars = 0
    reentry_count = 0
    entries_by_sym_date: dict[tuple[str, date], int] = defaultdict(int)

    last_ts = None
    for ts in all_timestamps:
        current_prices = {}
        bars_at_ts = {}

        for sym, b_map in bars_by_sym_ts.items():
            b = b_map.get(ts)
            if b is not None:
                current_prices[sym] = b.close
                bars_at_ts[sym] = b

        # Margin interest accrual
        if last_ts is not None and config.costs.margin_rate_annual > 0:
            elapsed = (ts - last_ts).total_seconds()
            tracker.accrue_margin_interest(
                rate_annual=config.costs.margin_rate_annual,
                elapsed_seconds=elapsed,
            )
        last_ts = ts

        account_state = tracker.get_account_state(ts, current_prices)
        equity_curve.append(account_state.equity)
        time_index.append(ts.isoformat())

        # A. Execute pending equity orders
        unfilled_orders = []
        for ord in pending_orders:
            bar = bars_at_ts.get(ord.symbol)
            if bar:
                fill = simulator.execute_order(ord, bar)
                if fill:
                    tracker.apply_fill(
                        fill,
                        exit_reason=ord.tag,
                        stop_price=(
                            ord.stop_loss_price
                            if ord.stop_loss_price is not None
                            else ord.stop_price
                        ),
                        target_price=ord.target_price,
                        entry_atr=ord.entry_atr,
                    )
                    if fill.side == OrderSide.BUY:
                        filled_entries_count += 1
                        d = fill.timestamp.date()
                        if entries_by_sym_date[(fill.symbol, d)] > 0:
                            reentry_count += 1
                        entries_by_sym_date[(fill.symbol, d)] += 1
                else:
                    unfilled_orders.append(ord)
        pending_orders = unfilled_orders

        # Track simultaneous positions & time in market
        curr_num_pos = len(tracker.positions)
        if curr_num_pos > max_simultaneous_positions:
            max_simultaneous_positions = curr_num_pos
        if curr_num_pos > 0:
            time_in_market_bars += 1

        # B. Check margin call & forced liquidations
        maint_req = calculate_maintenance_requirement(tracker.positions, current_prices)
        current_account_state = tracker.get_account_state(ts, current_prices)
        if is_margin_call(current_account_state.equity, maint_req):
            tracker.margin_call_count += 1
            liquidation_orders = generate_forced_liquidation_orders(
                current_account_state, current_prices
            )
            for liq_ord in liquidation_orders:
                pending_orders.append(liq_ord)

        # C. Covered Call Repurchase & Expiration/Assignment check
        if config.options.enabled and validation_status == "VALIDATED":
            for sym in list(tracker.covered_calls.keys()):
                call_pos = tracker.covered_calls[sym]
                bar = bars_at_ts.get(sym)
                if not bar:
                    continue

                contracts = abs(call_pos.quantity)
                underlying_entry_p = (
                    tracker.positions[sym].avg_price if sym in tracker.positions else bar.close
                )

                # Look for current quote of this contract in chain
                current_quote = None
                if option_chain_provider:
                    chain = option_chain_provider.get_chain(sym, ts)
                    for q in chain:
                        if q.symbol == call_pos.symbol:
                            current_quote = q
                            break

                # 1. Repurchase check (pullback or profit target)
                should_repurch, repurch_reason, repurch_p = should_repurchase_covered_call(
                    call_position=call_pos,
                    current_call_quote=current_quote,
                    current_underlying_price=bar.close,
                    underlying_price_at_entry=underlying_entry_p,
                    config=config.options,
                )
                if should_repurch:
                    repurch_cost = repurch_p * 100.0 * contracts
                    tracker.cash -= repurch_cost
                    opt_realized = (call_pos.avg_price - repurch_p) * 100.0 * contracts
                    tracker.options_realized_pnl += opt_realized
                    tracker.covered_call_records.append(
                        CoveredCallRecord(
                            contract_symbol=call_pos.symbol,
                            underlying=sym,
                            strike=call_pos.strike,
                            expiration=call_pos.expiration,
                            entry_time=call_pos.expiration,
                            exit_time=ts,
                            entry_premium=call_pos.avg_price,
                            exit_premium=repurch_p,
                            contracts=contracts,
                            realized_pnl=round(opt_realized, 2),
                            was_assigned=False,
                            underlying_shares_delivered=0.0,
                        )
                    )
                    tracker.covered_calls.pop(sym, None)
                    continue

                # 2. Expiration and assignment check
                if ts >= call_pos.expiration or sym not in tracker.positions:
                    is_assigned, cash_proceeds, shares_deliv = evaluate_expiration_assignment(
                        call_pos, bar.close
                    )
                    if is_assigned:
                        tracker.cash += cash_proceeds
                        # Deliver shares from underlying position
                        curr_stock = tracker.positions.get(sym)
                        if curr_stock:
                            new_shares = max(0.0, curr_stock.quantity - shares_deliv)
                            if new_shares == 0:
                                tracker.positions.pop(sym, None)
                                tracker.entry_times.pop(sym, None)
                            else:
                                tracker.positions[sym] = curr_stock.model_copy(
                                    update={"quantity": new_shares}
                                )
                    # Realized P&L on the short option contract: premium received at entry
                    opt_realized = call_pos.avg_price * 100.0 * contracts
                    tracker.options_realized_pnl += opt_realized
                    tracker.covered_call_records.append(
                        CoveredCallRecord(
                            contract_symbol=call_pos.symbol,
                            underlying=sym,
                            strike=call_pos.strike,
                            expiration=call_pos.expiration,
                            entry_time=call_pos.expiration,  # proxy
                            exit_time=ts,
                            entry_premium=call_pos.avg_price,
                            exit_premium=0.0,
                            contracts=contracts,
                            realized_pnl=round(opt_realized, 2),
                            was_assigned=is_assigned,
                            underlying_shares_delivered=shares_deliv,
                        )
                    )
                    tracker.covered_calls.pop(sym, None)

        # D. Check exits on active positions using stored exit geometry
        for sym, pos in list(tracker.positions.items()):
            bar = bars_at_ts.get(sym)
            if not bar:
                continue
            entry_time = tracker.entry_times.get(sym, ts)
            stored_stop = tracker.stop_prices.get(sym)
            stored_target = tracker.target_prices.get(sym)
            stored_atr = tracker.entry_atrs.get(sym, 1.0)
            should_exit, reason = check_exit_condition(
                entry_price=pos.avg_price,
                entry_time=entry_time,
                current_bar=bar,
                atr=stored_atr,
                config=config.exits,
                stop_price=stored_stop,
                target_price=stored_target,
            )
            if should_exit:
                pending_orders.append(
                    Order(
                        order_id=str(uuid.uuid4())[:8],
                        symbol=sym,
                        timestamp=ts,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=pos.quantity,
                        tag=reason,
                    )
                )

        # E. Sell Covered Calls on active underlying shares (1 contract per 100 shares)
        if config.options.enabled and validation_status == "VALIDATED" and option_chain_provider:
            for sym, pos in tracker.positions.items():
                if sym not in tracker.covered_calls and pos.quantity >= 100.0:
                    bar = bars_at_ts.get(sym)
                    if not bar:
                        continue
                    # Check underlying strength predicate [Label: OBSERVED / HYPOTHESIS]
                    feat_df = features_by_sym.get(sym)
                    if feat_df is not None and ts in feat_df.index:
                        if not check_strength_predicate(feat_df.loc[ts]):
                            continue
                    chain = option_chain_provider.get_chain(sym, ts)
                    selected_call = select_covered_call_contract(
                        chain=chain,
                        underlying_price=bar.close,
                        min_dte=config.options.min_dte,
                        max_dte=config.options.max_dte,
                        moneyness=config.options.moneyness,
                    )
                    if selected_call and selected_call.bid > 0:
                        contracts = int(pos.quantity // 100)
                        # Option fill price after slippage
                        slip = (config.costs.option_slippage_bps / 10000.0) * selected_call.bid
                        fill_prem = max(0.01, selected_call.bid - slip)
                        prem_total = fill_prem * 100.0 * contracts

                        tracker.cash += prem_total
                        tracker.options_premium_collected += prem_total
                        tracker.covered_calls[sym] = OptionPosition(
                            symbol=selected_call.symbol,
                            underlying=sym,
                            contract_type=OptionContractType.CALL,
                            strike=selected_call.strike,
                            expiration=selected_call.expiration,
                            quantity=-float(contracts),
                            avg_price=round(fill_prem, 4),
                            associated_underlying_shares=float(contracts * 100),
                        )

        # F. Generate equity entry orders for next bar
        for sym, sig_map in entry_signals_by_sym_ts.items():
            existing_pos = tracker.positions.get(sym, None)
            existing_layers = len(tracker.layers_by_symbol.get(sym, []))
            if existing_pos and existing_layers >= config.portfolio.max_layers:
                continue

            bar = bars_at_ts.get(sym)
            if not bar:
                continue

            sig = sig_map.get(ts)
            if sig:
                # If layering into existing position, only enter if price
                # pulled back below avg_price
                if existing_pos and bar.close > existing_pos.avg_price:
                    continue

                entry_atr = atr_by_sym.get(sym, {}).get(ts, 1.0)
                if is_fidelity:
                    stop_loss_p = (
                        bar.close - (config.signals.swing_stop_atr * entry_atr)
                        if config.exits.family == "atr"
                        else (bar.close * 0.98)
                    )
                    target_p = (
                        bar.close + (config.signals.swing_target_atr * entry_atr)
                        if config.exits.family == "atr"
                        else (bar.close * 1.03)
                    )
                    if config.signals.order_execution_style == "stop_limit":
                        order_type = OrderType.STOP_LIMIT
                        stop_trigger_p = bar.close
                        limit_p = round(bar.close + 0.20 * entry_atr, 4)
                    else:
                        order_type = OrderType.MARKET
                        stop_trigger_p = None
                        limit_p = None
                else:
                    if config.exits.family == "atr":
                        stop_loss_p = bar.close - (config.exits.stop_atr * entry_atr)
                        target_p = bar.close + (config.exits.target_atr * entry_atr)
                    elif config.exits.family == "fixed_pct":
                        stop_loss_p = bar.close * (1.0 - config.exits.stop_pct)
                        target_p = bar.close * (1.0 + config.exits.target_pct)
                    else:
                        stop_loss_p = bar.close - (1.0 * entry_atr)
                        target_p = bar.close + (1.5 * entry_atr)
                    order_type = OrderType.MARKET
                    stop_trigger_p = stop_loss_p
                    limit_p = None

                qty = calculate_position_size(
                    symbol=sym,
                    price=bar.close,
                    stop_price=stop_loss_p,
                    account_state=current_account_state,
                    config=config.portfolio,
                    current_prices=current_prices,
                )
                if qty > 0:
                    layer_num = existing_layers + 1
                    pending_orders.append(
                        Order(
                            order_id=str(uuid.uuid4())[:8],
                            symbol=sym,
                            timestamp=ts,
                            side=OrderSide.BUY,
                            order_type=order_type,
                            quantity=qty,
                            stop_price=(
                                round(stop_trigger_p, 4)
                                if stop_trigger_p is not None
                                else None
                            ),
                            limit_price=limit_p,
                            stop_loss_price=round(stop_loss_p, 4),
                            target_price=round(target_p, 4),
                            entry_atr=entry_atr,
                            tag=f"layer_{layer_num}:{sig.reason}",
                        )
                    )

    final_prices = {sym: bars[-1].close for sym, bars in data.items() if bars}
    final_state = tracker.get_account_state(all_timestamps[-1], final_prices)

    unique_dates = {ts.date() for ts in all_timestamps}
    n_days = max(1, len(unique_dates))
    n_symbols = max(1, len(tradable_symbols))
    trades_per_day = round(len(tracker.closed_trades) / n_days, 2)
    trades_per_symbol_per_day = round(trades_per_day / n_symbols, 2)

    durations = [
        (t.exit_time - t.entry_time).total_seconds() / 60.0 for t in tracker.closed_trades
    ]
    median_holding = round(float(np.median(durations)), 1) if durations else 0.0

    time_in_market_pct = (
        round((time_in_market_bars / len(all_timestamps)) * 100.0, 2) if all_timestamps else 0.0
    )

    commission_paid = round(sum(t.commission_paid for t in tracker.closed_trades), 2)
    slippage_paid = round(sum(t.slippage_paid for t in tracker.closed_trades), 2)
    margin_interest = round(tracker.margin_interest_paid, 2)
    total_cost_paid = round(commission_paid + slippage_paid + margin_interest, 2)

    gross_pnl_total = sum(t.gross_pnl for t in tracker.closed_trades)
    costs_pct_gross = (
        round((total_cost_paid / abs(gross_pnl_total)) * 100.0, 2)
        if gross_pnl_total != 0
        else 0.0
    )

    total_signals = sum(len(sigs) for sigs in signals_by_sym.values())

    return BacktestResult(
        initial_cash=config.portfolio.initial_cash,
        final_equity=final_state.equity,
        total_trades=len(tracker.closed_trades),
        implementation_label=implementation_label,
        trades=tracker.closed_trades,
        equity_curve=equity_curve,
        timestamps=time_index,
        margin_interest_paid=margin_interest,
        peak_margin_debt=round(tracker.peak_margin_debt, 2),
        margin_call_count=tracker.margin_call_count,
        forced_liquidation_count=tracker.forced_liquidation_count,
        options_premium_collected=round(tracker.options_premium_collected, 2),
        options_realized_pnl=round(tracker.options_realized_pnl, 2),
        options_validation_status=validation_status,
        total_signals_generated=total_signals,
        filled_entries_count=filled_entries_count,
        max_simultaneous_positions=max_simultaneous_positions,
        reentry_count=reentry_count,
        time_in_market_pct=time_in_market_pct,
        trades_per_day=trades_per_day,
        trades_per_symbol_per_day=trades_per_symbol_per_day,
        median_holding_time_minutes=median_holding,
        commission_paid=commission_paid,
        slippage_paid=slippage_paid,
        total_cost_paid=total_cost_paid,
        costs_as_pct_of_gross_pnl=costs_pct_gross,
    )
