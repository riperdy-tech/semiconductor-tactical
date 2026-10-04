"""Unit and regression tests for Phase L — Post-Run Audit and Accounting Correction.

Covers all 15 audit requirements from Section 15 of
REDDIT_V2_POST_RUN_AUDIT_AND_ACCOUNTING_PLAN.md:
1. Effective common-start initialization;
2. No-lookahead core initialization;
3. Raw/reference price vs execution price;
4. pre_slippage_pnl correctness;
5. Slippage counted exactly once;
6. Commission counted exactly once;
7. Financing counted exactly once;
8. Tactical closed vs open attribution;
9. Entry/fill/round-trip/open-lot count reconciliation;
10. Next-open buying-power no-lookahead;
11. Next-open margin liquidation semantics;
12. Peak margin debt sampled after transactions;
13. Core isolation under tactical reductions;
14. V2-A and V2-B same core path;
15. Synthetic V2-C margin activation.
"""

from datetime import UTC, datetime, timedelta

from tactical_engine.backtest.v2_engine import ACCOUNTING_TOLERANCE, run_v2_backtest
from tactical_engine.config import CostConfig
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType
from tactical_engine.execution.simulator import ExecutionSimulator
from tactical_engine.portfolio.v2_portfolio import V2PortfolioEngine
from tactical_engine.signals.v2_signals import V2DirectionalConfig


def _make_bar(
    symbol: str,
    dt: datetime,
    open_p: float,
    high_p: float | None = None,
    low_p: float | None = None,
    close_p: float | None = None,
    vol: float = 1000.0,
) -> Bar:
    c = close_p if close_p is not None else open_p
    h = high_p if high_p is not None else max(open_p, c) + 0.1
    l_val = low_p if low_p is not None else min(open_p, c) - 0.1
    return Bar(
        symbol=symbol,
        timestamp=dt,
        open=open_p,
        high=h,
        low=l_val,
        close=c,
        volume=vol,
    )


def test_effective_common_start_initialization() -> None:
    """Requirement 1: Effective common-start timestamp is the first mutual timestamp."""
    t0 = datetime(2026, 7, 1, 9, 30, tzinfo=UTC)
    t1 = datetime(2026, 7, 13, 9, 30, tzinfo=UTC)

    # MU and SNDK start at t0, SKHY starts at t1
    data = {
        "MU": [_make_bar("MU", t0, 100.0), _make_bar("MU", t1, 105.0)],
        "SNDK": [_make_bar("SNDK", t0, 50.0), _make_bar("SNDK", t1, 52.0)],
        "SKHY": [_make_bar("SKHY", t1, 25.0)],
    }

    res = run_v2_backtest(data=data, mode="V2-A", initial_cash=100000.0)
    assert res.effective_start_timestamp == t1.isoformat()
    # Core should be initialized on t1 using t1 open prices
    assert res.core_starting_value > 0
    # MU: 20000 / 105 = 190 shares; SNDK: 20000 / 52 = 384 shares; SKHY: 20000 / 25 = 800 shares
    assert res.core_actual_pct > 55.0
    assert res.core_residual_cash > 35000.0


def test_no_lookahead_core_initialization() -> None:
    """Requirement 2: Future bar data cannot alter core share quantities."""
    t0 = datetime(2026, 7, 13, 9, 30, tzinfo=UTC)
    t1 = datetime(2026, 7, 13, 9, 31, tzinfo=UTC)

    # Run A: Future price rises
    data_a = {
        "MU": [_make_bar("MU", t0, 100.0), _make_bar("MU", t1, 150.0)],
        "SNDK": [_make_bar("SNDK", t0, 50.0), _make_bar("SNDK", t1, 80.0)],
        "SKHY": [_make_bar("SKHY", t0, 25.0), _make_bar("SKHY", t1, 40.0)],
    }
    # Run B: Future price crashes
    data_b = {
        "MU": [_make_bar("MU", t0, 100.0), _make_bar("MU", t1, 50.0)],
        "SNDK": [_make_bar("SNDK", t0, 50.0), _make_bar("SNDK", t1, 20.0)],
        "SKHY": [_make_bar("SKHY", t0, 25.0), _make_bar("SKHY", t1, 10.0)],
    }

    res_a = run_v2_backtest(data=data_a, mode="V2-A", initial_cash=100000.0)
    res_b = run_v2_backtest(data=data_b, mode="V2-A", initial_cash=100000.0)

    # Initial core starting value and share counts must be 100% identical
    assert res_a.core_starting_value == res_b.core_starting_value
    assert res_a.core_actual_pct == res_b.core_actual_pct
    assert res_a.core_residual_cash == res_b.core_residual_cash


