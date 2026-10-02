from tactical_engine.config import CostConfig
from tactical_engine.data.models import OrderSide


def calculate_fill_price(
    base_price: float,
    side: OrderSide,
    quantity: float,
    bar_volume: float,
    cost_config: CostConfig,
) -> tuple[float, float]:
    # Fixed bps slippage
    slip_rate = cost_config.equity_slippage_bps / 10_000.0
    # Market impact based on participation rate
    impact_rate = 0.0
    if bar_volume > 0:
        participation = quantity / bar_volume
        impact_rate = (participation * 100.0) * (cost_config.market_impact_bps_per_1pct_volume / 10_000.0)

    total_slip = base_price * (slip_rate + impact_rate)
    fill_price = base_price + total_slip if side == OrderSide.BUY else base_price - total_slip
    return round(fill_price, 4), round(total_slip * quantity, 4)
