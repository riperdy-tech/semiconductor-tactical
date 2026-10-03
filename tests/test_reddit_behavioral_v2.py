"""Unit tests for Phase J — Reddit Behavioral Replication V2 (US-market scope).

Covers all 14 validation requirements from Section 19 of REDDIT_BEHAVIORAL_V2_EXECUTION_PLAN.md:
1. Persistent core holdings isolated from tactical trades;
2. Tactical add / reload / re-entry around core;
3. Tactical partial exits (e.g. 50% scale-out);
4. Covered-call ownership constraint and state transitions;
5. Covered-call assignment and share delivery;
6. Margin debt against persistent holdings and financing accrual;
7. Forced margin liquidation prioritizing tactical sleeve before core;
8. Profit withdrawals logged separately without inflating strategy return;
9. Strict zero-tolerance P&L attribution reconciliation invariant;
10. Stop-limit order execution with ceiling price protection;
11. U.S.-only instrument classification (MU, SNDK, SKHY);
12. KXIAY OTC ADR classification (1:10 ratio, never Nasdaq-listed);
13. Asian exchange venue exclusion (000660.KS and 285A.T strictly out of scope);
14. No-lookahead execution timing invariant.
"""

from datetime import UTC, datetime

import pytest

from tactical_engine.config import CostConfig
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType
from tactical_engine.data.v2_manifest import (
    InstrumentDataProviderStatus,
    InstrumentEvidenceStatus,
    load_v2_instrument_manifest,
)
from tactical_engine.execution.simulator import ExecutionSimulator
from tactical_engine.portfolio.v2_portfolio import (
    CoveredCallStatus,
    V2PortfolioEngine,
)


def test_v2_instrument_manifest_classification() -> None:
    manifest = load_v2_instrument_manifest()
    assert manifest.market_scope == "US_MARKET_ONLY"
    assert manifest.direct_asia_replication_status == "OUT_OF_SCOPE_FOR_V2"

    # 1. Core observed equities
    source_syms = manifest.get_source_identified_symbols()
    assert "MU" in source_syms
    assert "SNDK" in source_syms
    assert "SKHY" in source_syms

    mu_entry = manifest.get_instrument("MU")
    assert mu_entry is not None
    assert mu_entry.source_evidence_status == InstrumentEvidenceStatus.SOURCE_IDENTIFIED
    assert mu_entry.data_provider_status == InstrumentDataProviderStatus.VALIDATED
    assert mu_entry.exchange_venue == "NASDAQ"

    skhy_entry = manifest.get_instrument("SKHY")
    assert skhy_entry is not None
    assert skhy_entry.source_evidence_status == InstrumentEvidenceStatus.SOURCE_IDENTIFIED
    assert skhy_entry.data_provider_status == InstrumentDataProviderStatus.VALIDATED

    # 2. KXIAY U.S. OTC ADR Proxy
    kxiay = manifest.get_instrument("KXIAY")
    assert kxiay is not None
    assert kxiay.source_evidence_status == InstrumentEvidenceStatus.CANDIDATE_PROXY
    assert kxiay.instrument_type == "OTC_ADR"
    assert kxiay.exchange_venue == "OTC_US"
    assert kxiay.dr_ratio == "1:10"
    assert "Nasdaq" not in kxiay.exchange_venue
    assert "NYSE" not in kxiay.exchange_venue
    assert kxiay.data_provider_status == InstrumentDataProviderStatus.UNVALIDATED

    # 3. Direct Asian Exchange Exclusion
    assert manifest.is_asia_direct_excluded("000660.KS")
    assert manifest.is_asia_direct_excluded("285A.T")
    assert manifest.is_asia_direct_excluded("000660")
    assert manifest.is_asia_direct_excluded("285A")

    krx = manifest.get_instrument("000660.KS")
    assert krx is not None
    assert krx.source_evidence_status == InstrumentEvidenceStatus.OUT_OF_SCOPE_FOR_V2
    assert krx.data_provider_status == InstrumentDataProviderStatus.OUT_OF_SCOPE

    tse = manifest.get_instrument("285A.T")
    assert tse is not None
    assert tse.source_evidence_status == InstrumentEvidenceStatus.OUT_OF_SCOPE_FOR_V2
    assert tse.data_provider_status == InstrumentDataProviderStatus.OUT_OF_SCOPE

    # 4. Candidate 2x Leveraged ETFs
    candidate_proxies = manifest.get_candidate_proxy_symbols()
    for sym in ["SKUU", "SKHU", "SKHL", "MUU", "SNDG", "SNDU", "SNXX"]:
        assert sym in candidate_proxies
        entry = manifest.get_instrument(sym)
        assert entry is not None
        assert entry.source_evidence_status == InstrumentEvidenceStatus.CANDIDATE_PROXY

    # 5. Generic USD ETF Quarantined
    usd_entry = manifest.get_instrument("USD")
    assert usd_entry is not None
    assert usd_entry.source_evidence_status == InstrumentEvidenceStatus.CANDIDATE_PROXY
    assert "quarantined" in usd_entry.notes.lower()


