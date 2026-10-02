import uuid
import numpy as np
from pydantic import BaseModel
from tactical_engine.backtest.engine import BacktestResult
from tactical_engine.backtest.state import PortfolioTracker, TradeRecord
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType
from tactical_engine.execution.simulator import ExecutionSimulator
from tactical_engine.portfolio.sizing import calculate_position_size
from tactical_engine.signals.exits import check_exit_condition


class BootstrapDistribution(BaseModel):
    num_simulations: int
    mean_returns: list[float]
    ci_lower: float
    ci_upper: float
    median: float


def bootstrap_trade_returns(
    trades: list[TradeRecord],
    num_simulations: int = 1000,
    confidence_level: float = 0.95,
    seed: int = 42,
) -> BootstrapDistribution:
    if not trades:
        return BootstrapDistribution(
            num_simulations=num_simulations,
            mean_returns=[0.0] * num_simulations,
            ci_lower=0.0,
            ci_upper=0.0,
            median=0.0,
        )

    pnls = np.array([t.net_pnl for t in trades])
    rng = np.random.default_rng(seed)
    n = len(pnls)

    bootstrap_means = []
    for _ in range(num_simulations):
        sample = rng.choice(pnls, size=n, replace=True)
        bootstrap_means.append(float(np.mean(sample)))

    sorted_means = np.sort(bootstrap_means)
    alpha = 1.0 - confidence_level
    lower_idx = int(num_simulations * (alpha / 2.0))
    upper_idx = int(num_simulations * (1.0 - alpha / 2.0))

    return BootstrapDistribution(
        num_simulations=num_simulations,
        mean_returns=[round(m, 2) for m in bootstrap_means],
        ci_lower=round(float(sorted_means[lower_idx]), 2),
        ci_upper=round(float(sorted_means[min(upper_idx, num_simulations - 1)]), 2),
        median=round(float(np.median(sorted_means)), 2),
    )


def run_random_entry_control(
    data: dict[str, list[Bar]],
    config: EngineConfig,
    target_trades: int = 5,
    seed: int = 42,
) -> BacktestResult:
    # Baseline null hypothesis control: enters at randomly selected timestamps
    rng = np.random.default_rng(seed)
    all_timestamps = sorted(
        list(set(b.timestamp for bars in data.values() for b in bars))
    )
    if len(all_timestamps) < 10:
        return BacktestResult(
            initial_cash=config.portfolio.initial_cash,
            final_equity=config.portfolio.initial_cash,
            total_trades=0,
            trades=[],
            equity_curve=[],
            timestamps=[],
        )

    # Randomly select candidate entry indices (spaced apart)
    possible_indices = list(range(10, len(all_timestamps) - 10))
    chosen_indices = set(rng.choice(possible_indices, size=min(target_trades, len(possible_indices)), replace=False))

    tracker = PortfolioTracker(initial_cash=config.portfolio.initial_cash)
    simulator = ExecutionSimulator(cost_config=config.costs)
    pending_orders: list[Order] = []
    equity_curve: list[float] = []
    time_index: list[str] = []

    symbols = list(data.keys())

    for idx, ts in enumerate(all_timestamps):
        current_prices = {}
        bars_at_ts = {}

        for sym, bars in data.items():
            for b in bars:
                if b.timestamp == ts:
                    current_prices[sym] = b.close
                    bars_at_ts[sym] = b
                    break

        account_state = tracker.get_account_state(ts, current_prices)
        equity_curve.append(account_state.equity)
        time_index.append(ts.isoformat())

        # Execute pending orders
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

        # Check exits
        for sym, pos in list(tracker.positions.items()):
            bar = bars_at_ts.get(sym)
            if not bar:
                continue
            entry_time = tracker.entry_times.get(sym, ts)
            should_exit, reason = check_exit_condition(
                entry_price=pos.avg_price,
                entry_time=entry_time,
                current_bar=bar,
                atr=1.5,
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

        # Random entry if index selected
        if idx in chosen_indices and not tracker.positions:
            chosen_sym = str(rng.choice(symbols))
            bar = bars_at_ts.get(chosen_sym)
            if bar:
                qty = calculate_position_size(
                    symbol=chosen_sym,
                    price=bar.close,
                    stop_price=None,
                    account_state=account_state,
                    config=config.portfolio,
                )
                if qty > 0:
                    pending_orders.append(
                        Order(
                            order_id=str(uuid.uuid4())[:8],
                            symbol=chosen_sym,
                            timestamp=ts,
                            side=OrderSide.BUY,
                            order_type=OrderType.MARKET,
                            quantity=qty,
                            tag="random_entry_control",
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
