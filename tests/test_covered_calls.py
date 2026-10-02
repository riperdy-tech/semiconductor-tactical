from datetime import UTC, datetime, timedelta

from tactical_engine.options.assignment import evaluate_expiration_assignment
from tactical_engine.options.contracts import OptionContractType, OptionPosition, OptionQuote
from tactical_engine.options.covered_calls import select_covered_call_contract


def test_select_covered_call_contract():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    q_otm = OptionQuote(
        symbol="MU260116C00105000",
        underlying="MU",
        timestamp=t0,
        contract_type=OptionContractType.CALL,
        strike=105.0,
        expiration=t0 + timedelta(days=10),
        bid=2.0,
        ask=2.2,
        underlying_price=100.0,
    )
    q_itm = OptionQuote(
        symbol="MU260116C00095000",
        underlying="MU",
        timestamp=t0,
        contract_type=OptionContractType.CALL,
        strike=95.0,
        expiration=t0 + timedelta(days=10),
        bid=6.0,
        ask=6.2,
        underlying_price=100.0,
    )

    selected = select_covered_call_contract(
        chain=[q_otm, q_itm],
        underlying_price=100.0,
        min_dte=5,
        max_dte=14,
        moneyness="otm",
    )
    assert selected is not None
    assert selected.strike == 105.0


def test_evaluate_expiration_assignment():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    exp = t0 + timedelta(days=10)
    pos = OptionPosition(
        symbol="MU260116C00105000",
        underlying="MU",
        contract_type=OptionContractType.CALL,
        strike=105.0,
        expiration=exp,
        quantity=-1.0,  # 1 short call contract
        avg_price=2.0,
        associated_underlying_shares=100.0,
    )

    # Underlying closed at $108 > $105 strike -> ASSIGNED
    assigned, cash, shares = evaluate_expiration_assignment(pos, underlying_close=108.0)
    assert assigned is True
    assert cash == 105.0 * 100.0  # $10,500 received for 100 shares
    assert shares == 100.0

    # Underlying closed at $102 <= $105 strike -> EXPIRED WORTHLESS
    assigned2, cash2, shares2 = evaluate_expiration_assignment(pos, underlying_close=102.0)
    assert assigned2 is False
    assert cash2 == 0.0
    assert shares2 == 0.0
