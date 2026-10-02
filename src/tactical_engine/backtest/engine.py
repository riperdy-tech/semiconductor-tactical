import uuid

from pydantic import BaseModel

from tactical_engine.backtest.state import PortfolioTracker, TradeRecord
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType
from tactical_engine.execution.simulator import ExecutionSimulator
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


def run_backtest(data: dict[str, list[Bar]], config: EngineConfig) -> BacktestResult:
    # 1. Feature & Signal generation per symbol
    features_by_sym = {}
    signals_by_sym = {}
    for sym, bars in data.items():
        df_feat = compute_bar_features(bars, trend_window=config.signals.trend_window)
        features_by_sym[sym] = df_feat
        signals_by_sym[sym] = generate_pullback_signals(df_feat, config.signals)

    # 2. Synchronized bar simulation loop
    all_timestamps = sorted(list(set(b.timestamp for bars in data.values() for b in bars)))

    tracker = PortfolioTracker(initial_cash=config.portfolio.initial_cash)
    simulator = ExecutionSimulator(cost_config=config.costs)
    pending_orders: list[Order] = []
    equity_curve: list[float] = []
    time_index: list[str] = []

    for ts in all_timestamps:
        current_prices = {}
        bars_at_ts = {}

        # Collect current bars
        for sym, bars in data.items():
            for b in bars:
                if b.timestamp == ts:
                    current_prices[sym] = b.close
                    bars_at_ts[sym] = b
                    break

        account_state = tracker.get_account_state(ts, current_prices)
        equity_curve.append(account_state.equity)
        time_index.append(ts.isoformat())

        # A. Execute pending orders generated at previous bar close
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

        # B. Check exits on active positions
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

        # C. Generate entry orders for next bar
        for sym, sigs in signals_by_sym.items():
            if sym in tracker.positions:
                continue  # Single layer for base test
            bar = bars_at_ts.get(sym)
            if not bar:
                continue
            # Look for signal confirmed at ts
            matching_sigs = [s for s in sigs if s.timestamp == ts and s.action == "ENTER_LONG"]
            if matching_sigs:
                sig = matching_sigs[0]
                df_sym = features_by_sym[sym]
                atr = float(df_sym.loc[ts, "atr"]) if ts in df_sym.index else 1.0
                stop_p = bar.close - (config.exits.stop_atr * atr)
                qty = calculate_position_size(
                    symbol=sym,
                    price=bar.close,
                    stop_price=stop_p,
                    account_state=account_state,
                    config=config.portfolio,
                )
                if qty > 0:
                    pending_orders.append(
                        Order(
                            order_id=str(uuid.uuid4())[:8],
                            symbol=sym,
                            timestamp=ts,
                            side=OrderSide.BUY,
                            order_type=OrderType.MARKET,
                            quantity=qty,
                            tag=sig.reason,
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
    )
