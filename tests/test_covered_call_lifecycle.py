from datetime import UTC, datetime, timedelta

import pytest

from tactical_engine.config import OptionConfig
from tactical_engine.options.contracts import (
    OptionContractType,
    OptionLifecycleState,
    OptionPosition,
    OptionQuote,
)
from tactical_engine.options.lifecycle import CoveredCallLifecycle, validate_covered_share_capacity
from tactical_engine.options.repurchase import should_repurchase_covered_call


def _quote(
    timestamp: datetime,
    *,
    bid: float = 2.00,
    ask: float = 2.20,
    strike: float = 105.0,
) -> OptionQuote:
    return OptionQuote(
        symbol="MU261016C00105000",
        underlying="MU",
        timestamp=timestamp,
        contract_type=OptionContractType.CALL,
        strike=strike,
        expiration=datetime(2026, 10, 16, 20, 0, tzinfo=UTC),
        bid=bid,
        ask=ask,
        underlying_price=100.0,
    )


def test_sell_uses_bid_and_records_sold_to_open_lifecycle():
    t0 = datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
    lifecycle = CoveredCallLifecycle()
    lifecycle, transition = lifecycle.sell(
        _quote(t0), contracts=1, eligible_underlying_shares=100
    )

    assert transition.cash_delta == 200.0
    assert lifecycle.state == OptionLifecycleState.OPEN
    assert lifecycle.history[-2:] == (
        OptionLifecycleState.SOLD,
        OptionLifecycleState.OPEN,
    )
    assert lifecycle.covered_shares == 100.0
    assert lifecycle.entry_premium == 2.0


def test_lifecycle_is_immutable_between_transitions():
    t0 = datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
    lifecycle = CoveredCallLifecycle()
    opened, _ = lifecycle.sell(_quote(t0), contracts=1, eligible_underlying_shares=100)

    assert lifecycle.state == OptionLifecycleState.AVAILABLE
    assert opened.state == OptionLifecycleState.OPEN
    with pytest.raises(ValueError):
        opened.state = OptionLifecycleState.BOUGHT_BACK


def test_overwrite_is_rejected():
    t0 = datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
    lifecycle = CoveredCallLifecycle()

    with pytest.raises(ValueError, match="underlying shares"):
        lifecycle.sell(_quote(t0), contracts=2, eligible_underlying_shares=100)

    validate_covered_share_capacity(
        contracts=1,
        eligible_underlying_shares=100,
    )
    with pytest.raises(ValueError, match="under-covered"):
        validate_covered_share_capacity(
            contracts=2,
            eligible_underlying_shares=100,
        )


def test_buyback_uses_ask_and_reconciles_realized_pnl():
    t0 = datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
    t1 = t0 + timedelta(minutes=2)
    lifecycle = CoveredCallLifecycle()
    lifecycle, _ = lifecycle.sell(
        _quote(t0, bid=2.00, ask=2.20), contracts=1, eligible_underlying_shares=100
    )

    lifecycle, transition = lifecycle.buy_back(_quote(t1, bid=1.00, ask=1.10))
    assert transition.cash_delta == pytest.approx(-110.0)
    assert transition.realized_option_pnl == pytest.approx(90.0)
    assert lifecycle.state == OptionLifecycleState.BOUGHT_BACK
    assert lifecycle.realized_option_pnl == pytest.approx(90.0)


def test_buyback_rejects_future_or_missing_executable_quote():
    t0 = datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
    lifecycle = CoveredCallLifecycle()
    lifecycle, _ = lifecycle.sell(_quote(t0), contracts=1, eligible_underlying_shares=100)

    with pytest.raises(ValueError, match="precede"):
        lifecycle.buy_back(_quote(t0 - timedelta(minutes=1), bid=1.0, ask=1.1))

    with pytest.raises(ValueError, match="positive executable ask"):
        lifecycle.buy_back(_quote(t0 + timedelta(minutes=1), bid=0.0, ask=0.0))


def test_expiration_without_assignment():
    t0 = datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
    expiration = datetime(2026, 10, 16, 20, 0, tzinfo=UTC)
    lifecycle = CoveredCallLifecycle()
    lifecycle, _ = lifecycle.sell(_quote(t0), contracts=1, eligible_underlying_shares=100)

    lifecycle, transition = lifecycle.settle_expiration(
        settlement_time=expiration,
        underlying_close=104.99,
    )
    assert transition.state_after == OptionLifecycleState.EXPIRED
    assert transition.cash_delta == 0.0
    assert transition.shares_delivered == 0.0
    assert lifecycle.realized_option_pnl == pytest.approx(200.0)


def test_expiration_assignment_delivers_only_linked_shares():
    t0 = datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
    expiration = datetime(2026, 10, 16, 20, 0, tzinfo=UTC)
    lifecycle = CoveredCallLifecycle()
    lifecycle, _ = lifecycle.sell(_quote(t0), contracts=1, eligible_underlying_shares=100)

    lifecycle, transition = lifecycle.settle_expiration(
        settlement_time=expiration,
        underlying_close=108.0,
    )
    assert transition.state_after == OptionLifecycleState.ASSIGNED
    assert transition.cash_delta == 10_500.0
    assert transition.shares_delivered == 100.0
    assert lifecycle.realized_option_pnl == pytest.approx(200.0)
    assert lifecycle.to_record().underlying_shares_delivered == 100.0


def test_no_fabricated_pullback_fill_without_option_quote():
    t0 = datetime(2026, 10, 5, 14, 30, tzinfo=UTC)
    position = OptionPosition(
        symbol="MU261016C00105000",
        underlying="MU",
        contract_type=OptionContractType.CALL,
        strike=105.0,
        expiration=datetime(2026, 10, 16, 20, 0, tzinfo=UTC),
        quantity=-1,
        avg_price=2.0,
        associated_underlying_shares=100,
        entry_time=t0,
    )
    should_repurchase, reason, price = should_repurchase_covered_call(
        call_position=position,
        current_call_quote=None,
        current_underlying_price=97.0,
        underlying_price_at_entry=100.0,
        config=OptionConfig(enabled=True, repurchase_rule="pullback"),
    )
    assert should_repurchase is False
    assert reason == "NO_EXECUTABLE_OPTION_QUOTE"
    assert price == 0.0
