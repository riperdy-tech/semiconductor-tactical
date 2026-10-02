from tactical_engine.options.contracts import OptionContractType, OptionQuote


def select_covered_call_contract(
    chain: list[OptionQuote],
    underlying_price: float,
    min_dte: int = 1,
    max_dte: int = 14,
    moneyness: str = "otm",
) -> OptionQuote | None:
    calls = [
        q
        for q in chain
        if q.contract_type == OptionContractType.CALL and min_dte <= q.dte <= max_dte and q.bid > 0
    ]
    if not calls:
        return None

    if moneyness == "otm":
        otm_calls = [q for q in calls if q.strike > underlying_price]
        if otm_calls:
            # Pick lowest strike that is still strictly OTM (closest to market)
            return min(otm_calls, key=lambda q: (q.strike, q.dte))
    elif moneyness == "atm":
        return min(calls, key=lambda q: abs(q.strike - underlying_price))
    elif moneyness == "itm":
        itm_calls = [q for q in calls if q.strike < underlying_price]
        if itm_calls:
            return max(itm_calls, key=lambda q: q.strike)

    # Fallback to call closest to underlying price
    return min(calls, key=lambda q: abs(q.strike - underlying_price))
