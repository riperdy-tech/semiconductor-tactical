from tactical_engine.data.models import Position
from tactical_engine.portfolio.margin import (
    calculate_maintenance_requirement,
    calculate_margin_debt,
    calculate_margin_interest,
    is_margin_call,
)


def test_calculate_margin_debt():
    assert calculate_margin_debt(cash=5000.0) == 0.0
    assert calculate_margin_debt(cash=-10000.0) == 10000.0


def test_calculate_margin_interest():
    # $10,000 debt at 8% annual for 1 day (1/365 of year)
    interest = calculate_margin_interest(
        debt=10000.0,
        rate_annual=0.08,
        elapsed_seconds=86400,
    )
    expected = 10000.0 * 0.08 * (1.0 / 365.0)
    assert round(interest, 2) == round(expected, 2)


def test_maintenance_requirement_and_margin_call():
    positions = {
        "MU": Position(symbol="MU", quantity=100.0, avg_price=100.0),
    }
    current_prices = {"MU": 100.0}
    # Market value = $10,000. Maintenance req at 25% = $2,500
    req = calculate_maintenance_requirement(
        positions=positions,
        current_prices=current_prices,
        maintenance_ratio=0.25,
    )
    assert req == 2500.0

    # Equity = $2,000 < $2,500 -> Margin call
    assert is_margin_call(equity=2000.0, maintenance_requirement=req) is True
    # Equity = $3,000 >= $2,500 -> No margin call
    assert is_margin_call(equity=3000.0, maintenance_requirement=req) is False