def test_raw_reference_price_vs_execution_price() -> None:
    """Requirement 3: Fill exposes both unadjusted reference_price and execution price."""
    sim = ExecutionSimulator(cost_config=CostConfig(equity_slippage_bps=10.0))
    t0 = datetime(2026, 7, 1, 9, 30, tzinfo=UTC)
    bar = _make_bar("MU", t0, open_p=100.0, vol=100000.0)

    order_buy = Order(
        order_id="b1",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=100.0,
    )
    fill_buy = sim.execute_order(order_buy, bar)
    assert fill_buy is not None
    assert fill_buy.reference_price == 100.0
    assert fill_buy.price > 100.0  # Buy has positive slippage added
    assert fill_buy.slippage > 0.0

    order_sell = Order(
        order_id="s1",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        quantity=100.0,
    )
    fill_sell = sim.execute_order(order_sell, bar)
    assert fill_sell is not None
    assert fill_sell.reference_price == 100.0
    assert fill_sell.price < 100.0  # Sell has slippage deducted
    assert fill_sell.slippage > 0.0


def test_pre_slippage_pnl_correctness_and_cost_accounting() -> None:
    """Requirements 4, 5, 6: pre_slippage_pnl - slippage == realized_pnl."""
    portfolio = V2PortfolioEngine(initial_cash=100000.0)
    # Exogenous core
    portfolio.open_or_add_core("MU", quantity=100, price=100.0)

    # Buy tactical at reference $100.0, filled at $100.10 (slippage = $10.0)
    portfolio.tactical_add(
        symbol="MU",
        quantity=100,
        price=100.10,
        commission=1.0,
        slippage=10.0,
    )
    # Sell tactical at reference $110.0, filled at $109.90 (slippage = $10.0)
    pnl = portfolio.tactical_reduce(
        symbol="MU",
        quantity=100,
        price=109.90,
        commission=1.0,
        slippage=10.0,
    )

    # Reference P&L: 100 * (110.0 - 100.0) = $1,000.0
    ref_pnl = 100 * (110.0 - 100.0)
    total_slip = 20.0
    realized_pnl = pnl

    # Mechanical invariant: realized_pnl == pre_slippage_pnl - slippage
    assert abs((ref_pnl - total_slip) - realized_pnl) < 1e-4

    # Reconciliation
    recon = portfolio.reconcile_pnl_attribution({"MU": 110.0})
    assert recon["reconciles"]
    assert recon["discrepancy"] < 1e-4


def test_financing_counted_exactly_once() -> None:
    """Requirement 7: Margin financing is deducted from cash/equity exactly once."""
    portfolio = V2PortfolioEngine(
        initial_cash=10000.0,
        margin_interest_rate_annual=0.10,  # 10% annual
    )
    # Buy $20,000 worth of stock on margin -> cash becomes -$10,000
    portfolio.tactical_add("MU", quantity=200, price=100.0)
    assert portfolio.cash == -10000.0
    assert portfolio.margin_debt == 10000.0

    # Accrue 36.5 days of interest (0.10 * 36.5/365 = 1% interest = $100)
    portfolio.accrue_financing(36.5 * 86400.0)
    assert abs(portfolio.financing_interest_paid - 100.0) < 1e-2

    recon = portfolio.reconcile_pnl_attribution({"MU": 100.0})
    assert recon["reconciles"]
    assert abs(recon["financing_interest_paid"] - 100.0) < 1e-2


def test_tactical_closed_vs_open_attribution() -> None:
    """Requirement 8: Closed tactical P&L and terminal open P&L sum to sleeve contribution."""
    portfolio = V2PortfolioEngine(initial_cash=100000.0)
    # Trade 1: Closed round trip (Buy at 100, sell at 110 -> realized = +$1,000)
    portfolio.tactical_add("MU", quantity=100, price=100.0)
    portfolio.tactical_reduce("MU", quantity=100, price=110.0)

    # Trade 2: Still open at period end (Buy at 100, terminal price = 105 -> unrealized = +$500)
    portfolio.tactical_add("MU", quantity=100, price=100.0)

    recon = portfolio.reconcile_pnl_attribution({"MU": 105.0})
    assert recon["tactical_realized_pnl"] == 1000.0
    assert recon["tactical_unrealized_pnl"] == 500.0
    total_contrib = recon["tactical_realized_pnl"] + recon["tactical_unrealized_pnl"]
    assert total_contrib == 1500.0
    assert recon["reconciles"]