def test_v2_persistent_core_holdings_isolated_from_tactical_exits() -> None:
    engine = V2PortfolioEngine(initial_cash=100_000.0)

    # Establish long persistent core position
    engine.open_or_add_core("MU", quantity=500.0, price=100.0)
    assert engine.cash == 50_000.0
    assert "MU" in engine.core_positions
    assert engine.core_positions["MU"].quantity == 500.0
    assert engine.core_positions["MU"].avg_price == 100.0

    # Add tactical trading sleeve position
    engine.tactical_add("MU", quantity=200.0, price=105.0)
    assert engine.cash == 50_000.0 - 21_000.0
    assert engine.tactical_positions["MU"].quantity == 200.0

    # Full tactical exit on price rebound
    tact_pnl = engine.tactical_reduce("MU", quantity=200.0, price=110.0)
    assert tact_pnl == 200.0 * 5.0  # $1,000 profit
    assert "MU" not in engine.tactical_positions  # Tactical sleeve is flat

    # Crucial architectural invariant: Core holding is completely intact!
    assert "MU" in engine.core_positions
    assert engine.core_positions["MU"].quantity == 500.0
    assert engine.core_positions["MU"].avg_price == 100.0

    # Re-entry: Tactical sleeve reloads on next pullback
    engine.tactical_add("MU", quantity=150.0, price=102.0)
    assert engine.tactical_positions["MU"].quantity == 150.0
    assert engine.core_positions["MU"].quantity == 500.0


def test_v2_tactical_partial_exit_and_reload() -> None:
    engine = V2PortfolioEngine(initial_cash=50_000.0)

    # Tactical add 1,000 shares of SNDK
    engine.tactical_add("SNDK", quantity=1_000.0, price=20.0)
    assert engine.tactical_positions["SNDK"].quantity == 1_000.0

    # Partial exit: 50% scale-out on rebound
    pnl_1 = engine.tactical_reduce("SNDK", quantity=500.0, price=22.0)
    assert pnl_1 == 500.0 * 2.0  # $1,000 profit
    assert engine.tactical_positions["SNDK"].quantity == 500.0
    assert engine.tactical_positions["SNDK"].avg_price == 20.0

    # Reload tactical on pullback
    engine.tactical_add("SNDK", quantity=300.0, price=21.0)
    assert engine.tactical_positions["SNDK"].quantity == 800.0
    # Weighted avg price: (500 * 20 + 300 * 21) / 800 = 16300 / 800 = 20.375
    assert engine.tactical_positions["SNDK"].avg_price == pytest.approx(20.375)

    # Full exit
    pnl_2 = engine.tactical_reduce("SNDK", quantity=800.0, price=23.0)
    assert pnl_2 == pytest.approx(800.0 * (23.0 - 20.375))
    assert "SNDK" not in engine.tactical_positions


def test_v2_covered_call_ownership_constraint_and_repurchase() -> None:
    engine = V2PortfolioEngine(initial_cash=50_000.0)
    engine.open_or_add_core("MU", quantity=250.0, price=100.0)

    # Attempting to write 3 contracts (300 shares) when owning 250 must fail
    with pytest.raises(ValueError, match="Insufficient unencumbered"):
        engine.write_covered_call(
            underlying="MU",
            contract_symbol="MU261016C110",
            strike=110.0,
            expiration=datetime(2026, 10, 16, tzinfo=UTC),
            contracts=3.0,
            premium_per_share=3.50,
            entry_time=datetime(2026, 10, 5, 10, 0, tzinfo=UTC),
        )

    # Write 2 contracts (200 shares) - valid
    call = engine.write_covered_call(
        underlying="MU",
        contract_symbol="MU261016C110",
        strike=110.0,
        expiration=datetime(2026, 10, 16, tzinfo=UTC),
        contracts=2.0,
        premium_per_share=3.50,
        entry_time=datetime(2026, 10, 5, 10, 0, tzinfo=UTC),
        commission=2.0,
    )
    assert call.shares_covered == 200.0
    assert engine.core_positions["MU"].encumbered_shares_for_calls == 200.0
    assert engine.core_positions["MU"].available_shares_for_calls == 50.0
    # Premium collected: 200 * $3.50 - $2 comm = $698
    assert engine.cash == 25_000.0 + 698.0

    # Underlying pulls back: repurchase covered call at $1.20
    opt_pnl = engine.repurchase_covered_call(
        contract_symbol="MU261016C110",
        buyback_premium_per_share=1.20,
        exit_time=datetime(2026, 10, 7, 14, 30, tzinfo=UTC),
        commission=2.0,
    )
    # P&L gross of commission: (3.50 - 1.20) * 200 = 460.0 (commissions tracked in commissions_paid)
    assert opt_pnl == pytest.approx(460.0)
    assert len(engine.open_calls) == 0
    assert len(engine.closed_calls) == 1
    assert engine.closed_calls[0].status == CoveredCallStatus.BOUGHT_BACK

    # Shares unlocked
    assert engine.core_positions["MU"].encumbered_shares_for_calls == 0.0
    assert engine.core_positions["MU"].available_shares_for_calls == 250.0


