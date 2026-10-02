from datetime import datetime

from pydantic import BaseModel, Field

from tactical_engine.data.models import Bar


class DatasetValidationResult(BaseModel):
    symbol: str
    row_count: int
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_valid: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    calendar_gaps_count: int = 0
    missing_minute_slots: int = 0
    rth_coverage_pct: float = 100.0
    gaps_count: int = 0
    duplicates_count: int = 0


def validate_bar_sequence(bars: list[Bar]) -> None:
    """Ensure bars are non-empty and strictly monotonically increasing in timestamp."""
    if not bars:
        return
    for i in range(1, len(bars)):
        if bars[i].timestamp <= bars[i - 1].timestamp:
            raise ValueError(
                f"Monotonic timestamp violation: {bars[i].timestamp} <= {bars[i - 1].timestamp}"
            )


def detect_duplicates(bars: list[Bar]) -> list[datetime]:
    """Find timestamps that occur more than once in the bar series."""
    seen: set[datetime] = set()
    dupes: list[datetime] = []
    for bar in bars:
        if bar.timestamp in seen:
            dupes.append(bar.timestamp)
        else:
            seen.add(bar.timestamp)
    return dupes


def detect_time_gaps(
    bars: list[Bar], max_gap_seconds: float = 86400 * 5
) -> list[tuple[datetime, datetime]]:
    """Detect time gaps between consecutive bars exceeding the threshold
    (e.g. 5 days for daily bars)."""
    gaps: list[tuple[datetime, datetime]] = []
    for i in range(1, len(bars)):
        dt_diff = (bars[i].timestamp - bars[i - 1].timestamp).total_seconds()
        if dt_diff > max_gap_seconds:
            gaps.append((bars[i - 1].timestamp, bars[i].timestamp))
    return gaps


def detect_price_anomalies(
    bars: list[Bar], max_pct_move: float = 0.5
) -> list[tuple[datetime, float]]:
    """Detect single-bar close-to-close jumps exceeding max_pct_move (potential split artifact)."""
    anomalies: list[tuple[datetime, float]] = []
    for i in range(1, len(bars)):
        prev_close = bars[i - 1].close
        if prev_close <= 0:
            continue
        pct_change = abs(bars[i].close - prev_close) / prev_close
        if pct_change >= max_pct_move:
            anomalies.append((bars[i].timestamp, pct_change))
    return anomalies


