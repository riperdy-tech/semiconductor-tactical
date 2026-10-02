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
    """Validate that the observed timestamp cadence matches the declared resolution."""
    if not declared_interval or len(bars) < 2:
        return True, ""

    deltas = [
        (bars[i].timestamp - bars[i - 1].timestamp).total_seconds()
        for i in range(1, min(len(bars), 1000))
    ]
    deltas.sort()
    median_delta = deltas[len(deltas) // 2]

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

    if interval_clean in ("1m", "5m", "15m", "1h"):
        if median_delta > expected_sec * 3:
            return False, (
                f"Resolution cadence mismatch: declared '{declared_interval}' "
                f"(expected ~{expected_sec}s), but observed median bar spacing is "
                f"{median_delta:.0f}s. Data appears to be higher timeframe (e.g. daily)."
            )
    elif interval_clean in ("1d", "daily"):
        if median_delta < 3600 * 12:
            return False, (
                f"Resolution cadence mismatch: declared '{declared_interval}' "
                f"(expected daily ~86400s), but observed median bar spacing is {median_delta:.0f}s "
                f"(intraday data)."
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

    # Check gaps
    gaps = detect_time_gaps(bars, max_gap_seconds=max_gap_seconds)
    if gaps:
        warnings.append(
            f"Detected {len(gaps)} calendar gaps > {max_gap_seconds / 86400:.1f} days "
            f"(first: {gaps[0][0]} -> {gaps[0][1]})"
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
        gaps_count=len(gaps),
        duplicates_count=len(dupes),
    )

