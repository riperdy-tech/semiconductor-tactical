from tactical_engine.config import SignalConfig
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.signals.features import compute_bar_features
from tactical_engine.signals.pullback import generate_pullback_signals


def test_pullback_signal_generation():
    bars = generate_synthetic_bars(symbol="MU", num_bars=100, seed=42)
    df = compute_bar_features(bars, trend_window=20)
    cfg = SignalConfig(pullback_zscore=-1.0, trend_window=20)
    signals = generate_pullback_signals(df, cfg)
    assert isinstance(signals, list)
    # With synthetic pullback injected at bar 30, we expect at least one ENTER_LONG intent
    entries = [s for s in signals if s.action == "ENTER_LONG"]
    assert len(entries) > 0
    assert entries[0].symbol == "MU"
