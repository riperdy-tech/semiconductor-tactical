from tactical_engine.options.contracts import OptionPosition


def evaluate_expiration_assignment(
    position: OptionPosition,
    underlying_close: float,
) -> tuple[bool, float, float]:
    """Evaluates whether a short call is assigned at expiration.

    Returns:
        (is_assigned, cash_proceeds, shares_delivered)
    """
    contracts = abs(position.quantity)
    if contracts <= 0:
        return False, 0.0, 0.0

    # For call options: In-The-Money if underlying_close > strike
    if underlying_close > position.strike:
        shares_to_deliver = contracts * 100.0
        strike_cash = position.strike * shares_to_deliver
        return True, strike_cash, shares_to_deliver

    return False, 0.0, 0.0
