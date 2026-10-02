from datetime import UTC, datetime

from tactical_engine.options.chain_provider import HistoricalOptionChainProvider
from tactical_engine.options.contracts import OptionContractType, OptionQuote


def test_option_quote_validation():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    exp = datetime(2026, 1, 16, 21, 0, tzinfo=UTC)
    quote = OptionQuote(
        symbol="MU260116C00105000",
        underlying="MU",
        timestamp=t0,
        contract_type=OptionContractType.CALL,
        strike=105.0,
        expiration=exp,
        bid=2.40,
        ask=2.50,
        underlying_price=101.5,
    )
    assert quote.contract_type == OptionContractType.CALL
    assert quote.mid == 2.45
    assert quote.dte >= 11


def test_chain_provider_lookup():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    exp = datetime(2026, 1, 16, 21, 0, tzinfo=UTC)
    q1 = OptionQuote(
        symbol="MU260116C00105000",
        underlying="MU",
        timestamp=t0,
        contract_type=OptionContractType.CALL,
        strike=105.0,
        expiration=exp,
        bid=2.40,
        ask=2.50,
        underlying_price=101.5,
    )
    provider = HistoricalOptionChainProvider(quotes=[q1])
    chain = provider.get_chain(underlying="MU", timestamp=t0)
    assert len(chain) == 1
    assert chain[0].symbol == "MU260116C00105000"
