from datetime import UTC, datetime

from tactical_engine.data.models import AccountState, OrderSide, Position
from tactical_engine.portfolio.margin import generate_forced_liquidation_orders


def test_generate_forced_liquidation_orders():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    positions = {
        "MU": Position(symbol="MU", quantity=100.0, avg_price=100.0),
        "AMD": Position(symbol="AMD", quantity=50.0, avg_price=100.0),
    }
    current_prices = {"MU": 100.0, "AMD": 100.0}
    # Market value = $15,000. Cash = -$13,000 -> Equity = $2,000.
    # Maintenance requirement at 25% = $3,750 > $2,000 equity (margin call!).
    state = AccountState(
        timestamp=t0,
        cash=-13000.0,
        positions=positions,
        margin_debt=13000.0,
        equity=2000.0,
    )

    orders = generate_forced_liquidation_orders(
        account_state=state,
        current_prices=current_prices,
        maintenance_ratio=0.25,
    )

    assert len(orders) > 0
    assert all(o.side == OrderSide.SELL for o in orders)
    assert all("forced_liquidation" in o.tag for o in orders)
