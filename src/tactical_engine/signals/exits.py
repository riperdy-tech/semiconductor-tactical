from datetime import datetime

from tactical_engine.config import ExitConfig
from tactical_engine.data.models import Bar


def check_exit_condition(
    entry_price: float,
    entry_time: datetime,
    current_bar: Bar,
    atr: float,
    config: ExitConfig,
    stop_price: float | None = None,
    target_price: float | None = None,
) -> tuple[bool, str]:
    # 1. Time-based exit check
    hold_duration = (current_bar.timestamp - entry_time).total_seconds() / 60.0
    if hold_duration >= config.max_hold_minutes:
        return True, f"time_stop ({hold_duration:.0f}m >= {config.max_hold_minutes}m)"

    # 2. Price-based targets & stops: use stored values if provided to prevent ATR drift
    if stop_price is None or target_price is None:
        if config.family == "atr":
            calc_stop = entry_price - (config.stop_atr * atr)
            calc_target = entry_price + (config.target_atr * atr)
        elif config.family == "fixed_pct":
            calc_stop = entry_price * (1.0 - config.stop_pct)
            calc_target = entry_price * (1.0 + config.target_pct)
        else:
            # Default fallback
            calc_stop = entry_price - (1.0 * atr)
            calc_target = entry_price + (1.5 * atr)
        stop_price = stop_price if stop_price is not None else calc_stop
        target_price = target_price if target_price is not None else calc_target

    # Intrabar ambiguity rule (BACKTEST_PROTOCOL.md §3):
    # If both stop and target touched in the same bar, assume stop hit first (conservative).
    stop_hit = current_bar.low <= stop_price
    target_hit = current_bar.high >= target_price

    if stop_hit and target_hit:
        return True, "stop_loss_hit (conservative intrabar ambiguity resolution)"
    if stop_hit:
        return True, f"stop_loss_hit ({current_bar.low:.2f} <= {stop_price:.2f})"
    if target_hit:
        return True, f"target_hit ({current_bar.high:.2f} >= {target_price:.2f})"

    return False, ""
