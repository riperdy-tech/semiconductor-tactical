from datetime import UTC, datetime, timedelta

from tactical_engine.config import OptionConfig
from tactical_engine.options.contracts import (
    OptionContractType,
    OptionPosition,
    OptionQuote,
)
from tactical_engine.options.repurchase import should_repurchase_covered_call


def test_profit_based_repurchase():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t_exp = t0 + timedelta(days=7)

    pos = OptionPosition(
        symbol="MU260112C00105000",
        underlying="MU",
        contract_type=OptionContractType.CALL,
        strike=105.0,
        expiration=t_exp,
        quantity=-1.0,
        avg_price=2.00,  # Sold at $2.00
    )

    quote = OptionQuote(
        symbol="MU260112C00105000",
        underlying="MU",
        timestamp=t0 + timedelta(days=2),
        expiration=t_exp,
        strike=105.0,
        contract_type=OptionContractType.CALL,
        bid=0.90,
        ask=0.95,  # Ask is <= 50% of $2.00 ($1.00)
        underlying_price=101.0,
    )

    cfg = OptionConfig(enabled=True, repurchase_rule="profit")
    should_repurch, reason, repurch_p = should_repurchase_covered_call(
        call_position=pos,
        current_call_quote=quote,
        current_underlying_price=101.0,
        underlying_price_at_entry=100.0,
        config=cfg,
    )
    assert should_repurch is True
    assert reason == "profit_target_50pct"
    assert repurch_p == 0.95


def test_pullback_repurchase():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t_exp = t0 + timedelta(days=7)

    pos = OptionPosition(
        symbol="MU260112C00105000",
        underlying="MU",
        contract_type=OptionContractType.CALL,
        strike=105.0,
        expiration=t_exp,
        quantity=-1.0,
        avg_price=2.00,
    )

    cfg = OptionConfig(enabled=True, repurchase_rule="pullback")
    # Underlying dropped 3% from $100 entry to $97.00
    should_repurch, reason, repurch_p = should_repurchase_covered_call(
        call_position=pos,
        current_call_quote=None,
        current_underlying_price=97.0,
        underlying_price_at_entry=100.0,
        config=cfg,
    )
    assert should_repurch is False
    assert reason == "NO_EXECUTABLE_OPTION_QUOTE"
    assert repurch_p == 0.0


def test_expiration_only_rule_does_not_repurchase_early():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    t_exp = t0 + timedelta(days=7)

    pos = OptionPosition(
        symbol="MU260112C00105000",
        underlying="MU",
        contract_type=OptionContractType.CALL,
        strike=105.0,
        expiration=t_exp,
        quantity=-1.0,
        avg_price=2.00,
    )

    cfg = OptionConfig(enabled=True, repurchase_rule="expiration")
    should_repurch, reason, repurch_p = should_repurchase_covered_call(
        call_position=pos,
        current_call_quote=None,
        current_underlying_price=90.0,
        underlying_price_at_entry=100.0,
        config=cfg,
    )
    assert should_repurch is False