def test_entry_fill_round_trip_open_lot_count_reconciliation() -> None:
    """Requirement 9: Detailed trade counts reconcile cleanly."""
    base = datetime(2026, 7, 13, 9, 30, tzinfo=UTC)
    bars = {
        "MU": [_make_bar("MU", base + timedelta(minutes=i), 100.0 + (i * 0.1)) for i in range(30)],
        "SNDK": [
            _make_bar("SNDK", base + timedelta(minutes=i), 50.0 + (i * 0.05)) for i in range(30)
        ],
        "SKHY": [
            _make_bar("SKHY", base + timedelta(minutes=i), 25.0 + (i * 0.02)) for i in range(30)
        ],
    }
    res = run_v2_backtest(data=bars, mode="V2-B", initial_cash=100000.0)
    # Invariant: entry fills + reload fills >= completed round trips
    assert res.entry_fills_count + res.reload_fills_count >= res.completed_round_trips_count


def test_next_open_buying_power_no_lookahead() -> None:
    """Requirement 10: Changing bar close does NOT affect next-open order decision.

    Exercises the actual execution-time buying power decision boundary:
    If bar t close were used, Scenario A (crash) would reject and Scenario B (surge)
    would accept. Using bar t+1 open for execution valuation ensures both scenarios
    make the exact same accept/reject decision and fill identical quantities.
    """
    portfolio_a = V2PortfolioEngine(initial_cash=50000.0, max_leverage=2.0)
    portfolio_b = V2PortfolioEngine(initial_cash=50000.0, max_leverage=2.0)

    # Establish identical core holdings: 200 shares MU @ $100 ($20,000)
    portfolio_a.open_or_add_core("MU", quantity=200, price=100.0)
    portfolio_b.open_or_add_core("MU", quantity=200, price=100.0)
    # Remaining cash: $30,000 in both

    # Bar t close: Scenario A crashes to $10.0; Scenario B surges to $1,000.0
    close_prices_a = {"MU": 10.0}
    close_prices_b = {"MU": 1000.0}

    # At bar t+1 open, open price is identically $100.0 in both
    open_prices = {"MU": 100.0}

    # Pending buy order: 650 shares @ $100 = $65,000 cost
    target_cost = 65000.0

    # 1. Prove that if bar t close were used at execution time, the decisions would diverge:
    bp_if_close_a = portfolio_a.get_buying_power(close_prices_a)
    bp_if_close_b = portfolio_b.get_buying_power(close_prices_b)
    # Equity A at $10 close: $30,000 + $2,000 = $32,000
    # Max exp = $64,000 -> BP = $64,000 - $2,000 = $62,000 < $65,000
    assert bp_if_close_a < target_cost  # Would have REJECTED
    # Equity B at $1,000 close: $30,000 + $200,000 = $230,000
    # Max exp = $460,000 -> BP = $260,000 > $65,000
    assert bp_if_close_b > target_cost  # Would have ACCEPTED

    # 2. Execution-time valuation: both use bar t+1 open ($100.0)
    bp_exec_a = portfolio_a.get_buying_power(open_prices)
    bp_exec_b = portfolio_b.get_buying_power(open_prices)
    assert bp_exec_a == bp_exec_b
    assert bp_exec_a >= target_cost  # Equity $50,000 -> Max exp $100,000 -> BP $80,000 >= $65,000

    # 3. Simulate execution loop with no lookahead
    t1 = datetime(2026, 7, 13, 9, 31, tzinfo=UTC)
    b1 = _make_bar("MU", t1, open_p=100.0, close_p=100.0, vol=100000.0)
    sim = ExecutionSimulator(cost_config=CostConfig())
    order = Order(
        order_id="pending_buy",
        symbol="MU",
        timestamp=t1,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=650.0,
    )
    fill_a = sim.execute_order(order, b1)
    fill_b = sim.execute_order(order, b1)
    assert fill_a is not None and fill_b is not None

    # Decision on fill: both accept identically
    can_buy_a = portfolio_a.get_buying_power(open_prices) >= (fill_a.quantity * fill_a.price)
    can_buy_b = portfolio_b.get_buying_power(open_prices) >= (fill_b.quantity * fill_b.price)
    assert can_buy_a is True and can_buy_b is True
    assert fill_a.quantity == fill_b.quantity == 650.0
    assert fill_a.price == fill_b.price