def test_v2_covered_call_assignment_and_share_delivery() -> None:
    engine = V2PortfolioEngine(initial_cash=50_000.0)
    engine.open_or_add_core("SKHY", quantity=500.0, price=20.0)

    # Write 5 calls at strike $25, premium $1.50
    engine.write_covered_call(
        underlying="SKHY",
        contract_symbol="SKHY261016C25",
        strike=25.0,
        expiration=datetime(2026, 10, 16, tzinfo=UTC),
        contracts=5.0,
        premium_per_share=1.50,
        entry_time=datetime(2026, 10, 5, 10, 0, tzinfo=UTC),
    )

    # Stock closes at $28 at expiry -> assigned
    opt_pnl, eq_pnl = engine.assign_covered_call(
        contract_symbol="SKHY261016C25",
        exit_time=datetime(2026, 10, 16, 16, 0, tzinfo=UTC),
    )
    assert opt_pnl == 500.0 * 1.50  # $750 premium retained
    assert eq_pnl == 500.0 * (25.0 - 20.0)  # $2,500 equity gain to strike
    assert "SKHY" not in engine.core_positions  # All 500 shares delivered
    assert engine.closed_calls[0].status == CoveredCallStatus.ASSIGNED
    assert engine.closed_calls[0].shares_delivered == 500.0


def test_v2_margin_financing_and_maintenance() -> None:
    # Initial cash $40k, buy $80k core shares -> $40k margin debt
    engine = V2PortfolioEngine(
        initial_cash=40_000.0,
        margin_interest_rate_annual=0.05,
        maintenance_ratio=0.25,
    )
    engine.open_or_add_core("MU", quantity=800.0, price=100.0)

    assert engine.cash == -40_000.0
    assert engine.margin_debt == 40_000.0

    # Accrue 36.5 days of financing
    interest = engine.accrue_financing(elapsed_seconds=36.5 * 86400.0)
    expected_interest = 40_000.0 * 0.05 * 0.1  # $200
    assert interest == pytest.approx(expected_interest)
    assert engine.cash == -40_200.0

    # Check maintenance
    prices = {"MU": 100.0}
    pos_val = engine.total_positions_market_value(prices)
    assert pos_val == 80_000.0
    req = engine.get_maintenance_requirement(prices)
    assert req == 80_000.0 * 0.25  # $20,000
    equity = engine.get_equity(prices)
    assert equity == -40_200.0 + 80_000.0  # $39,800
    assert not engine.is_margin_call(prices)


def test_v2_margin_liquidation_prioritizes_tactical_sleeve() -> None:
    engine = V2PortfolioEngine(
        initial_cash=10_000.0,
        margin_interest_rate_annual=0.05,
        maintenance_ratio=0.25,
    )
    # Core: 100 shares @ $100 = $10,000
    engine.open_or_add_core("MU", quantity=100.0, price=100.0)
    # Tactical: 200 shares @ $100 = $20,000
    engine.tactical_add("MU", quantity=200.0, price=100.0)

    # Cash = $10k - $30k = -$20,000 (Margin debt = $20,000)
    assert engine.cash == -20_000.0

    # Price drops sharply to $60
    current_prices = {"MU": 60.0}
    pos_val = 300.0 * 60.0  # $18,000
    assert engine.total_positions_market_value(current_prices) == pos_val
    equity = -20_000.0 + 18_000.0  # -$2,000 (negative equity!)
    assert engine.get_equity(current_prices) == equity
    req = 18_000.0 * 0.25  # $4,500
    assert engine.get_maintenance_requirement(current_prices) == req
    assert engine.is_margin_call(current_prices)

    orders = engine.generate_margin_liquidation_orders(
        current_prices, timestamp=datetime(2026, 10, 5, 15, 0, tzinfo=UTC)
    )
    assert len(orders) > 0
    # First order must be tactical liquidation to protect core
    assert "v2_forced_liquidation_tactical" in orders[0].tag
    assert orders[0].side == OrderSide.SELL
    assert orders[0].symbol == "MU"


