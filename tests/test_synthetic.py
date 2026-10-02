from tactical_engine.data.models import Bar
from tactical_engine.data.synthetic import generate_synthetic_bars


def test_synthetic_bars_reproducibility():
    bars1 = generate_synthetic_bars(symbol="MU", num_bars=100, seed=42)
    bars2 = generate_synthetic_bars(symbol="MU", num_bars=100, seed=42)
    assert len(bars1) == 100
    assert bars1 == bars2
    assert isinstance(bars1[0], Bar)
    assert bars1[0].high >= bars1[0].low