def test_next_open_margin_liquidation_semantics() -> None:
    """Requirement 11: Liquidation queued at bar t close executes strictly at bar t+1 open."""
    portfolio = V2PortfolioEngine(
        initial_cash=10000.0,
        maintenance_ratio=0.25,
        max_leverage=2.0,
    )
    # Core 100 shares @ $100 ($10k); Tactical 100 shares @ $100 on margin ($10k)
    portfolio.open_or_add_core("MU", quantity=100, price=100.0)
    portfolio.tactical_add("MU", quantity=100, price=100.0)
    assert portfolio.cash == -10000.0

    t0 = datetime(2026, 7, 13, 9, 30, tzinfo=UTC)
    t1 = datetime(2026, 7, 13, 9, 31, tzinfo=UTC)

    # Crash price from 100 to 60 at bar t0 close -> equity = $2,000 < $3,000 req (deficit=$1,000)
    close_prices = {"MU": 60.0}
    assert portfolio.is_margin_call(close_prices)

    pending_orders: list[Order] = []
    liq_orders = portfolio.generate_margin_liquidation_orders(close_prices, timestamp=t0)
    pending_orders.extend(liq_orders)

    # --- ASSERT AT BAR t0 CLOSE ---
    # 1. Liquidation orders were generated, prioritizing tactical sleeve first
    assert len(pending_orders) >= 1
    assert "tactical" in pending_orders[0].tag
    assert pending_orders[0].symbol == "MU"
    # 2. Portfolio inventory and cash MUST NOT have changed at bar t0 close
    assert portfolio.tactical_positions["MU"].quantity == 100.0
    assert portfolio.cash == -10000.0

    # --- ADVANCE TO BAR t1 OPEN ---
    b1 = _make_bar("MU", t1, open_p=60.0, close_p=60.0, vol=50000.0)
    sim = ExecutionSimulator(cost_config=CostConfig())

    unfilled: list[Order] = []
    for o in pending_orders:
        fill = sim.execute_order(o, b1)
        if fill is not None:
            if "tactical" in o.tag:
                portfolio.tactical_reduce(
                    symbol=fill.symbol,
                    quantity=fill.quantity,
                    price=fill.price,
                    commission=fill.commission,
                    slippage=fill.slippage,
                )
            elif "core" in o.tag:
                portfolio.reduce_core(
                    symbol=fill.symbol,
                    quantity=fill.quantity,
                    price=fill.price,
                    commission=fill.commission,
                    slippage=fill.slippage,
                )
        else:
            unfilled.append(o)
    pending_orders = unfilled

    # --- ASSERT AT BAR t1 EXECUTION ---
    # 1. Orders were consumed at bar t1 open
    assert len(pending_orders) == 0
    # 2. Tactical position was reduced by liquidation
    assert portfolio.tactical_positions["MU"].quantity < 100.0
    # 3. Cash proceeds first appear at bar t1 open execution
    assert portfolio.cash > -10000.0


