from tactical_engine.config import OptionConfig
from tactical_engine.options.contracts import OptionPosition, OptionQuote


def should_repurchase_covered_call(
    call_position: OptionPosition,
    current_call_quote: OptionQuote | None,
    current_underlying_price: float,
    underlying_price_at_entry: float,
    config: OptionConfig,
) -> tuple[bool, str, float]:
    """Evaluates whether an open covered call should be repurchased before expiration.

    Returns:
        (should_repurchase, reason, repurchase_price)
    """
    if config.repurchase_rule == "expiration":
        return False, "", 0.0

    current_ask = current_call_quote.ask if current_call_quote else None

    # 1. Profit-based repurchase: buy back when premium decays by profit_target_pct (default 50%)
    if config.repurchase_rule == "profit" and current_ask is not None:
        target_buyback_price = call_position.avg_price * 0.50
        if current_ask <= target_buyback_price:
            return True, "profit_target_50pct", current_ask

    # 2. Pullback repurchase: buy back call when underlying pulls back below entry price
    if config.repurchase_rule == "pullback":
        pullback_threshold = 0.02
        if current_underlying_price <= underlying_price_at_entry * (1.0 - pullback_threshold):
            repurchase_p = (
                current_ask
                if current_ask is not None
                else max(0.01, call_position.avg_price * 0.30)
            )
            return True, "underlying_pullback_2pct", repurchase_p

    return False, "", 0.0
