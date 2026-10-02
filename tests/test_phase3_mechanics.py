from datetime import UTC, datetime, timedelta

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig, PortfolioConfig
from tactical_engine.data.models import AccountState, Bar, Fill, OrderSide, Position
from tactical_engine.portfolio.sizing import calculate_position_size


def test_gross_leverage_constrains_portfolio_exposure():
    """Verify that calculate_position_size strictly limits total exposure by max_gross_leverage."""
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    state = AccountState(
        timestamp=t0,
        cash=100_000.0,
        equity=100_000.0,
        positions={
            "MU": Position(symbol="MU", quantity=500.0, avg_price=100.0),  # $50,000 market value
            "AMD": Position(symbol="AMD", quantity=400.0, avg_price=100.0),  # $40,000 market value
        },
    )
    # Total existing position value = $90,000

    current_prices = {"MU": 100.0, "AMD": 100.0, "SNDK": 100.0}

    # At 1.0x leverage: max portfolio gross = $100,000.
    # Remaining capacity = $10,000 -> 100 shares of SNDK
    cfg_1x = PortfolioConfig(max_symbol_weight=0.50, max_gross_leverage=1.0)
    qty_1x = calculate_position_size(
        symbol="SNDK",
        price=100.0,
        stop_price=None,
        account_state=state,
        config=cfg_1x,
        current_prices=current_prices,
    )
    assert qty_1x == 100.0

    # At 1.25x leverage: max portfolio gross = $125,000. Remaining capacity = $35,000 -> 350 shares
    cfg_125x = PortfolioConfig(max_symbol_weight=0.50, max_gross_leverage=1.25)
    qty_125x = calculate_position_size(
        symbol="SNDK",
        price=100.0,
        stop_price=None,
        account_state=state,
        config=cfg_125x,
        current_prices=current_prices,
    )
    assert qty_125x == 350.0

    # At 1.5x leverage: max portfolio gross = $150,000. Max symbol cap is $50,000 -> 500 shares
    cfg_15x = PortfolioConfig(max_symbol_weight=0.50, max_gross_leverage=1.5)
    qty_15x = calculate_position_size(
        symbol="SNDK",
        price=100.0,
        stop_price=None,
        account_state=state,
        config=cfg_15x,
        current_prices=current_prices,
    )
    assert qty_15x == 500.0  # Capped by max_symbol_weight (0.50 * 100,000 = 50,000)

    # At 2.0x leverage with max_symbol_weight=1.5: remaining capacity = $110,000 -> 1100 shares
    cfg_2x = PortfolioConfig(max_symbol_weight=1.5, max_gross_leverage=2.0)
    qty_2x = calculate_position_size(
        symbol="SNDK",
        price=100.0,
        stop_price=None,
        account_state=state,
        config=cfg_2x,
        current_prices=current_prices,
    )
    assert qty_2x == 1100.0


def test_layered_entries_state_and_max_layers():
    """Verify that PortfolioTracker correctly records LayerRecord and enforces layer caps."""
    from tactical_engine.backtest.state import PortfolioTracker

    tracker = PortfolioTracker(initial_cash=100_000.0)
    t0 = datetime(2026, 1, 5, 9, 30, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 9, 35, tzinfo=UTC)

    # Layer 1 fill
    fill1 = Fill(
        order_id="o1",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.BUY,
        quantity=100.0,
        price=100.0,
        commission=1.0,
        slippage=5.0,
    )
    tracker.apply_fill(fill1, stop_price=98.0)

    layers = tracker.layers_by_symbol["MU"]
    assert len(layers) == 1
    assert layers[0].layer_number == 1
    assert layers[0].quantity == 100.0
    assert layers[0].incremental_risk == 200.0  # (100 - 98) * 100
    assert layers[0].aggregate_risk == 200.0

    # Layer 2 fill
    fill2 = Fill(
        order_id="o2",
        symbol="MU",
        timestamp=t1,
        side=OrderSide.BUY,
        quantity=100.0,
        price=95.0,
        commission=1.0,
        slippage=5.0,
    )
    tracker.apply_fill(fill2, stop_price=93.0)

    layers2 = tracker.layers_by_symbol["MU"]
    assert len(layers2) == 2
    assert layers2[1].layer_number == 2
    assert layers2[1].quantity == 100.0
    assert layers2[1].incremental_risk == 200.0
    assert layers2[1].aggregate_risk == 400.0

    # Full exit clears layers
    t2 = datetime(2026, 1, 5, 10, 0, tzinfo=UTC)
    fill_exit = Fill(
        order_id="o3",
        symbol="MU",
        timestamp=t2,
        side=OrderSide.SELL,
        quantity=200.0,
        price=105.0,
        commission=2.0,
        slippage=10.0,
    )
    tracker.apply_fill(fill_exit)
    assert "MU" not in tracker.layers_by_symbol


def test_two_x_etf_trading_execution():
    """Verify backtest executes on actual 2x ETF bars when included."""
    t0 = datetime(2026, 1, 5, 9, 30, tzinfo=UTC)
    bars_usd = []
    price = 25.0
    for i in range(70):
        t = t0 + timedelta(minutes=i)
        price *= 0.995  # pullback
        bars_usd.append(
            Bar(
                symbol="USD",
                timestamp=t,
                open=price * 1.002,
                high=price * 1.004,
                low=price * 0.996,
                close=price,
                volume=50000.0,
            )
        )

    cfg = EngineConfig()
    cfg.strategy.universe = []
    cfg.strategy.two_x_etfs = ["USD"]
    cfg.signals.pullback_zscore = -0.5

    result = run_backtest(data={"USD": bars_usd}, config=cfg)
    # Confirm trades on the 2x ETF were executed
    assert result.total_trades > 0
    assert all(t.symbol == "USD" for t in result.trades)