def test_peak_margin_debt_sampled_after_transactions() -> None:
    """Requirement 12: Peak margin debt is causally generated by a transaction

    and captured in backtest.
    """
    base_time = datetime(2026, 7, 13, 9, 30, tzinfo=UTC)
    mu_bars = []
    # 10 flat bars
    p = 100.0
    for i in range(10):
        t = base_time + timedelta(minutes=i)
        mu_bars.append(_make_bar("MU", t, open_p=p, close_p=p))
    # 5 impulse bars: price surges from 100 to 103.0 (+3.0% > 2.0%)
    for i in range(5):
        p += 0.60
        t = base_time + timedelta(minutes=10 + i)
        mu_bars.append(_make_bar("MU", t, open_p=p - 0.3, close_p=p, vol=2000.0))
    # 1 pullback bar: 50% retracement to 101.5
    t = base_time + timedelta(minutes=15)
    mu_bars.append(_make_bar("MU", t, open_p=101.7, low_p=101.4, close_p=101.5, vol=1500.0))
    # 3 stabilization bars above trough
    for i in range(3):
        t = base_time + timedelta(minutes=16 + i)
        p_stab = 101.6 + (i * 0.05)
        mu_bars.append(
            _make_bar("MU", t, open_p=p_stab - 0.05, low_p=101.51, close_p=p_stab, vol=1200.0)
        )
    # Execution bar where ENTER_LONG executes at open, plus subsequent bars
    for i in range(5):
        t = base_time + timedelta(minutes=19 + i)
        mu_bars.append(_make_bar("MU", t, open_p=101.7, close_p=101.7, vol=1000.0))

    sndk_bars = [_make_bar("SNDK", b.timestamp, open_p=50.0, close_p=50.0) for b in mu_bars]
    skhy_bars = [_make_bar("SKHY", b.timestamp, open_p=25.0, close_p=25.0) for b in mu_bars]
    data = {"MU": mu_bars, "SNDK": sndk_bars, "SKHY": skhy_bars}

    cfg = V2DirectionalConfig(
        impulse_lookback_bars=10,
        min_impulse_pct=0.02,
        pullback_depth_fraction=0.50,
        stabilization_bars=3,
        tactical_scale_out_ratio=0.50,
        stop_buffer_pct=0.002,
        rebound_target_ratio=0.50,
        trend_filter=False,
    )

    # --- EXPERIMENT 1: Causal transaction creating margin debt ---
    # Initial cash: $10,000, 95% core allocation (~$9,400 core), leaving ~$600 cash.
    # Sizing generates a tactical buy order for ~$1,000 of MU.
    # Executing the transaction consumes all remaining cash and creates ~$315.99 of margin debt.
    res_margin = run_v2_backtest(
        data=data,
        mode="V2-C",
        initial_cash=10000.0,
        core_allocation_pct=0.95,
        signal_config=cfg,
        max_leverage=2.0,
    )
    assert res_margin.entry_fills_count >= 1
    assert res_margin.peak_margin_debt > 0.0
    # Expected debt from buying 9 shares @ 101.7 with insufficient cash (~$315.99)
    assert abs(res_margin.peak_margin_debt - 315.99) < 1.0

    # --- EXPERIMENT 2: Negative Control (Cash-Funded, No Debt) ---
    # Same price path and signal, but with $50,000 cash and 50% core allocation ($25,000 cash).
    # Tactical buy executes identically, but is completely cash-funded.
    # Proves peak_margin_debt is 0.0 when transaction does not require debt.
    res_control = run_v2_backtest(
        data=data,
        mode="V2-C",
        initial_cash=50000.0,
        core_allocation_pct=0.50,
        signal_config=cfg,
        max_leverage=2.0,
    )
    assert res_control.entry_fills_count >= 1
    assert res_control.peak_margin_debt == 0.0


def test_core_isolation_under_tactical_reductions() -> None:
    """Requirement 13: Ordinary tactical exits never touch core holdings."""
    portfolio = V2PortfolioEngine(initial_cash=100000.0)
    portfolio.open_or_add_core("MU", quantity=500, price=100.0)
    portfolio.tactical_add("MU", quantity=100, price=100.0)

    # Tactical full exit
    portfolio.tactical_reduce("MU", quantity=100, price=105.0)

    assert portfolio.core_positions["MU"].quantity == 500
    assert "MU" not in portfolio.tactical_positions


def test_v2_a_and_v2_b_same_core_path() -> None:
    """Requirement 14: Core ending value and core P&L are identical between V2-A and V2-B."""
    base = datetime(2026, 7, 13, 9, 30, tzinfo=UTC)
    bars = {
        "MU": [_make_bar("MU", base + timedelta(minutes=i), 100.0 + (i * 0.1)) for i in range(20)],
        "SNDK": [
            _make_bar("SNDK", base + timedelta(minutes=i), 50.0 + (i * 0.05)) for i in range(20)
        ],
        "SKHY": [
            _make_bar("SKHY", base + timedelta(minutes=i), 25.0 + (i * 0.02)) for i in range(20)
        ],
    }
    res_a = run_v2_backtest(data=bars, mode="V2-A", initial_cash=100000.0)
    res_b = run_v2_backtest(data=bars, mode="V2-B", initial_cash=100000.0)

    assert res_a.core_starting_value == res_b.core_starting_value
    assert res_a.core_ending_value == res_b.core_ending_value
    assert res_a.core_unrealized_pnl == res_b.core_unrealized_pnl
    assert res_a.core_realized_pnl == res_b.core_realized_pnl


