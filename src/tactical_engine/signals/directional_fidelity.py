import pandas as pd

from tactical_engine.config import SignalConfig
from tactical_engine.data.models import SignalIntent
from tactical_engine.signals.regime import RegimeProvider


def check_trend_predicate(
    row: pd.Series,
    regime_provider: RegimeProvider | None = None,
    timestamp: pd.Timestamp | None = None,
    sector_filter: bool = True,
) -> tuple[bool, str]:
    """Trend State Predicate [Label: HYPOTHESIS].

    Mechanical proxy: requires positive trend slope and moving average alignment,
    with optional semiconductor sector trend confirmation.
    """
    trend_ok = bool(row.get("trend_ok", True))
    trend_slope = float(row.get("trend_slope", 0.0))

    if not trend_ok or trend_slope <= 0.0:
        return False, "trend_slope_non_positive_or_ma_misaligned"

    if sector_filter and regime_provider is not None and timestamp is not None:
        state = regime_provider.get_regime_state(timestamp)
        if not state.regime_allows_trade:
            return False, f"sector_regime_blocked:sector_ok={state.sector_trend_ok}"

    return True, "trend_intact"


def check_pullback_predicate(
    row: pd.Series,
    pullback_min_pct: float = 0.005,
    pullback_max_pct: float = 0.030,
    stabilization_threshold: float = 0.35,
) -> tuple[bool, str]:
    """Pullback State Predicate [Label: HYPOTHESIS].

    Mechanical proxy: evaluates dip depth from recent 20-bar high without catching
    a falling knife, requiring local bar stabilization.
    """
    dist_high = float(row.get("dist_high", 0.0))
    pullback_depth = abs(dist_high)

    if not (pullback_min_pct <= pullback_depth <= pullback_max_pct):
        return False, f"pullback_depth_out_of_bounds ({pullback_depth:.3f})"

    # Bar stabilization check: close in upper half of bar or positive return vs prior bar
    high = float(row.get("high", row.get("close", 1.0)))
    low = float(row.get("low", row.get("close", 1.0)))
    close = float(row.get("close", 1.0))
    bar_range = high - low

    if bar_range > 1e-6:
        bar_pos = (close - low) / bar_range
    else:
        bar_pos = 0.5

    returns = float(row.get("returns", 0.0))
    is_stabilized = (bar_pos >= stabilization_threshold) or (returns >= 0.0)

    if not is_stabilized:
        return False, "pullback_not_stabilized"

    return True, f"pullback_confirmed:depth={pullback_depth:.3f}"


def check_strength_predicate(row: pd.Series) -> bool:
    """Strength State Predicate [Label: HYPOTHESIS].

    Used by the covered-call overlay to determine when underlying is at strength.
    """
    dist_high = float(row.get("dist_high", 0.0))
    returns = float(row.get("returns", 0.0))
    trend_ok = bool(row.get("trend_ok", True))
    return dist_high >= -0.003 and returns > 0 and trend_ok


def generate_directional_fidelity_signals(
    df: pd.DataFrame,
    config: SignalConfig,
    regime_provider: RegimeProvider | None = None,
) -> list[SignalIntent]:
    """Directional Fidelity Signal Generator [Label: HYPOTHESIS / DERIVED].

    Approximates discretionary trend-following dip entries with structured stop-limit
    parameters, avoiding high-frequency tick churn.
    """
    signals = []
    if df.empty:
        return signals

    symbol = str(df["symbol"].iloc[0])
    for timestamp, row in df.iterrows():
        # 1. Trend Predicate
        trend_allows, trend_msg = check_trend_predicate(
            row=row,
            regime_provider=regime_provider,
            timestamp=timestamp,  # type: ignore
            sector_filter=config.sector_filter,
        )

        # 2. Pullback Predicate
        pullback_allows, pb_msg = check_pullback_predicate(
            row=row,
            pullback_min_pct=config.pullback_min_pct,
            pullback_max_pct=config.pullback_max_pct,
            stabilization_threshold=config.stabilization_threshold,
        )

        # 3. Relative Volume Filter [Label: ASSUMPTION]
        rel_vol_ok = True
        if config.relative_volume_filter and "rel_volume" in row:
            rel_vol_ok = float(row["rel_volume"]) >= 0.5

        # 4. Event Filter [Label: ASSUMPTION]
        event_ok = True
        if config.event_filter and "is_event_blackout" in row:
            event_ok = not bool(row["is_event_blackout"])

        if trend_allows and pullback_allows and rel_vol_ok and event_ok:
            close_p = float(row["close"])
            atr = float(row.get("atr", 1.0))
            trigger_p = close_p
            target_p = round(close_p + config.swing_target_atr * atr, 4)

            signals.append(
                SignalIntent(
                    symbol=symbol,
                    timestamp=timestamp,  # type: ignore
                    action="ENTER_LONG",
                    strength=1.0,
                    reason=f"fidelity_swing:{pb_msg}:{trend_msg}",
                    stop_price=trigger_p,
                    target_price=target_p,
                )
            )
        else:
            signals.append(
                SignalIntent(
                    symbol=symbol,
                    timestamp=timestamp,  # type: ignore
                    action="HOLD",
                )
            )

    return signals
