from datetime import UTC, datetime

from tactical_engine.data.models import AccountState, Position
from tactical_engine.portfolio.margin import (
    calculate_buying_power,
    calculate_residual_debt,
    generate_forced_liquidation_orders,
    is_margin_call,
)


def test_buying_power_calculation():
    # Equity $100k, Current positions $50k
    # At 1.0x leverage: max exposure $100k -> remaining buying power $50k
    bp_1x = calculate_buying_power(
        equity=100_000.0, current_positions_value=50_000.0, max_leverage=1.0
    )
    assert bp_1x == 50_000.0

    # At 2.0x leverage: max exposure $200k -> remaining buying power $150k
    bp_2x = calculate_buying_power(
        equity=100_000.0, current_positions_value=50_000.0, max_leverage=2.0
    )
    assert bp_2x == 150_000.0


def test_residual_debt_on_severe_account_deficit():
    # Cash -$50k, positions $30k -> uncollateralized residual debt = $20,000
    res_debt = calculate_residual_debt(cash=-50_000.0, remaining_positions_value=30_000.0)
    assert res_debt == 20_000.0

    # Solvency case: Cash -$10k, positions $40k -> Net equity $30k -> 0 residual debt
    solvent_debt = calculate_residual_debt(cash=-10_000.0, remaining_positions_value=40_000.0)
    assert solvent_debt == 0.0


def test_multi_position_forced_liquidation_ordering():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    state = AccountState(
        timestamp=t0,
        cash=-80_000.0,  # Negative cash (margin debt)
        equity=20_000.0,  # Total equity $20k
        positions={
            "AMD": Position(symbol="AMD", quantity=1000.0, avg_price=20.0),  # $20k position
            "MU": Position(symbol="MU", quantity=800.0, avg_price=100.0),  # $80k position
        },
    )
    # Total position value = $100k. Maintenance ratio 25% = $25k. Equity is $20k < $25k
    current_prices = {"MU": 100.0, "AMD": 20.0}
    assert is_margin_call(state.equity, 25_000.0) is True

    orders = generate_forced_liquidation_orders(state, current_prices, maintenance_ratio=0.25)
    assert len(orders) >= 1
    # Verify largest position (MU with $80k) was selected first for liquidation
    assert orders[0].symbol == "MU"
    assert "forced_liquidation" in orders[0].tag