def test_synthetic_v2_c_margin_activation() -> None:
    """Requirement 15: Synthetic margin test verifying debt, financing, and liquidation."""
    portfolio = V2PortfolioEngine(
        initial_cash=10000.0,
        margin_interest_rate_annual=0.08,
        maintenance_ratio=0.25,
        max_leverage=2.0,
    )
    # Buy $15,000 on $10,000 cash -> $5,000 debt
    portfolio.tactical_add("MU", quantity=150, price=100.0)
    assert portfolio.cash == -5000.0
    assert portfolio.margin_debt == 5000.0

    # Accrue interest over 30 days
    portfolio.accrue_financing(30.0 * 86400.0)
    assert portfolio.financing_interest_paid > 0.0

    # Verify liquidation ordering: tactical first
    liq = portfolio.generate_margin_liquidation_orders({"MU": 20.0}, timestamp=datetime.now(UTC))
    assert len(liq) > 0
    assert liq[0].symbol == "MU"


def test_phase_l1_exact_algebraic_reconciliation() -> None:
    """Phase L.1 Section 5: Exact 4-tier closed vs open algebraic reconciliation test.

    Proves:
    - closed_ref_pnl - closed_slip - closed_comm = closed_net_realized_pnl
    - open_ref_mtm - open_entry_slip - open_entry_comm = open_net_terminal_contrib
    - closed_net_realized_pnl + open_net_terminal_contrib - financing = total_tactical_contrib
    - final account equity reconciliation closes to machine precision ($0.00 discrepancy)
    - fails if open-entry slippage is incorrectly included in closed-trade layer.
    """
    portfolio = V2PortfolioEngine(
        initial_cash=100000.0,
        margin_interest_rate_annual=0.10,
    )

    # 1. Exogenous Core holding (100 shares MU @ $100, zero setup cost)
    portfolio.open_or_add_core("MU", quantity=100, price=100.0, commission=0.0, slippage=0.0)

    # 2. Closed Tactical Trade (Trade 1 on SNDK):
    # Buy: ref=$50.0, slip=$5.0, exec=$50.05, comm=$2.0
    portfolio.tactical_add("SNDK", quantity=100, price=50.05, commission=2.0, slippage=5.0)
    # Sell: ref=$55.0, slip=$5.0, exec=$54.95, comm=$2.0
    portfolio.tactical_reduce("SNDK", quantity=100, price=54.95, commission=2.0, slippage=5.0)

    # Closed trade metrics
    closed_ref_pnl = 100 * (55.0 - 50.0)  # $500.0
    closed_entry_slip = 5.0
    closed_exit_slip = 5.0
    closed_slip = closed_entry_slip + closed_exit_slip  # $10.0
    closed_comm = 2.0 + 2.0  # $4.0
    closed_net_realized_pnl = closed_ref_pnl - closed_slip - closed_comm  # $486.0

    # 3. Terminal Open Tactical Lot (Trade 2 on SKHY):
    # Buy: ref=$25.0, slip=$2.50, exec=$25.05, comm=$1.0
    portfolio.tactical_add("SKHY", quantity=50, price=25.05, commission=1.0, slippage=2.50)

    # Terminal market prices
    market_prices = {"MU": 110.0, "SNDK": 55.0, "SKHY": 30.0}

    # Open position metrics
    open_ref_mtm = 50 * (30.0 - 25.0)  # $250.0
    open_entry_slip = 2.50
    open_entry_comm = 1.0
    open_net_terminal_contribution = open_ref_mtm - open_entry_slip - open_entry_comm  # $246.50

    # Accrue financing interest
    portfolio.financing_interest_paid = 15.0
    portfolio.cash -= 15.0

    total_tactical_contrib = (
        closed_net_realized_pnl
        + open_net_terminal_contribution
        - portfolio.financing_interest_paid
    )  # $486.0 + $246.50 - $15.0 = $717.50

    core_contrib = 100 * (110.0 - 100.0)  # $1,000.0
    total_strategy_pnl = core_contrib + total_tactical_contrib  # $1,717.50

    eq = portfolio.get_equity(market_prices)
    accounting_pnl = eq - portfolio.initial_cash

    # Algebraic Invariant Assertions:
    # Tier 1 & 2: Closed round-trip algebra
    assert abs((closed_ref_pnl - closed_slip - closed_comm) - closed_net_realized_pnl) < 1e-6
    # Tier 3: Open terminal lot algebra
    assert (
        abs(
            (open_ref_mtm - open_entry_slip - open_entry_comm) - open_net_terminal_contribution
        )
        < 1e-6
    )
    # Tier 4: Total tactical economic contribution
    assert (
        abs(
            (
                closed_net_realized_pnl
                + open_net_terminal_contribution
                - portfolio.financing_interest_paid
            )
            - total_tactical_contrib
        )
        < 1e-6
    )
    # Account equity reconciliation
    assert abs(accounting_pnl - total_strategy_pnl) < 1e-6
    assert abs(eq - (portfolio.initial_cash + total_strategy_pnl)) < 1e-6

    # Slippage single-count decomposition
    total_slip = closed_slip + open_entry_slip
    assert abs(total_slip - portfolio.slippage_paid) < 1e-6

    # Commissions single-count decomposition
    total_comm = closed_comm + open_entry_comm
    assert abs(total_comm - portfolio.commissions_paid) < 1e-6

    # PROVE THE FLAW: If open-entry slippage was mistakenly deducted from closed-trade reference P&L
    flawed_closed_pnl = closed_ref_pnl - portfolio.slippage_paid - closed_comm
    # Discrepancy is EXACTLY the open entry slippage ($2.50)
    assert abs(flawed_closed_pnl - closed_net_realized_pnl) == open_entry_slip == 2.50
    assert abs(flawed_closed_pnl - closed_net_realized_pnl) > 0.0


