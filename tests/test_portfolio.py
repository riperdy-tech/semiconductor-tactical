from datetime import datetime, timezone
from tactical_engine.config import PortfolioConfig
from tactical_engine.data.models import AccountState
from tactical_engine.portfolio.sizing import calculate_position_size


def test_position_sizing_respects_max_weight():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    state = AccountState(timestamp=t0, cash=100_000.0, equity=100_000.0)
    cfg = PortfolioConfig(max_symbol_weight=0.25)
    # Price $100 -> max allocation $25,000 -> 250 shares
    qty = calculate_position_size(
        symbol="MU",
        price=100.0,
        stop_price=None,
        account_state=state,
        config=cfg,
    )
    assert qty == 250.0


def test_position_sizing_constrained_by_risk():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    state = AccountState(timestamp=t0, cash=100_000.0, equity=100_000.0)
    cfg = PortfolioConfig(max_symbol_weight=0.50, risk_per_trade_pct=0.50)
    # 0.50% of $100,000 = $500 risk. Stop at $98 with entry at $100 -> $2 risk/share -> 250 shares
    qty = calculate_position_size(
        symbol="MU",
        price=100.0,
        stop_price=98.0,
        account_state=state,
        config=cfg,
    )
    assert qty == 250.0
