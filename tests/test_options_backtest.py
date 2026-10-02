from datetime import UTC, datetime, timedelta

from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.options.chain_provider import HistoricalOptionChainProvider
from tactical_engine.options.contracts import OptionContractType, OptionQuote
from tactical_engine.reports.metrics import calculate_metrics


def test_covered_call_backtest_with_historical_chain():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars(symbol="MU", num_bars=60, start_time=t0, seed=42)

    # Build chain provider with quotes matching timestamps
    quotes = []
    exp = t0 + timedelta(days=10)
    for b in bars:
        quotes.append(
            OptionQuote(
                symbol="MU260116C00105000",
                underlying="MU",
                timestamp=b.timestamp,
                contract_type=OptionContractType.CALL,
                strike=105.0,
                expiration=exp,
                bid=2.50,
                ask=2.60,
                underlying_price=b.close,
            )
        )
    chain_provider = HistoricalOptionChainProvider(quotes=quotes)

    cfg = EngineConfig()
    cfg.options.enabled = True
    cfg.options.moneyness = "otm"

    result = run_backtest(
        data={"MU": bars},
        config=cfg,
        option_chain_provider=chain_provider,
    )
    metrics = calculate_metrics(result)

    assert hasattr(result, "options_realized_pnl")
    assert hasattr(result, "options_premium_collected")
    assert hasattr(result, "options_validation_status")
    assert result.options_validation_status == "VALIDATED"
    assert hasattr(metrics, "options_premium_collected")


def test_unvalidated_options_status_when_no_chain():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)
    bars = generate_synthetic_bars(symbol="MU", num_bars=50, start_time=t0, seed=42)
    cfg = EngineConfig()
    cfg.options.enabled = True

    # No chain provider supplied -> MUST flag UNVALIDATED per AGENTS.md rule 5
    result = run_backtest(data={"MU": bars}, config=cfg, option_chain_provider=None)
    assert result.options_validation_status == "UNVALIDATED"