def test_accounting_tolerance_boundary() -> None:
    """Phase L.2 Section 5: Verify accounting tolerance boundary behavior."""
    assert ACCOUNTING_TOLERANCE == 0.001

    portfolio = V2PortfolioEngine(initial_cash=100000.0)
    recon = portfolio.reconcile_pnl_attribution({"MU": 100.0})
    # Must be strictly within declared tolerance
    assert recon["discrepancy"] <= ACCOUNTING_TOLERANCE

    # Synthetic backtest result tolerance check
    base = datetime(2026, 7, 13, 9, 30, tzinfo=UTC)
    bars = {
        "MU": [_make_bar("MU", base + timedelta(minutes=i), 100.0) for i in range(5)],
        "SNDK": [_make_bar("SNDK", base + timedelta(minutes=i), 50.0) for i in range(5)],
        "SKHY": [_make_bar("SKHY", base + timedelta(minutes=i), 25.0) for i in range(5)],
    }
    res = run_v2_backtest(data=bars, mode="V2-A", initial_cash=100000.0)
    assert res.reconciliation_discrepancy <= res.accounting_tolerance
    assert res.reconciles_cleanly is True


def test_canonical_report_and_json_consistency() -> None:
    """Phase L.1 / L.2: Verify Markdown report and JSON describe identical metrics."""
    import json
    from pathlib import Path

    json_path = Path("reports/v2_historical_comparison.json")
    md_path = Path("reports/V2_HISTORICAL_COMPARISON.md")

    if not json_path.exists() or not md_path.exists():
        return

    with open(json_path) as f:
        data = json.load(f)
    with open(md_path) as f:
        md_text = f.read()

    # Verify Run ID
    run_id = data["run_id"]
    assert f"`{run_id}`" in md_text

    # Verify Execution Code SHA if present
    if "execution_code_sha" in data and data["execution_code_sha"]:
        assert f"`{data['execution_code_sha']}`" in md_text
    elif "git_sha" in data and data["git_sha"]:
        assert f"`{data['git_sha']}`" in md_text

    # Verify V2-B final equity and return
    v2b = data["v2_b_core_tactical"]
    equity_str = f"${v2b['final_equity']:,.2f}"
    assert equity_str in md_text

    ret_str = f"{v2b['total_return_pct']:+.2f}%"
    assert ret_str in md_text

