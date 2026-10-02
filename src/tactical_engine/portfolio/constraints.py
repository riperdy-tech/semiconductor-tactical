from tactical_engine.config import PortfolioConfig
from tactical_engine.data.models import AccountState


def check_portfolio_constraints(
    account_state: AccountState,
    additional_gross_exposure: float,
    config: PortfolioConfig,
) -> bool:
    current_gross = sum(
        pos.quantity * pos.avg_price for pos in account_state.positions.values()
    )
    new_gross = current_gross + additional_gross_exposure
    if account_state.equity <= 0:
        return False
    leverage = new_gross / account_state.equity
    return leverage <= config.max_gross_leverage
