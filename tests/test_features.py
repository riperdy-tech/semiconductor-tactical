from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.signals.features import compute_bar_features


def test_feature_calculation_shape_and_columns():
    bars = generate_synthetic_bars(symbol="MU", num_bars=100, seed=42)
    df = compute_bar_features(bars, trend_window=20)
    assert len(df) == 100
    expected_cols = ["returns", "atr", "zscore", "vwap_dist", "trend_ok"]
    for col in expected_cols:
        assert col in df.columns
    # Check that early bars handle warmup gracefully
    assert not df["close"].isna().any()