def validate_resolution_cadence(
    bars: list[Bar], declared_interval: str | None = None
) -> tuple[bool, str]:
    """Validate that the observed timestamp cadence matches the declared resolution,

    distinguishing regular session spacing from legitimate overnight/weekend gaps.
    """
    if not declared_interval or len(bars) < 2:
        return True, ""

    interval_clean = declared_interval.lower().strip()
    expected_map = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "1h": 3600,
        "1d": 86400,
        "daily": 86400,
    }

    expected_sec = expected_map.get(interval_clean)
    if expected_sec is None:
        return True, ""

    # Separate intrasession transitions (same calendar day) from intersession transitions
    intrasession_deltas: list[float] = []
    intersession_deltas: list[float] = []

    for i in range(1, len(bars)):
        prev_dt = bars[i - 1].timestamp
        curr_dt = bars[i].timestamp
        delta_sec = (curr_dt - prev_dt).total_seconds()

        if prev_dt.date() == curr_dt.date():
            intrasession_deltas.append(delta_sec)
        else:
            intersession_deltas.append(delta_sec)

    # 1. Validation for Intraday intervals (1m, 5m, 15m, 1h)
    if interval_clean in ("1m", "5m", "15m", "1h"):
        # If there are no intrasession deltas at all, all bars are on separate calendar days
        if not intrasession_deltas:
            all_deltas = sorted(
                (bars[i].timestamp - bars[i - 1].timestamp).total_seconds()
                for i in range(1, len(bars))
            )
            med_all = all_deltas[len(all_deltas) // 2]
            return False, (
                f"Resolution cadence mismatch: declared '{declared_interval}' "
                f"(expected ~{expected_sec}s), but all bars occur on separate calendar "
                f"dates with median spacing {med_all:.0f}s. Data is daily, not intraday."
            )

        intrasession_deltas.sort()
        median_intrasession = intrasession_deltas[len(intrasession_deltas) // 2]

        if median_intrasession > expected_sec * 3:
            return False, (
                f"Resolution cadence mismatch: declared '{declared_interval}' "
                f"(expected ~{expected_sec}s), but observed median intrasession spacing is "
                f"{median_intrasession:.0f}s."
            )

    # 2. Validation for Daily intervals (1d, daily)
    elif interval_clean in ("1d", "daily"):
        # Daily data must have at most 1 bar per calendar day during regular trading
        if intrasession_deltas:
            intrasession_deltas.sort()
            median_intrasession = intrasession_deltas[len(intrasession_deltas) // 2]
            if median_intrasession < 3600 * 12:
                return False, (
                    f"Resolution cadence mismatch: declared '{declared_interval}' "
                    f"(expected daily bars), but found multiple intraday bars on the same date "
                    f"with median spacing {median_intrasession:.0f}s."
                )

    return True, ""



def validate_symbol_bars(
    symbol: str,
    bars: list[Bar],
    max_gap_seconds: float = 86400 * 5,
    expected_interval: str | None = None,
) -> DatasetValidationResult:
    """Comprehensive validation of a symbol's historical bar series."""
    if not bars:
        return DatasetValidationResult(
            symbol=symbol,
            row_count=0,
            is_valid=False,
            errors=["No bars provided for symbol"],
        )

    errors: list[str] = []
    warnings: list[str] = []

    # Check duplicates
    dupes = detect_duplicates(bars)
    if dupes:
        errors.append(f"Found {len(dupes)} duplicate timestamps (first: {dupes[0]})")

    # Check monotonicity
    try:
        validate_bar_sequence(bars)
    except ValueError as e:
        if not dupes:
            errors.append(str(e))

    # Check resolution cadence if declared
    if expected_interval:
        cadence_ok, cadence_err = validate_resolution_cadence(bars, expected_interval)
        if not cadence_ok:
            errors.append(cadence_err)

    # Check OHLC relations and volume
    for bar in bars:
        if bar.open <= 0 or bar.high <= 0 or bar.low <= 0 or bar.close <= 0:
            errors.append(f"Non-positive price detected at {bar.timestamp}")
            break
        if bar.volume < 0:
            errors.append(f"Negative volume detected at {bar.timestamp}")
            break
        if bar.high < bar.low or bar.open > bar.high or bar.close > bar.high:
            errors.append(f"OHLC violation at {bar.timestamp}")
            break

    # Check calendar gaps (> max_gap_seconds)
    calendar_gaps = detect_time_gaps(bars, max_gap_seconds=max_gap_seconds)
    if calendar_gaps:
        warnings.append(
            f"Detected {len(calendar_gaps)} calendar gaps > {max_gap_seconds / 86400:.1f} days "
            f"(first: {calendar_gaps[0][0]} -> {calendar_gaps[0][1]})"
        )

    # Check intraday missing minute slots if 1m resolution
    missing_minute_slots = 0
    rth_coverage_pct = 100.0
    if expected_interval and expected_interval.lower().strip() == "1m":
        total_missing = 0
        for i in range(1, len(bars)):
            prev_b = bars[i - 1]
            curr_b = bars[i]
            if prev_b.timestamp.date() == curr_b.timestamp.date():
                delta_m = (curr_b.timestamp - prev_b.timestamp).total_seconds() / 60.0
                if delta_m > 1.0:
                    total_missing += int(round(delta_m - 1.0))
        missing_minute_slots = total_missing
        expected_rth_bars = len(bars) + total_missing
        if expected_rth_bars > 0:
            rth_coverage_pct = round((len(bars) / expected_rth_bars) * 100.0, 2)
        if missing_minute_slots > 0:
            warnings.append(
                f"Observed {missing_minute_slots} missing 1-minute slots during RTH "
                f"({rth_coverage_pct:.1f}% coverage; legitimate zero-trade intervals)"
            )

    # Check price jumps / potential splits
    anomalies = detect_price_anomalies(bars)
    if anomalies:
        warnings.append(
            f"Detected {len(anomalies)} large price jumps >= 50% "
            f"(first: {anomalies[0][0]} {anomalies[0][1] * 100:.1f}%)"
        )

    return DatasetValidationResult(
        symbol=symbol,
        row_count=len(bars),
        start_time=bars[0].timestamp,
        end_time=bars[-1].timestamp,
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        calendar_gaps_count=len(calendar_gaps),
        missing_minute_slots=missing_minute_slots,
        rth_coverage_pct=rth_coverage_pct,
        gaps_count=len(calendar_gaps),
        duplicates_count=len(dupes),
    )

