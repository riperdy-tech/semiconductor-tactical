from tactical_engine.config import PortfolioConfig
from tactical_engine.data.models import AccountState


def calculate_position_size(
    symbol: str,
    price: float,
    stop_price: float | None,
    account_state: AccountState,
    config: PortfolioConfig,
    current_prices: dict[str, float] | None = None,
) -> float:
    if price <= 0:
        return 0.0

    current_equity = max(account_state.equity, 0.0)
    if current_equity <= 0:
        return 0.0

    # 1. Total portfolio gross leverage constraint
    total_current_gross = sum(
        pos.quantity * (current_prices.get(s, pos.avg_price) if current_prices else pos.avg_price)
        for s, pos in account_state.positions.items()
    )
    max_portfolio_gross = current_equity * config.max_gross_leverage
    remaining_gross = max(0.0, max_portfolio_gross - total_current_gross)
    qty_by_leverage = remaining_gross / price

    # 2. Max capital allocated per symbol
    max_symbol_capital = current_equity * config.max_symbol_weight
    existing_pos = account_state.positions.get(symbol, None)
    existing_value = (existing_pos.quantity * price) if existing_pos else 0.0
    remaining_symbol_capital = max(0.0, max_symbol_capital - existing_value)
    qty_by_symbol = remaining_symbol_capital / price

    # 3. Risk-based sizing if stop_price provided
    if stop_price and stop_price < price:
        risk_per_share = price - stop_price
        max_loss_budget = current_equity * (config.risk_per_trade_pct / 100.0)
        qty_by_risk = max_loss_budget / risk_per_share
    else:
        qty_by_risk = float("inf")

    qty = min(qty_by_symbol, qty_by_leverage, qty_by_risk)
    return float(int(qty))  # Whole shares
