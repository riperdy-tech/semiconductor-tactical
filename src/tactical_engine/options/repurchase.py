from tactical_engine.config import OptionConfig
from tactical_engine.options.contracts import OptionPosition, OptionQuote


def should_repurchase_covered_call(
    call_position: OptionPosition,
    current_call_quote: OptionQuote | None,
    current_underlying_price: float,
    underlying_price_at_entry: float,
    config: OptionConfig,
) -> tuple[bool, str, float]:
    """Return a buyback decision using only executable historical data.

    Missing quotes never fabricate a fill price. A pullback trigger without an
    executable ask is reported as no-fill rather than being converted into a
    theoretical premium.
    """
    if config.repurchase_rule == "expiration":
        return False, "", 0.0

    if current_call_quote is None:
        return False, "NO_EXECUTABLE_OPTION_QUOTE", 0.0

    current_ask = current_call_quote.ask
    if current_ask <= 0:
        return False, "NO_EXECUTABLE_OPTION_QUOTE", 0.0

    if call_position.entry_time is not None and current_call_quote.timestamp < call_position.entry_time:
        return False, "FUTURE_QUOTE_LOOKAHEAD_BLOCKED", 0.0

    if config.repurchase_rule == "profit":
        target_buyback_price = call_position.avg_price * 0.50
        if current_ask <= target_buyback_price:
            return True, "profit_target_50pct", current_ask

    if config.repurchase_rule == "pullback":
        pullback_threshold = 0.02
        if current_underlying_price <= underlying_price_at_entry * (1.0 - pullback_threshold):
            return True, "underlying_pullback_2pct", current_ask

    return False, "", 0.0