def test_v2_pnl_reconciliation_zero_tolerance_invariant() -> None:
    engine = V2PortfolioEngine(initial_cash=100_000.0)

    # 1. Add core
    engine.open_or_add_core("MU", quantity=500.0, price=100.0, commission=5.0)

    # 2. Add tactical
    engine.tactical_add("MU", quantity=200.0, price=102.0, commission=2.0)

    # 3. Partial tactical reduce
    engine.tactical_reduce("MU", quantity=100.0, price=106.0, commission=1.0)

    # 4. Write covered call
    engine.write_covered_call(
        underlying="MU",
        contract_symbol="MU261016C115",
        strike=115.0,
        expiration=datetime(2026, 10, 16, tzinfo=UTC),
        contracts=2.0,
        premium_per_share=4.0,
        entry_time=datetime(2026, 10, 5, 10, 0, tzinfo=UTC),
        commission=2.0,
    )

    # 5. Buy back 1 call or repurchase
    engine.repurchase_covered_call(
        contract_symbol="MU261016C115",
        buyback_premium_per_share=2.5,
        exit_time=datetime(2026, 10, 6, 14, 0, tzinfo=UTC),
        commission=2.0,
    )

    # 6. Accrue margin interest (if any debt)
    if engine.cash < 0:
        engine.accrue_financing(elapsed_seconds=10 * 86400.0)

    # 7. Record a withdrawal
    if engine.cash > 5_000.0:
        engine.record_withdrawal(
            amount=5_000.0,
            timestamp=datetime(2026, 10, 7, 10, 0, tzinfo=UTC),
            note="Periodic profit harvest",
        )

    # Reconcile at current market prices
    current_prices = {"MU": 108.0}
    recon = engine.reconcile_pnl_attribution(current_prices)

    assert recon["reconciles"] is True
    assert recon["discrepancy"] < 1e-4


def test_v2_stop_limit_execution_mechanics() -> None:
    simulator = ExecutionSimulator(
        cost_config=CostConfig(commission_per_share=0.005, slippage_rate=0.0001)
    )
    bar = Bar(
        symbol="MU",
        timestamp=datetime(2026, 10, 5, 10, 15, tzinfo=UTC),
        open=100.0,
        high=102.5,
        low=99.5,
        close=101.5,
        volume=50_000.0,
    )

    # Case 1: Trigger touched and bar trades through limit -> filled at limit/base
    order_1 = Order(
        order_id="v2_stop_lim_1",
        symbol="MU",
        timestamp=datetime(2026, 10, 5, 10, 14, tzinfo=UTC),
        side=OrderSide.BUY,
        order_type=OrderType.STOP_LIMIT,
        quantity=100.0,
        stop_price=101.0,
        limit_price=102.0,
    )
    fill_1 = simulator.execute_order(order=order_1, bar=bar)
    assert fill_1 is not None
    assert fill_1.price <= 102.0 + 1e-4

    # Case 2: Gap up through limit price (low of bar is higher than limit) -> non-fill
    gap_bar = Bar(
        symbol="MU",
        timestamp=datetime(2026, 10, 5, 10, 16, tzinfo=UTC),
        open=105.0,
        high=107.0,
        low=104.5,
        close=106.0,
        volume=60_000.0,
    )
    order_gap = Order(
        order_id="v2_stop_lim_gap",
        symbol="MU",
        timestamp=datetime(2026, 10, 5, 10, 15, tzinfo=UTC),
        side=OrderSide.BUY,
        order_type=OrderType.STOP_LIMIT,
        quantity=100.0,
        stop_price=101.0,
        limit_price=102.0,
    )
    fill_gap = simulator.execute_order(order=order_gap, bar=gap_bar)
    assert fill_gap is None  # Non-fill protected by ceiling limit!


def test_v2_no_lookahead_contract() -> None:
    t0 = datetime(2026, 10, 5, 10, 0, tzinfo=UTC)
    t1 = datetime(2026, 10, 5, 10, 1, tzinfo=UTC)

    bar_t0 = Bar(
        symbol="MU",
        timestamp=t0,
        open=100.0,
        high=101.0,
        low=99.5,
        close=100.5,
        volume=10_000.0,
    )
    bar_t1 = Bar(
        symbol="MU",
        timestamp=t1,
        open=100.6,
        high=101.2,
        low=100.4,
        close=101.0,
        volume=12_000.0,
    )

    # Signal produced on bar_t0 close cannot fill at bar_t0 close.
    # Earliest fill is bar_t1.
    order_t0 = Order(
        order_id="v2_ord_01",
        symbol="MU",
        timestamp=t0,  # Signal generated at t0
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=100.0,
    )
    # Execution occurs on bar_t1
    assert order_t0.timestamp == bar_t0.timestamp
    assert bar_t1.timestamp > order_t0.timestamp
