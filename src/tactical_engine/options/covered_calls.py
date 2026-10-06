from tactical_engine.options.contracts import OptionContractType, OptionQuote


def select_covered_call_contract(
    chain: list[OptionQuote],
    underlying_price: float,
    min_dte: int = 1,
    max_dte: int = 14,
    moneyness: str = "otm",
) -> OptionQuote | None:
    """Select a call using only observable contract and quote fields.

    This helper is deliberately non-Greek. It is suitable for engineering
    fixtures but does not freeze the V2-D headline contract policy.
    """

    calls = [
        q
        for q in chain
        if q.contract_type == OptionContractType.CALL
        and min_dte <= q.dte <= max_dte
        and q.bid > 0
        and q.ask > 0
    ]
    if not calls:
        return None

    if moneyness == "otm":
        otm_calls = [q for q in calls if q.strike > underlying_price]
        if otm_calls:
            return min(otm_calls, key=lambda q: (q.strike, q.expiration, q.symbol))
    elif moneyness == "atm":
        return min(calls, key=lambda q: (abs(q.strike - underlying_price), q.expiration, q.symbol))
    elif moneyness == "itm":
        itm_calls = [q for q in calls if q.strike < underlying_price]
        if itm_calls:
            return max(itm_calls, key=lambda q: (q.strike, -q.dte, q.symbol))

    return min(calls, key=lambda q: (abs(q.strike - underlying_price), q.expiration, q.symbol))
