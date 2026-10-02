from tactical_engine.data.models import Position


def calculate_margin_debt(cash: float) -> float:
    return max(0.0, -cash)


def calculate_margin_interest(debt: float, rate_annual: float, elapsed_seconds: float) -> float:
    if debt <= 0 or rate_annual <= 0 or elapsed_seconds <= 0:
        return 0.0
    # Annual rate amortized by actual seconds (365 days / year basis)
    year_fraction = elapsed_seconds / (365.0 * 86400.0)
    return debt * rate_annual * year_fraction


def calculate_maintenance_requirement(
    positions: dict[str, Position],
    current_prices: dict[str, float],
    maintenance_ratio: float = 0.25,
) -> float:
    total_market_value = 0.0
    for sym, pos in positions.items():
        price = current_prices.get(sym, pos.avg_price)
        total_market_value += abs(pos.quantity * price)
    return total_market_value * maintenance_ratio


def is_margin_call(equity: float, maintenance_requirement: float) -> bool:
    return equity < maintenance_requirement
