from tactical_engine.config import PortfolioConfig
from tactical_engine.data.models import AccountState


def calculate_position_size(
    symbol: str,
    price: float,
    stop_price: float | None,
    account_state: AccountState,
    config: PortfolioConfig,
) -> float:
    if price <= 0:
        return 0.0

    current_equity = max(account_state.equity, 0.0)
    if current_equity <= 0:
        return 0.0

    # 1. Max capital allocated per symbol
    max_capital = current_equity * config.max_symbol_weight
    existing_pos = account_state.positions.get(symbol, None)
    existing_value = (existing_pos.quantity * price) if existing_pos else 0.0
    remaining_capital = max(0.0, max_capital - existing_value)

    qty_by_capital = remaining_capital / price

    # 2. Risk-based sizing if stop_price provided
    if stop_price and stop_price < price:
        risk_per_share = price - stop_price
        max_loss_budget = current_equity * (config.risk_per_trade_pct / 100.0)
        qty_by_risk = max_loss_budget / risk_per_share
        qty = min(qty_by_capital, qty_by_risk)
    else:
        qty = qty_by_capital

    return float(int(qty))  # Whole shares
