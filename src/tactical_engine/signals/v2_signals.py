"""Reddit Behavioral Replication V2 — Directional Signal Engine.

Implements the 6-stage behavioral process:
1. Higher-timeframe regime context [Label: HYPOTHESIS]
2. Strong directional impulse [Label: HYPOTHESIS]
3. Retreat / pullback [Label: HYPOTHESIS]
4. Stabilization / reclaim [Label: HYPOTHESIS]
5. Tactical add / reload [Label: HYPOTHESIS]
6. Rebound partial scale-out (50%) & LOCAL_LOW stop invalidation [Label: HYPOTHESIS]

All operations affect strictly the TACTICAL sleeve and never liquidate persistent core holdings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

import pandas as pd
from pydantic import BaseModel

from tactical_engine.data.models import Bar, SignalIntent


class V2SignalState(StrEnum):
    IDLE = "IDLE"
    IMPULSE_OBSERVED = "IMPULSE_OBSERVED"
    PULLBACK_OBSERVED = "PULLBACK_OBSERVED"
    STABILIZING = "STABILIZING"
    TACTICAL_LONG = "TACTICAL_LONG"
    PARTIALLY_REDUCED = "PARTIALLY_REDUCED"


class V2DirectionalConfig(BaseModel):
    """Frozen pre-registered V2 candidate parameters."""

    impulse_lookback_bars: int = 30  # 30-minute impulse window
    min_impulse_pct: float = 0.020  # 2.0% minimum surge
    pullback_depth_fraction: float = 0.500  # 50% retracement of impulse range
    stabilization_bars: int = 5  # 5 bars of consolidation above local low
    tactical_scale_out_ratio: float = 0.50  # 50% partial exit on rebound
    stop_buffer_pct: float = 0.002  # 0.2% buffer below local low pivot
    rebound_target_ratio: float = 0.50  # 50% rebound of pullback distance toward impulse peak
    trend_filter: bool = True
    stop_mode: str = "LOCAL_LOW"


@dataclass
class V2SymbolTracker:
    symbol: str
    state: V2SignalState = V2SignalState.IDLE
    impulse_low: float = 0.0
    impulse_high: float = 0.0
    impulse_high_time: datetime | None = None
    pullback_trough: float = 0.0
    pullback_trough_time: datetime | None = None
    stabilization_bar_count: int = 0
    entry_price: float = 0.0
    stop_price: float = 0.0
    partial_target_price: float = 0.0
    tactical_units: int = 0  # 1 for initial add, 2 for reload


# ---------------------------------------------------------------------------
# Stage 1: Higher-Timeframe Trend / Regime Predicate [Label: HYPOTHESIS]
# ---------------------------------------------------------------------------
def check_regime_context_predicate(
    df: pd.DataFrame,
    current_idx: int,
    trend_filter: bool = True,
) -> tuple[bool, str]:
    """Evaluates whether broader trend allows tactical longs.

    Mechanical proxy: price above 60-bar simple moving average with non-negative slope.
    """
    if not trend_filter:
        return True, "trend_filter_disabled"

    if current_idx < 60:
        return True, "insufficient_bars_for_trend"

    closes = df["close"].iloc[current_idx - 59 : current_idx + 1]
    sma_60 = closes.mean()
    current_close = closes.iloc[-1]

    if current_idx >= 65:
        sma_prev = df["close"].iloc[current_idx - 64 : current_idx - 4].mean()
    else:
        sma_prev = sma_60
    slope = sma_60 - sma_prev

    if current_close < sma_60 or slope < -1e-5:
        return False, f"trend_bearish (close={current_close:.2f} < sma={sma_60:.2f})"

    return True, "trend_bullish"


# ---------------------------------------------------------------------------
# Stage 2: Directional Impulse Predicate [Label: HYPOTHESIS]
# ---------------------------------------------------------------------------
def check_directional_impulse_predicate(
    df: pd.DataFrame,
    current_idx: int,
    lookback_bars: int = 30,
    min_impulse_pct: float = 0.020,
) -> tuple[bool, float, float]:
    """Detects strong directional impulse thrust over lookback window.

    Returns (is_impulse, impulse_low, impulse_high).
    """
    if current_idx < lookback_bars:
        return False, 0.0, 0.0

    window = df.iloc[current_idx - lookback_bars + 1 : current_idx + 1]
    low_val = float(window["low"].min())
    high_val = float(window["high"].max())

    if low_val <= 0:
        return False, 0.0, 0.0

    impulse_pct = (high_val - low_val) / low_val
    if impulse_pct >= min_impulse_pct:
        # Verify the peak happened after the trough within the window
        low_idx = window["low"].idxmin()
        high_idx = window["high"].idxmax()
        if high_idx >= low_idx:
            return True, low_val, high_val

    return False, 0.0, 0.0


# ---------------------------------------------------------------------------
# Stage 3: Retreat / Pullback Predicate [Label: HYPOTHESIS]
# ---------------------------------------------------------------------------
def check_retreat_pullback_predicate(
    current_low: float,
    current_close: float,
    impulse_low: float,
    impulse_high: float,
    depth_fraction: float = 0.500,
) -> tuple[bool, float]:
    """Evaluates if price has retraced toward target depth fraction of impulse range.

    Target depth: impulse_high - depth_fraction * (impulse_high - impulse_low).
    """
    impulse_range = impulse_high - impulse_low
    if impulse_range <= 0:
        return False, 0.0

    target_pullback_level = impulse_high - (depth_fraction * impulse_range)
    # Pullback confirmed if current price touches or drops below the target depth
    if current_low <= target_pullback_level:
        return True, target_pullback_level

    return False, target_pullback_level


# ---------------------------------------------------------------------------
# Stage 4: Stabilization / Reclaim Predicate [Label: HYPOTHESIS]
# ---------------------------------------------------------------------------
def check_stabilization_reclaim_predicate(
    recent_bars: list[Bar],
    pullback_trough: float,
    min_stabilization_bars: int = 5,
    buffer_pct: float = 0.001,
) -> bool:
    """Verifies price has stabilized above local trough for min_stabilization_bars.

    Does not make a fresh lower low beyond buffer, and closes constructively.
    """
    if len(recent_bars) < min_stabilization_bars:
        return False

    check_window = recent_bars[-min_stabilization_bars:]
    breakout_floor = pullback_trough * (1.0 - buffer_pct)

    for b in check_window:
        if b.low < breakout_floor:
            return False  # Failed stabilization: new low made

    # Reclaim condition: last bar closes above the open or above window median
    last_bar = check_window[-1]
    return last_bar.close >= last_bar.open or last_bar.close >= pullback_trough


# ---------------------------------------------------------------------------
# V2 Directional Signal Generator State Machine
# ---------------------------------------------------------------------------
class V2SignalGenerator:
    """State machine tracking intraday swing progression for tactical trading."""

    def __init__(self, config: V2DirectionalConfig | None = None) -> None:
        self.config = config or V2DirectionalConfig()
        self.trackers: dict[str, V2SymbolTracker] = {}
        self.recent_bars: dict[str, list[Bar]] = {}

    def get_tracker(self, symbol: str) -> V2SymbolTracker:
        if symbol not in self.trackers:
            self.trackers[symbol] = V2SymbolTracker(symbol=symbol)
        return self.trackers[symbol]

    def process_bar(
        self,
        bar: Bar,
        df: pd.DataFrame,
        current_idx: int,
        current_tactical_shares: float = 0.0,
    ) -> SignalIntent | None:
        """Processes one bar and generates tactical signals.

        Returns SignalIntent for tactical ENTER_LONG or EXIT_LONG, or None.
        """
        sym = bar.symbol
        tracker = self.get_tracker(sym)

        # Maintain recent bar history
        if sym not in self.recent_bars:
            self.recent_bars[sym] = []
        self.recent_bars[sym].append(bar)
        if len(self.recent_bars[sym]) > 100:
            self.recent_bars[sym].pop(0)

        # Sync position state
        if current_tactical_shares <= 0 and tracker.state in (
            V2SignalState.TACTICAL_LONG,
            V2SignalState.PARTIALLY_REDUCED,
        ):
            tracker.state = V2SignalState.IDLE
            tracker.tactical_units = 0

        # -------------------------------------------------------------------
        # In-Position Management: Exit / Scale-Out / Stop Check
        # -------------------------------------------------------------------
        if tracker.state in (V2SignalState.TACTICAL_LONG, V2SignalState.PARTIALLY_REDUCED):
            # 1. Stop Loss: LOCAL_LOW invalidation
            if bar.low <= tracker.stop_price:
                tracker.state = V2SignalState.IDLE
                tracker.tactical_units = 0
                return SignalIntent(
                    symbol=sym,
                    timestamp=bar.timestamp,
                    action="EXIT_LONG",
                    strength=1.0,  # Full exit of remaining tactical shares
                    reason=(
                        f"v2_local_low_stop_hit "
                        f"(price={bar.low:.2f} <= stop={tracker.stop_price:.2f})"
                    ),
                    stop_price=tracker.stop_price,
                )

            # 2. Rebound Target: 50% partial exit
            is_rebound = (
                tracker.state == V2SignalState.TACTICAL_LONG
                and bar.high >= tracker.partial_target_price
            )
            if is_rebound:
                tracker.state = V2SignalState.PARTIALLY_REDUCED
                # Move stop to breakeven or trail up
                tracker.stop_price = max(tracker.stop_price, tracker.entry_price * 0.999)
                return SignalIntent(
                    symbol=sym,
                    timestamp=bar.timestamp,
                    action="EXIT_LONG",
                    strength=self.config.tactical_scale_out_ratio,  # 50% scale-out
                    reason=(
                        f"v2_rebound_50pct_partial_exit "
                        f"(high={bar.high:.2f} >= target={tracker.partial_target_price:.2f})"
                    ),
                    target_price=tracker.partial_target_price,
                )

            # 3. Reload Condition: If partially reduced and secondary pullback stabilizes
            if tracker.state == V2SignalState.PARTIALLY_REDUCED and tracker.tactical_units == 1:
                # Can reload if price pulls back above initial stop and forms secondary base
                if bar.low > tracker.stop_price and bar.close > tracker.entry_price:
                    tracker.tactical_units = 2
                    return SignalIntent(
                        symbol=sym,
                        timestamp=bar.timestamp,
                        action="ENTER_LONG",
                        strength=0.5,  # Reload second half
                        reason="v2_tactical_reload_on_continuation",
                        stop_price=tracker.stop_price,
                    )

            return None

        # -------------------------------------------------------------------
        # Entry Hunting: 6-Stage Sequence
        # -------------------------------------------------------------------
        regime_ok, _ = check_regime_context_predicate(
            df=df,
            current_idx=current_idx,
            trend_filter=self.config.trend_filter,
        )
        if not regime_ok:
            tracker.state = V2SignalState.IDLE
            return None

        # Stage 2: Check Impulse
        is_impulse, imp_low, imp_high = check_directional_impulse_predicate(
            df=df,
            current_idx=current_idx,
            lookback_bars=self.config.impulse_lookback_bars,
            min_impulse_pct=self.config.min_impulse_pct,
        )

        if is_impulse:
            if tracker.state == V2SignalState.IDLE or imp_high > tracker.impulse_high:
                tracker.state = V2SignalState.IMPULSE_OBSERVED
                tracker.impulse_low = imp_low
                tracker.impulse_high = imp_high
                tracker.impulse_high_time = bar.timestamp
                tracker.pullback_trough = bar.low
                tracker.stabilization_bar_count = 0

        # Stage 3: Check Pullback
        if tracker.state == V2SignalState.IMPULSE_OBSERVED:
            is_pullback, target_level = check_retreat_pullback_predicate(
                current_low=bar.low,
                current_close=bar.close,
                impulse_low=tracker.impulse_low,
                impulse_high=tracker.impulse_high,
                depth_fraction=self.config.pullback_depth_fraction,
            )
            if is_pullback:
                tracker.state = V2SignalState.PULLBACK_OBSERVED
                tracker.pullback_trough = bar.low
                tracker.pullback_trough_time = bar.timestamp
                tracker.stabilization_bar_count = 1
            else:
                # Update peak if continues higher
                if bar.high > tracker.impulse_high:
                    tracker.impulse_high = bar.high
                    tracker.impulse_high_time = bar.timestamp

        # Stage 4: Check Stabilization
        elif tracker.state == V2SignalState.PULLBACK_OBSERVED:
            if bar.low < tracker.pullback_trough:
                # Deeper pullback: update trough and reset count
                tracker.pullback_trough = bar.low
                tracker.pullback_trough_time = bar.timestamp
                tracker.stabilization_bar_count = 1
            else:
                tracker.stabilization_bar_count += 1

            if tracker.stabilization_bar_count >= self.config.stabilization_bars:
                is_stabilized = check_stabilization_reclaim_predicate(
                    recent_bars=self.recent_bars[sym],
                    pullback_trough=tracker.pullback_trough,
                    min_stabilization_bars=self.config.stabilization_bars,
                )
                if is_stabilized:
                    # Setup valid! Stage 5: Tactical Add
                    tracker.state = V2SignalState.TACTICAL_LONG
                    tracker.entry_price = bar.close
                    tracker.tactical_units = 1

                    # Structural Stop: LOCAL_LOW pivot minus buffer
                    stop_buf = 1.0 - self.config.stop_buffer_pct
                    tracker.stop_price = tracker.pullback_trough * stop_buf

                    # Rebound Target: 50% retracement of pullback range back toward peak
                    pullback_dist = tracker.impulse_high - tracker.pullback_trough
                    rebound_gain = self.config.rebound_target_ratio * pullback_dist
                    tracker.partial_target_price = bar.close + rebound_gain

                    return SignalIntent(
                        symbol=sym,
                        timestamp=bar.timestamp,
                        action="ENTER_LONG",
                        strength=1.0,
                        reason=(
                            f"v2_tactical_add:impulse={tracker.impulse_low:.2f}->{tracker.impulse_high:.2f},"
                            f"trough={tracker.pullback_trough:.2f},stab_bars={tracker.stabilization_bar_count}"
                        ),
                        stop_price=tracker.stop_price,
                        target_price=tracker.partial_target_price,
                    )

        return None
