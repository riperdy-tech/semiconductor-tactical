from datetime import UTC, datetime

from tactical_engine.backtest.state import PortfolioTracker
from tactical_engine.data.models import Fill, OrderSide


def test_cash_and_pnl_exact_reconciliation_closed_trades():
    """Verify that net cash change equals sum of net P&L minus margin interest paid."""
    initial_cash = 100_000.0
    tracker = PortfolioTracker(initial_cash=initial_cash)

    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t1 = datetime(2026, 1, 5, 14, 35, tzinfo=UTC)
    t2 = datetime(2026, 1, 5, 15, 0, tzinfo=UTC)

    # 1. Buy 100 shares at $100.10 (base 100.0 + 0.10 slippage), $1.00 commission
    fill_buy1 = Fill(
        order_id="b1",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.BUY,
        quantity=100.0,
        price=100.10,
        commission=1.00,
        slippage=10.00,
    )
    tracker.apply_fill(fill_buy1)
    # Cash should be: 100_000 - (100 * 100.10 + 1.00) = 89,989.00
    assert tracker.cash == 89_989.00

    # 2. Layer 2: Buy 100 shares at $95.10 (base 95.0 + 0.10 slippage), $1.00 commission
    fill_buy2 = Fill(
        order_id="b2",
        symbol="MU",
        timestamp=t1,
        side=OrderSide.BUY,
        quantity=100.0,
        price=95.10,
        commission=1.00,
        slippage=10.00,
    )
    tracker.apply_fill(fill_buy2)
    # Cash should be: 89,989 - (100 * 95.10 + 1.00) = 80,478.00
    assert tracker.cash == 80_478.00
    # Avg price: (100 * 100.10 + 100 * 95.10) / 200 = 97.60
    assert tracker.positions["MU"].avg_price == 97.60

    # 3. Sell all 200 shares at $105.00 (base 105.10 - 0.10 slippage), $2.00 commission
    fill_sell = Fill(
        order_id="s1",
        symbol="MU",
        timestamp=t2,
        side=OrderSide.SELL,
        quantity=200.0,
        price=105.00,
        commission=2.00,
        slippage=20.00,
    )
    tracker.apply_fill(fill_sell, exit_reason="profit_target")
    # Proceeds: 200 * 105.00 - 2.00 = 20,998.00
    # Ending cash: 80,478.00 + 20,998.00 = 101,476.00
    assert tracker.cash == 101_476.00
    assert len(tracker.closed_trades) == 1

    trade = tracker.closed_trades[0]
    # Gross P&L: (105.00 - 97.60) * 200 = 7.40 * 200 = 1,480.00
    assert trade.gross_pnl == 1480.00
    # Total commission: entry ($1 + $1) + exit ($2) = $4.00
    assert trade.commission_paid == 4.00
    # Net P&L: 1480.00 - 4.00 = 1476.00
    assert trade.net_pnl == 1476.00
    # Slippage paid: entry ($10 + $10) + exit ($20) = $40.00
    assert trade.slippage_paid == 40.00

    # Exact reconciliation check
    cash_change = tracker.cash - initial_cash
    assert round(cash_change, 2) == round(trade.net_pnl, 2)


def test_equity_and_unrealized_pnl_reconciliation():
    """Verify equity reconciliation with both closed trades and open positions."""
    initial_cash = 50_000.0
    tracker = PortfolioTracker(initial_cash=initial_cash)
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)

    # Buy AMD
    tracker.apply_fill(
        Fill(
            order_id="b1",
            symbol="AMD",
            timestamp=t0,
            side=OrderSide.BUY,
            quantity=500.0,
            price=10.00,
            commission=1.00,
            slippage=2.50,
        )
    )

    # Current market price is $12.00 -> unrealized gain of ($12 - $10) * 500 = $1,000.00
    current_prices = {"AMD": 12.00}
    state = tracker.get_account_state(t0, current_prices)

    # Cash: 50,000 - (5,000 + 1) = 44,999.00
    assert tracker.cash == 44_999.00
    # Market value: 500 * 12 = 6,000.00
    # Total equity: 44,999.00 + 6,000.00 = 50,999.00
    assert state.equity == 50_999.00
    # Equity change: 50,999 - 50,000 = +999.00 (Unrealized $1,000 - $1.00 entry commission)
    equity_change = state.equity - initial_cash
    assert equity_change == 999.00
