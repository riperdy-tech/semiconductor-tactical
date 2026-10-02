from collections import defaultdict
from tactical_engine.backtest.engine import BacktestResult


def attribute_pnl_by_ticker(result: BacktestResult) -> dict[str, float]:
    pnl_by_sym = defaultdict(float)
    for t in result.trades:
        pnl_by_sym[t.symbol] += t.net_pnl
    return {k: round(v, 2) for k, v in pnl_by_sym.items()}
