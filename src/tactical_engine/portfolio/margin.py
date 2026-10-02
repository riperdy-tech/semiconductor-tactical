import uuid
from tactical_engine.data.models import AccountState, Order, OrderSide, OrderType, Position


def calculate_margin_debt(cash: float) -> float:
    return max(0.0, -cash)


def calculate_margin_interest(debt: float, rate_annual: float, elapsed_seconds: float) -> float:
    if debt <= 0 or rate_annual <= 0 or elapsed_seconds <= 0:
        return 0.0
    year_fraction = elapsed_seconds / (365.0 * 86400.0)
    return debt * rate_annual * year_fraction


def calculate_maintenance_requirement(
    positions: dict[str, Position],
    current_prices: dict[str, float],
    maintenance_ratio: float = 0.25,
) -> float:
    total_market_value = 0.0
    for sym, pos in positions.items():
        price = current_prices.get(sym, pos.avg_price)
        total_market_value += abs(pos.quantity * price)
    return total_market_value * maintenance_ratio


def is_margin_call(equity: float, maintenance_requirement: float) -> bool:
    return equity < maintenance_requirement


def generate_forced_liquidation_orders(
    account_state: AccountState,
    current_prices: dict[str, float],
    maintenance_ratio: float = 0.25,
) -> list[Order]:
    """Generates market SELL orders on existing long positions to restore maintenance margin."""
    req = calculate_maintenance_requirement(
        account_state.positions, current_prices, maintenance_ratio
    )
    if not is_margin_call(account_state.equity, req):
        return []

    deficit = req - account_state.equity
    orders: list[Order] = []

    # Sort positions by market value descending to liquidate largest first
    sorted_positions = sorted(
        account_state.positions.items(),
        key=lambda item: abs(item[1].quantity * current_prices.get(item[0], item[1].avg_price)),
        reverse=True,
    )

    remaining_deficit = deficit
    for sym, pos in sorted_positions:
        if pos.quantity <= 0:
            continue
        price = current_prices.get(sym, pos.avg_price)
        pos_value = pos.quantity * price
        # Liquidating $1 of position eliminates $(1 - maintenance_ratio) of deficit
        relief_per_dollar = 1.0 - maintenance_ratio
        dollars_to_liquidate = min(pos_value, remaining_deficit / relief_per_dollar)
        shares_to_liquidate = min(pos.quantity, float(int(dollars_to_liquidate / price)) or 1.0)

        orders.append(
            Order(
                order_id=str(uuid.uuid4())[:8],
                symbol=sym,
                timestamp=account_state.timestamp,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=shares_to_liquidate,
                tag=f"forced_liquidation (margin deficit=${deficit:,.2f})",
            )
        )
        remaining_deficit -= shares_to_liquidate * price * relief_per_dollar
        if remaining_deficit <= 0:
            break

    return orders
