import uuid

from pydantic import BaseModel

from tactical_engine.backtest.state import PortfolioTracker, TradeRecord
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType
from tactical_engine.execution.simulator import ExecutionSimulator
from tactical_engine.options.assignment import evaluate_expiration_assignment
from tactical_engine.options.chain_provider import OptionChainProvider
from tactical_engine.options.contracts import CoveredCallRecord, OptionContractType, OptionPosition
from tactical_engine.options.covered_calls import select_covered_call_contract
from tactical_engine.portfolio.margin import (
    calculate_maintenance_requirement,
    generate_forced_liquidation_orders,
    is_margin_call,
)
from tactical_engine.portfolio.sizing import calculate_position_size
from tactical_engine.signals.exits import check_exit_condition
from tactical_engine.signals.features import compute_bar_features
from tactical_engine.signals.pullback import generate_pullback_signals


class BacktestResult(BaseModel):
    initial_cash: float
    final_equity: float
    total_trades: int
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


def run_backtest(
    data: dict[str, list[Bar]],
    config: EngineConfig,
    option_chain_provider: OptionChainProvider | None = None,
) -> BacktestResult:
    # 1. Validation status per AGENTS.md rule 5
    if not config.options.enabled:
        validation_status = "NONE"
    elif option_chain_provider is None:
        validation_status = "UNVALIDATED"
    else:
        validation_status = "VALIDATED"

    # 2. Feature & Signal generation per symbol
    features_by_sym = {}
    signals_by_sym = {}
    for sym, bars in data.items():
        df_feat = compute_bar_features(bars, trend_window=config.signals.trend_window)
        features_by_sym[sym] = df_feat
        signals_by_sym[sym] = generate_pullback_signals(df_feat, config.signals)

    all_timestamps = sorted(list(set(b.timestamp for bars in data.values() for b in bars)))

    tracker = PortfolioTracker(initial_cash=config.portfolio.initial_cash)
    simulator = ExecutionSimulator(cost_config=config.costs)
    pending_orders: list[Order] = []
    equity_curve: list[float] = []
    time_index: list[str] = []

    last_ts = None
    for ts in all_timestamps:
        current_prices = {}
        bars_at_ts = {}

        for sym, bars in data.items():
            for b in bars:
                if b.timestamp == ts:
                    current_prices[sym] = b.close
                    bars_at_ts[sym] = b
                    break

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
                    tracker.apply_fill(fill, exit_reason=ord.tag)
                else:
                    unfilled_orders.append(ord)
        pending_orders = unfilled_orders

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

        # C. Covered Call Expiration & Assignment check
        if config.options.enabled and validation_status == "VALIDATED":
            for sym in list(tracker.covered_calls.keys()):
                call_pos = tracker.covered_calls[sym]
                bar = bars_at_ts.get(sym)
                if bar and (ts >= call_pos.expiration or sym not in tracker.positions):
                    is_assigned, cash_proceeds, shares_deliv = evaluate_expiration_assignment(
                        call_pos, bar.close
                    )
                    contracts = abs(call_pos.quantity)
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

        # D. Check exits on active positions
        for sym, pos in list(tracker.positions.items()):
            bar = bars_at_ts.get(sym)
            if not bar:
                continue
            entry_time = tracker.entry_times.get(sym, ts)
            df_sym = features_by_sym[sym]
            atr = float(df_sym.loc[ts, "atr"]) if ts in df_sym.index else 1.0
            should_exit, reason = check_exit_condition(
                entry_price=pos.avg_price,
                entry_time=entry_time,
                current_bar=bar,
                atr=atr,
                config=config.exits,
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
        for sym, sigs in signals_by_sym.items():
            existing_pos = tracker.positions.get(sym, None)
            existing_layers = len(tracker.layers_by_symbol.get(sym, []))
            if existing_pos and existing_layers >= config.portfolio.max_layers:
                continue

            bar = bars_at_ts.get(sym)
            if not bar:
                continue

            matching_sigs = [s for s in sigs if s.timestamp == ts and s.action == "ENTER_LONG"]
            if matching_sigs:
                sig = matching_sigs[0]
                # If layering into existing position, only enter if price
                # pulled back below avg_price
                if existing_pos and bar.close > existing_pos.avg_price:
                    continue

                df_sym = features_by_sym[sym]
                atr = float(df_sym.loc[ts, "atr"]) if ts in df_sym.index else 1.0
                stop_p = bar.close - (config.exits.stop_atr * atr)
                qty = calculate_position_size(
                    symbol=sym,
                    price=bar.close,
                    stop_price=stop_p,
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
                            order_type=OrderType.MARKET,
                            quantity=qty,
                            tag=f"layer_{layer_num}:{sig.reason}",
                        )
                    )

    final_prices = {sym: bars[-1].close for sym, bars in data.items() if bars}
    final_state = tracker.get_account_state(all_timestamps[-1], final_prices)

    return BacktestResult(
        initial_cash=config.portfolio.initial_cash,
        final_equity=final_state.equity,
        total_trades=len(tracker.closed_trades),
        trades=tracker.closed_trades,
        equity_curve=equity_curve,
        timestamps=time_index,
        margin_interest_paid=round(tracker.margin_interest_paid, 2),
        peak_margin_debt=round(tracker.peak_margin_debt, 2),
        margin_call_count=tracker.margin_call_count,
        forced_liquidation_count=tracker.forced_liquidation_count,
        options_premium_collected=round(tracker.options_premium_collected, 2),
        options_realized_pnl=round(tracker.options_realized_pnl, 2),
        options_validation_status=validation_status,
    )
