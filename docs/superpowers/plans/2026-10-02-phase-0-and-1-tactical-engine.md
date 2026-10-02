# Phase 0 & Phase 1 Tactical Research Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete Phase 0 (Foundation) and Phase 1 (Equity-Only Tactical Backtest Engine) research pipeline with deterministic signals, execution simulation, walk-forward-ready state, and automated reporting.

**Architecture:** A functional, pipeline-oriented backtesting architecture where market data flows through feature engineering -> pure signal predicates -> portfolio sizing & allocation -> execution simulation (slippage, liquidity caps, costs) -> state accounting -> metrics & markdown report generation.

**Tech Stack:** Python 3.12, Pydantic v2, PyYAML, NumPy, Pandas, Pytest, Ruff.

**Spec:** [`docs/STRATEGY_SPEC.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/STRATEGY_SPEC.md), [`docs/BACKTEST_PROTOCOL.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/BACKTEST_PROTOCOL.md), [`docs/DATA_CONTRACT.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/DATA_CONTRACT.md), [`docs/ARCHITECTURE.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/docs/ARCHITECTURE.md), [`AGENTS.md`](file:///c:/Users/riper/Downloads/semiconductor-tactical/AGENTS.md).

## Global Constraints

- Signals at timestamp `t` only use data timestamped <= `t`. Default fill is next eligible bar `t+1`.
- Intrabar ambiguity: conservative execution ordering (stop hit before target if both touched in same bar).
- No look-ahead, survivorship bias, or fictional options fills.
- All code must pass `python -m pytest` and `python -m ruff check .`.
- No LLM in signal paths. Every unsupported threshold labeled as `HYPOTHESIS` or `ASSUMPTION`.

---

### Task 1: Typed Configuration Models & YAML Loader

**Files:**
- Create: `src/tactical_engine/config.py`
- Modify: `src/tactical_engine/__init__.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: `configs/base.yaml`
- Produces: `EngineConfig` Pydantic model, `load_config(path: str | Path) -> EngineConfig`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
from pathlib import Path
import pytest
from tactical_engine.config import EngineConfig, load_config


def test_load_base_config():
    config_path = Path("configs/base.yaml")
    config = load_config(config_path)
    assert isinstance(config, EngineConfig)
    assert config.project.name == "high-beta-tactical"
    assert config.strategy.variant == "risk_controlled"
    assert "MU" in config.strategy.universe
    assert config.signals.pullback_zscore == -1.5
    assert config.exits.family == "atr"
    assert config.portfolio.max_gross_leverage == 1.0
    assert config.costs.equity_slippage_bps == 5.0


def test_config_validation_error(tmp_path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("strategy:\n  variant: unknown_variant\n", encoding="utf-8")
    with pytest.raises(Exception):
        load_config(bad_yaml)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tactical_engine.config'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tactical_engine/config.py
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    name: str = "high-beta-tactical"
    timezone_report: str = "America/New_York"
    random_seed: int = 42


class StrategyConfig(BaseModel):
    variant: Literal["literal_clone", "risk_controlled", "regime_adapted"] = "risk_controlled"
    universe: list[str] = Field(default_factory=lambda: ["MU", "SNDK", "SKHY", "AMD"])
    two_x_etfs: list[str] = Field(default_factory=list)
    bar_interval: str = "1m"


class SignalConfig(BaseModel):
    pullback_zscore: float = -1.5
    trend_window: int = 60
    sector_filter: bool = True
    relative_volume_filter: bool = True
    event_filter: bool = True


class ExitConfig(BaseModel):
    family: Literal["fixed_pct", "atr", "vwap", "time"] = "atr"
    target_pct: float = 0.015
    stop_pct: float = 0.015
    target_atr: float = 1.0
    stop_atr: float = 1.0
    max_hold_minutes: int = 120


class PortfolioConfig(BaseModel):
    initial_cash: float = 100_000.0
    max_symbol_weight: float = 0.25
    max_gross_leverage: float = 1.0
    max_layers: int = 2
    risk_per_trade_pct: float = 0.25


class CostConfig(BaseModel):
    equity_commission_bps: float = 0.0
    equity_slippage_bps: float = 5.0
    option_slippage_bps: float = 10.0
    market_impact_bps_per_1pct_volume: float = 10.0
    margin_rate_annual: float = 0.0


class OptionConfig(BaseModel):
    enabled: bool = False
    max_dte: int = 14
    min_dte: int = 1
    moneyness: Literal["otm", "atm", "itm"] = "otm"
    repurchase_rule: Literal["pullback", "time", "profit"] = "pullback"


class ResearchConfig(BaseModel):
    start: str | None = None
    end: str | None = None
    train_end: str | None = None
    validation_end: str | None = None
    test_start: str | None = None


class OutputConfig(BaseModel):
    root: str = "reports"


class EngineConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    signals: SignalConfig = Field(default_factory=SignalConfig)
    exits: ExitConfig = Field(default_factory=ExitConfig)
    portfolio: PortfolioConfig = Field(default_factory=PortfolioConfig)
    costs: CostConfig = Field(default_factory=CostConfig)
    options: OptionConfig = Field(default_factory=OptionConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    outputs: OutputConfig = Field(default_factory=OutputConfig)


def load_config(path: str | Path) -> EngineConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return EngineConfig.model_validate(data)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tactical_engine/config.py tests/test_config.py
git commit -m "feat(config): add typed EngineConfig and YAML loader"
```

---

### Task 2: Core Data Models & Validation

**Files:**
- Create: `src/tactical_engine/data/models.py`
- Create: `src/tactical_engine/data/validation.py`
- Test: `tests/test_data_models.py`

**Interfaces:**
- Consumes: Standard types, pandas timestamps
- Produces: `Bar`, `Quote`, `SignalIntent`, `Order`, `Fill`, `Position`, `AccountState`, and validation function `validate_bar_sequence(bars: list[Bar]) -> None`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data_models.py
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType, SignalIntent
from tactical_engine.data.validation import validate_bar_sequence


def test_bar_validation_success():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    bar = Bar(
        symbol="MU",
        timestamp=t0,
        open=100.0,
        high=102.0,
        low=99.0,
        close=101.5,
        volume=10000.0,
        vwap=101.0,
    )
    assert bar.high >= bar.low
    assert bar.volume >= 0.0


def test_bar_validation_invalid_high_low():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        Bar(
            symbol="MU",
            timestamp=t0,
            open=100.0,
            high=95.0,  # high < low is invalid
            low=99.0,
            close=97.0,
            volume=100.0,
        )


def test_validate_bar_sequence_order():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 5, 14, 31, tzinfo=timezone.utc)
    b1 = Bar(symbol="MU", timestamp=t1, open=10, high=11, low=9, close=10, volume=10)
    b0 = Bar(symbol="MU", timestamp=t0, open=10, high=11, low=9, close=10, volume=10)
    with pytest.raises(ValueError, match="Monotonic"):
        validate_bar_sequence([b1, b0])  # Non-monotonic
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_data_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tactical_engine.data.models'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tactical_engine/data/models.py
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, model_validator


class Bar(BaseModel, frozen=True):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    vwap: float | None = None

    @model_validator(mode="after")
    def check_ohlc(self) -> "Bar":
        if self.high < self.low:
            raise ValueError(f"high ({self.high}) cannot be less than low ({self.low})")
        if self.open < 0 or self.high < 0 or self.low < 0 or self.close < 0:
            raise ValueError("Prices cannot be negative")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
        if not (self.low <= self.open <= self.high and self.low <= self.close <= self.high):
            raise ValueError("Open and Close must be within High and Low")
        return self


class Quote(BaseModel, frozen=True):
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    bid_size: float = 0.0
    ask_size: float = 0.0


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class SignalIntent(BaseModel, frozen=True):
    symbol: str
    timestamp: datetime
    action: Literal["ENTER_LONG", "EXIT_LONG", "HOLD"] = "HOLD"
    strength: float = 1.0
    reason: str = ""
    stop_price: float | None = None
    target_price: float | None = None


class Order(BaseModel, frozen=True):
    order_id: str
    symbol: str
    timestamp: datetime
    side: OrderSide
    order_type: OrderType
    quantity: float
    limit_price: float | None = None
    stop_price: float | None = None
    tag: str = ""


class Fill(BaseModel, frozen=True):
    order_id: str
    symbol: str
    timestamp: datetime
    side: OrderSide
    quantity: float
    price: float
    commission: float = 0.0
    slippage: float = 0.0


class Position(BaseModel, frozen=True):
    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    realized_pnl: float = 0.0


class AccountState(BaseModel, frozen=True):
    timestamp: datetime
    cash: float
    positions: dict[str, Position] = Field(default_factory=dict)
    margin_debt: float = 0.0
    equity: float = 0.0
```

```python
# src/tactical_engine/data/validation.py
from tactical_engine.data.models import Bar


def validate_bar_sequence(bars: list[Bar]) -> None:
    if not bars:
        return
    for i in range(1, len(bars)):
        if bars[i].timestamp <= bars[i - 1].timestamp:
            raise ValueError(
                f"Monotonic timestamp violation: {bars[i].timestamp} <= {bars[i - 1].timestamp}"
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_data_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tactical_engine/data/models.py src/tactical_engine/data/validation.py tests/test_data_models.py
git commit -m "feat(data): add core models and bar validation gates"
```

---

### Task 3: Run Manifest Generator

**Files:**
- Create: `src/tactical_engine/backtest/manifest.py`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Consumes: `EngineConfig`, commit hash, data fingerprint
- Produces: `RunManifest` model and `create_manifest(...) -> RunManifest`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_manifest.py
from pathlib import Path
from tactical_engine.backtest.manifest import create_manifest
from tactical_engine.config import EngineConfig


def test_create_run_manifest():
    cfg = EngineConfig()
    manifest = create_manifest(config=cfg, data_hashes={"MU": "dummy_hash"})
    assert manifest.run_id is not None
    assert manifest.config_hash is not None
    assert manifest.strategy_variant == "risk_controlled"
    assert manifest.symbols == ["MU", "SNDK", "SKHY", "AMD"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tactical_engine.backtest.manifest'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tactical_engine/backtest/manifest.py
import hashlib
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from tactical_engine.config import EngineConfig


def get_git_commit_hash() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return "unknown"


class RunManifest(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    git_commit: str = Field(default_factory=get_git_commit_hash)
    config_hash: str
    data_hashes: dict[str, str] = Field(default_factory=dict)
    strategy_variant: str
    symbols: list[str]
    timeframe: str
    random_seed: int
    output_artifacts: list[str] = Field(default_factory=list)


def create_manifest(config: EngineConfig, data_hashes: dict[str, str] | None = None) -> RunManifest:
    raw_cfg_str = config.model_dump_json()
    cfg_hash = hashlib.sha256(raw_cfg_str.encode("utf-8")).hexdigest()[:16]
    return RunManifest(
        config_hash=cfg_hash,
        data_hashes=data_hashes or {},
        strategy_variant=config.strategy.variant,
        symbols=config.strategy.universe,
        timeframe=config.strategy.bar_interval,
        random_seed=config.project.random_seed,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_manifest.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tactical_engine/backtest/manifest.py tests/test_manifest.py
git commit -m "feat(backtest): add RunManifest and provenance tracker"
```

---

### Task 4: Deterministic Synthetic Fixture Generator

**Files:**
- Create: `src/tactical_engine/data/synthetic.py`
- Test: `tests/test_synthetic.py`

**Interfaces:**
- Consumes: symbol, num_bars, base_price, seed
- Produces: `generate_synthetic_bars(...) -> list[Bar]` with predictable trend + pullback spikes

- [ ] **Step 1: Write the failing test**

```python
# tests/test_synthetic.py
from tactical_engine.data.models import Bar
from tactical_engine.data.synthetic import generate_synthetic_bars


def test_synthetic_bars_reproducibility():
    bars1 = generate_synthetic_bars(symbol="MU", num_bars=100, seed=42)
    bars2 = generate_synthetic_bars(symbol="MU", num_bars=100, seed=42)
    assert len(bars1) == 100
    assert bars1 == bars2
    assert isinstance(bars1[0], Bar)
    assert bars1[0].high >= bars1[0].low
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_synthetic.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tactical_engine.data.synthetic'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tactical_engine/data/synthetic.py
from datetime import datetime, timedelta, timezone
import numpy as np
from tactical_engine.data.models import Bar


def generate_synthetic_bars(
    symbol: str,
    num_bars: int = 200,
    base_price: float = 100.0,
    seed: int = 42,
    start_time: datetime | None = None,
    interval_minutes: int = 1,
) -> list[Bar]:
    rng = np.random.default_rng(seed)
    if start_time is None:
        start_time = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)

    # Random walk with slight drift and occasional pullbacks
    returns = rng.normal(loc=0.0001, scale=0.002, size=num_bars)
    # Inject deliberate pullback at bar 30 and 80
    if num_bars > 35:
        returns[30:33] = -0.015
    if num_bars > 85:
        returns[80:83] = -0.018

    prices = base_price * np.exp(np.cumsum(returns))
    bars = []
    current_time = start_time

    for i in range(num_bars):
        close_p = float(prices[i])
        open_p = float(prices[i - 1]) if i > 0 else base_price
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.2))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.2))
        vol = float(rng.uniform(5000, 25000))
        vwap_p = (open_p + high_p + low_p + close_p) / 4.0

        bars.append(
            Bar(
                symbol=symbol,
                timestamp=current_time,
                open=round(open_p, 4),
                high=round(high_p, 4),
                low=round(low_p, 4),
                close=round(close_p, 4),
                volume=round(vol, 1),
                vwap=round(vwap_p, 4),
            )
        )
        current_time += timedelta(minutes=interval_minutes)

    return bars
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_synthetic.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tactical_engine/data/synthetic.py tests/test_synthetic.py
git commit -m "feat(data): add deterministic synthetic bar generator fixture"
```

---

### Task 5: Feature Engineering Module

**Files:**
- Create: `src/tactical_engine/signals/features.py`
- Test: `tests/test_features.py`

**Interfaces:**
- Consumes: `list[Bar]`
- Produces: `pd.DataFrame` with returns, rolling ATR, rolling z-score of price/return displacement, VWAP distance, and trend slope.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_features.py
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.signals.features import compute_bar_features


def test_feature_calculation_shape_and_columns():
    bars = generate_synthetic_bars(symbol="MU", num_bars=100, seed=42)
    df = compute_bar_features(bars, trend_window=20)
    assert len(df) == 100
    expected_cols = ["returns", "atr", "zscore", "vwap_dist", "trend_ok"]
    for col in expected_cols:
        assert col in df.columns
    # Check that early bars handle warmup gracefully with NaNs or 0
    assert not df["close"].isna().any()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_features.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tactical_engine.signals.features'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tactical_engine/signals/features.py
import pandas as pd
import numpy as np
from tactical_engine.data.models import Bar


def compute_bar_features(bars: list[Bar], trend_window: int = 60) -> pd.DataFrame:
    if not bars:
        return pd.DataFrame()

    data = [
        {
            "timestamp": b.timestamp,
            "symbol": b.symbol,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
            "vwap": b.vwap or b.close,
        }
        for b in bars
    ]
    df = pd.DataFrame(data).set_index("timestamp").sort_index()

    # Log returns
    df["returns"] = np.log(df["close"] / df["close"].shift(1)).fillna(0.0)

    # True Range & ATR
    prev_close = df["close"].shift(1).fillna(df["open"])
    tr = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            np.abs(df["high"] - prev_close),
            np.abs(df["low"] - prev_close),
        ),
    )
    df["atr"] = tr.rolling(window=14, min_periods=1).mean()

    # Rolling mean & std for displacement z-score (pullback hypothesis)
    rolling_mean = df["close"].rolling(window=trend_window, min_periods=10).mean()
    rolling_std = df["close"].rolling(window=trend_window, min_periods=10).std().replace(0, np.nan)
    df["zscore"] = ((df["close"] - rolling_mean) / rolling_std).fillna(0.0)

    # VWAP distance
    df["vwap_dist"] = (df["close"] - df["vwap"]) / df["vwap"]

    # Trend filter: fast moving average > slow moving average or price above rolling mean
    fast_ma = df["close"].rolling(window=max(5, trend_window // 4), min_periods=1).mean()
    slow_ma = df["close"].rolling(window=trend_window, min_periods=1).mean()
    df["trend_ok"] = fast_ma >= slow_ma

    return df
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_features.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tactical_engine/signals/features.py tests/test_features.py
git commit -m "feat(signals): implement pure bar feature calculations"
```

---

### Task 6: Pullback Signal Generation & Ranking

**Files:**
- Create: `src/tactical_engine/signals/pullback.py`
- Create: `src/tactical_engine/signals/ranking.py`
- Test: `tests/test_signals.py`

**Interfaces:**
- Consumes: `pd.DataFrame` of features, `SignalConfig`
- Produces: `generate_pullback_signals(df: pd.DataFrame, config: SignalConfig) -> list[SignalIntent]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_signals.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_signals.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tactical_engine.signals.pullback'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tactical_engine/signals/pullback.py
import pandas as pd
from tactical_engine.config import SignalConfig
from tactical_engine.data.models import SignalIntent


def generate_pullback_signals(df: pd.DataFrame, config: SignalConfig) -> list[SignalIntent]:
    signals = []
    if df.empty:
        return signals

    symbol = str(df["symbol"].iloc[0])
    for timestamp, row in df.iterrows():
        # Hypothesis: buy when zscore < threshold AND trend_ok is True
        is_pullback = row["zscore"] <= config.pullback_zscore
        trend_intact = row["trend_ok"] if config.sector_filter else True

        if is_pullback and trend_intact:
            signals.append(
                SignalIntent(
                    symbol=symbol,
                    timestamp=timestamp,  # type: ignore
                    action="ENTER_LONG",
                    strength=abs(float(row["zscore"])),
                    reason=f"pullback_zscore={row['zscore']:.2f}",
                )
            )
        else:
            signals.append(
                SignalIntent(
                    symbol=symbol,
                    timestamp=timestamp,  # type: ignore
                    action="HOLD",
                )
            )
    return signals
```

```python
# src/tactical_engine/signals/ranking.py
from tactical_engine.data.models import SignalIntent


def rank_signals_by_strength(signals: list[SignalIntent], top_n: int = 2) -> list[SignalIntent]:
    active = [s for s in signals if s.action == "ENTER_LONG"]
    ranked = sorted(active, key=lambda s: s.strength, reverse=True)
    return ranked[:top_n]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_signals.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tactical_engine/signals/pullback.py src/tactical_engine/signals/ranking.py tests/test_signals.py
git commit -m "feat(signals): implement pullback signal generator and cross-sectional ranker"
```

---

### Task 7: Exit Signal Logic (ATR, Fixed Pct, Time Stop)

**Files:**
- Create: `src/tactical_engine/signals/exits.py`
- Test: `tests/test_exits.py`

**Interfaces:**
- Consumes: Entry price, entry time, current bar, `ExitConfig`
- Produces: `check_exit_condition(...) -> tuple[bool, str]`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_exits.py
from datetime import datetime, timedelta, timezone
from tactical_engine.config import ExitConfig
from tactical_engine.data.models import Bar
from tactical_engine.signals.exits import check_exit_condition


def test_atr_exit_stop_hit():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    cfg = ExitConfig(family="atr", stop_atr=1.0, target_atr=1.5)
    # Entry at 100 with ATR = 2.0 -> stop at 98.0
    bar = Bar(symbol="MU", timestamp=t0, open=99.0, high=99.5, low=97.5, close=98.0, volume=100)
    should_exit, reason = check_exit_condition(
        entry_price=100.0,
        entry_time=t0,
        current_bar=bar,
        atr=2.0,
        config=cfg,
    )
    assert should_exit is True
    assert "stop" in reason


def test_time_exit():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    t1 = t0 + timedelta(minutes=130)
    cfg = ExitConfig(family="time", max_hold_minutes=120)
    bar = Bar(symbol="MU", timestamp=t1, open=100, high=101, low=99, close=100, volume=100)
    should_exit, reason = check_exit_condition(
        entry_price=100.0,
        entry_time=t0,
        current_bar=bar,
        atr=2.0,
        config=cfg,
    )
    assert should_exit is True
    assert "time_stop" in reason
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_exits.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tactical_engine.signals.exits'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tactical_engine/signals/exits.py
from datetime import datetime
from tactical_engine.config import ExitConfig
from tactical_engine.data.models import Bar


def check_exit_condition(
    entry_price: float,
    entry_time: datetime,
    current_bar: Bar,
    atr: float,
    config: ExitConfig,
) -> tuple[bool, str]:
    # 1. Time-based exit check
    hold_duration = (current_bar.timestamp - entry_time).total_seconds() / 60.0
    if hold_duration >= config.max_hold_minutes:
        return True, f"time_stop ({hold_duration:.0f}m >= {config.max_hold_minutes}m)"

    # 2. Price-based targets & stops
    if config.family == "atr":
        stop_price = entry_price - (config.stop_atr * atr)
        target_price = entry_price + (config.target_atr * atr)
    elif config.family == "fixed_pct":
        stop_price = entry_price * (1.0 - config.stop_pct)
        target_price = entry_price * (1.0 + config.target_pct)
    else:
        # Default fallback
        stop_price = entry_price - (1.0 * atr)
        target_price = entry_price + (1.5 * atr)

    # Intrabar ambiguity rule (BACKTEST_PROTOCOL.md §3):
    # If both stop and target touched in the same bar, assume stop hit first (conservative).
    stop_hit = current_bar.low <= stop_price
    target_hit = current_bar.high >= target_price

    if stop_hit and target_hit:
        return True, "stop_loss_hit (conservative intrabar ambiguity resolution)"
    if stop_hit:
        return True, f"stop_loss_hit ({current_bar.low:.2f} <= {stop_price:.2f})"
    if target_hit:
        return True, f"target_hit ({current_bar.high:.2f} >= {target_price:.2f})"

    return False, ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_exits.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tactical_engine/signals/exits.py tests/test_exits.py
git commit -m "feat(signals): implement exit rules with conservative intrabar ambiguity resolution"
```

---

### Task 8: Portfolio Sizing & Constraints

**Files:**
- Create: `src/tactical_engine/portfolio/sizing.py`
- Create: `src/tactical_engine/portfolio/constraints.py`
- Test: `tests/test_portfolio.py`

**Interfaces:**
- Consumes: `AccountState`, target price, stop price, `PortfolioConfig`
- Produces: `calculate_position_size(...) -> float` (quantity of shares)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_portfolio.py
from datetime import datetime, timezone
from tactical_engine.config import PortfolioConfig
from tactical_engine.data.models import AccountState, Position
from tactical_engine.portfolio.sizing import calculate_position_size


def test_position_sizing_respects_max_weight():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    state = AccountState(timestamp=t0, cash=100_000.0, equity=100_000.0)
    cfg = PortfolioConfig(max_symbol_weight=0.25, risk_per_trade_pct=0.25)
    # Price $100 -> max allocation $25,000 -> 250 shares
    qty = calculate_position_size(
        symbol="MU",
        price=100.0,
        stop_price=98.0,
        account_state=state,
        config=cfg,
    )
    assert qty == 250.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_portfolio.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tactical_engine.portfolio.sizing'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tactical_engine/portfolio/sizing.py
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
    existing_qty = account_state.positions.get(symbol, None)
    existing_value = (existing_qty.quantity * price) if existing_qty else 0.0
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
```

```python
# src/tactical_engine/portfolio/constraints.py
from tactical_engine.config import PortfolioConfig
from tactical_engine.data.models import AccountState


def check_portfolio_constraints(
    account_state: AccountState,
    additional_gross_exposure: float,
    config: PortfolioConfig,
) -> bool:
    current_gross = sum(pos.quantity * pos.avg_price for pos in account_state.positions.values())
    new_gross = current_gross + additional_gross_exposure
    if account_state.equity <= 0:
        return False
    leverage = new_gross / account_state.equity
    return leverage <= config.max_gross_leverage
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_portfolio.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tactical_engine/portfolio/sizing.py src/tactical_engine/portfolio/constraints.py tests/test_portfolio.py
git commit -m "feat(portfolio): implement position sizing and leverage constraint checks"
```

---

### Task 9: Execution Simulator & Cost/Slippage Model

**Files:**
- Create: `src/tactical_engine/execution/slippage.py`
- Create: `src/tactical_engine/execution/fills.py`
- Create: `src/tactical_engine/execution/simulator.py`
- Test: `tests/test_execution.py`

**Interfaces:**
- Consumes: `Order`, next `Bar`, `CostConfig`
- Produces: `Fill | None` with explicit slippage and commissions applied.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_execution.py
from datetime import datetime, timezone
from tactical_engine.config import CostConfig
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType
from tactical_engine.execution.simulator import ExecutionSimulator


def test_order_fill_next_bar_open_with_slippage():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 5, 14, 31, tzinfo=timezone.utc)
    order = Order(
        order_id="ord-1",
        symbol="MU",
        timestamp=t0,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=100.0,
    )
    next_bar = Bar(
        symbol="MU", timestamp=t1, open=100.0, high=101.0, low=99.0, close=100.5, volume=50000.0
    )
    cfg = CostConfig(equity_slippage_bps=10.0, equity_commission_bps=0.0)
    sim = ExecutionSimulator(cost_config=cfg)

    fill = sim.execute_order(order, next_bar)
    assert fill is not None
    # 10 bps slippage on $100 buy = +$0.10 -> fill at 100.10
    assert fill.price == 100.10
    assert fill.quantity == 100.0
    assert fill.timestamp == t1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_execution.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tactical_engine.execution.simulator'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tactical_engine/execution/slippage.py
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
        impact_rate = (participation * 100.0) * (
            cost_config.market_impact_bps_per_1pct_volume / 10_000.0
        )

    total_slip = base_price * (slip_rate + impact_rate)
    fill_price = base_price + total_slip if side == OrderSide.BUY else base_price - total_slip
    return round(fill_price, 4), round(total_slip * quantity, 4)
```

```python
# src/tactical_engine/execution/simulator.py
from tactical_engine.config import CostConfig
from tactical_engine.data.models import Bar, Fill, Order, OrderSide, OrderType
from tactical_engine.execution.slippage import calculate_fill_price


class ExecutionSimulator:
    def __init__(self, cost_config: CostConfig):
        self.cost_config = cost_config

    def execute_order(self, order: Order, bar: Bar) -> Fill | None:
        if order.symbol != bar.symbol:
            return None

        # Liquidity constraint: order capped at 10% of bar volume if volume > 0
        fill_qty = order.quantity
        if bar.volume > 0 and fill_qty > (bar.volume * 0.10):
            fill_qty = bar.volume * 0.10

        if fill_qty <= 0:
            return None

        # Default: market orders fill at next bar open
        base_price = bar.open
        if order.order_type == OrderType.LIMIT and order.limit_price is not None:
            if order.side == OrderSide.BUY and bar.low > order.limit_price:
                return None
            if order.side == OrderSide.SELL and bar.high < order.limit_price:
                return None
            base_price = order.limit_price

        fill_price, slippage_dollars = calculate_fill_price(
            base_price=base_price,
            side=order.side,
            quantity=fill_qty,
            bar_volume=bar.volume,
            cost_config=self.cost_config,
        )

        commission = fill_qty * fill_price * (self.cost_config.equity_commission_bps / 10_000.0)

        return Fill(
            order_id=order.order_id,
            symbol=order.symbol,
            timestamp=bar.timestamp,
            side=order.side,
            quantity=fill_qty,
            price=fill_price,
            commission=round(commission, 4),
            slippage=round(slippage_dollars, 4),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_execution.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tactical_engine/execution/slippage.py src/tactical_engine/execution/simulator.py tests/test_execution.py
git commit -m "feat(execution): implement execution simulator with slippage and liquidity bounds"
```

---

### Task 10: Backtest Engine & State Machine

**Files:**
- Create: `src/tactical_engine/backtest/state.py`
- Create: `src/tactical_engine/backtest/engine.py`
- Test: `tests/test_backtest_engine.py`

**Interfaces:**
- Consumes: `dict[str, list[Bar]]`, `EngineConfig`
- Produces: `BacktestResult` containing trade logs, equity history, and fills.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_backtest_engine.py
from tactical_engine.backtest.engine import run_backtest
from tactical_engine.config import EngineConfig
from tactical_engine.data.synthetic import generate_synthetic_bars


def test_deterministic_backtest_run():
    bars_mu = generate_synthetic_bars(symbol="MU", num_bars=120, seed=42)
    cfg = EngineConfig()
    result1 = run_backtest(data={"MU": bars_mu}, config=cfg)
    result2 = run_backtest(data={"MU": bars_mu}, config=cfg)

    assert result1.total_trades == result2.total_trades
    assert result1.equity_curve == result2.equity_curve
    assert len(result1.trades) >= 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_backtest_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tactical_engine.backtest.engine'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tactical_engine/backtest/state.py
from datetime import datetime
from pydantic import BaseModel, Field
from tactical_engine.data.models import AccountState, Fill, OrderSide, Position


class TradeRecord(BaseModel):
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    net_pnl: float
    exit_reason: str


class PortfolioTracker:
    def __init__(self, initial_cash: float):
        self.cash = initial_cash
        self.positions: dict[str, Position] = {}
        self.closed_trades: list[TradeRecord] = []
        self.entry_times: dict[str, datetime] = {}

    def apply_fill(self, fill: Fill, exit_reason: str = "") -> None:
        pos = self.positions.get(fill.symbol, Position(symbol=fill.symbol))
        if fill.side == OrderSide.BUY:
            total_qty = pos.quantity + fill.quantity
            total_cost = (pos.quantity * pos.avg_price) + (fill.quantity * fill.price)
            new_avg = total_cost / total_qty if total_qty > 0 else 0.0
            self.positions[fill.symbol] = Position(
                symbol=fill.symbol,
                quantity=total_qty,
                avg_price=round(new_avg, 4),
                realized_pnl=pos.realized_pnl,
            )
            self.cash -= (fill.quantity * fill.price) + fill.commission
            if fill.symbol not in self.entry_times:
                self.entry_times[fill.symbol] = fill.timestamp
        else:
            # Sell
            gross_pnl = (fill.price - pos.avg_price) * fill.quantity
            net_pnl = gross_pnl - fill.commission - fill.slippage
            self.closed_trades.append(
                TradeRecord(
                    symbol=fill.symbol,
                    entry_time=self.entry_times.get(fill.symbol, fill.timestamp),
                    exit_time=fill.timestamp,
                    entry_price=pos.avg_price,
                    exit_price=fill.price,
                    quantity=fill.quantity,
                    gross_pnl=round(gross_pnl, 2),
                    net_pnl=round(net_pnl, 2),
                    exit_reason=exit_reason,
                )
            )
            self.cash += (fill.quantity * fill.price) - fill.commission
            remaining_qty = max(0.0, pos.quantity - fill.quantity)
            if remaining_qty == 0:
                self.positions.pop(fill.symbol, None)
                self.entry_times.pop(fill.symbol, None)
            else:
                self.positions[fill.symbol] = Position(
                    symbol=fill.symbol,
                    quantity=remaining_qty,
                    avg_price=pos.avg_price,
                    realized_pnl=pos.realized_pnl + net_pnl,
                )

    def get_account_state(
        self, timestamp: datetime, current_prices: dict[str, float]
    ) -> AccountState:
        equity = self.cash
        for sym, pos in self.positions.items():
            price = current_prices.get(sym, pos.avg_price)
            equity += pos.quantity * price
        return AccountState(
            timestamp=timestamp,
            cash=round(self.cash, 2),
            positions=self.positions.copy(),
            equity=round(equity, 2),
        )
```

```python
# src/tactical_engine/backtest/engine.py
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from tactical_engine.config import EngineConfig
from tactical_engine.data.models import Bar, Order, OrderSide, OrderType
from tactical_engine.execution.simulator import ExecutionSimulator
from tactical_engine.portfolio.sizing import calculate_position_size
from tactical_engine.signals.exits import check_exit_condition
from tactical_engine.signals.features import compute_bar_features
from tactical_engine.signals.pullback import generate_pullback_signals
from tactical_engine.backtest.state import PortfolioTracker, TradeRecord


class BacktestResult(BaseModel):
    initial_cash: float
    final_equity: float
    total_trades: int
    trades: list[TradeRecord]
    equity_curve: list[float]
    timestamps: list[str]


def run_backtest(data: dict[str, list[Bar]], config: EngineConfig) -> BacktestResult:
    # 1. Feature & Signal generation per symbol
    features_by_sym = {}
    signals_by_sym = {}
    for sym, bars in data.items():
        df_feat = compute_bar_features(bars, trend_window=config.signals.trend_window)
        features_by_sym[sym] = df_feat
        signals_by_sym[sym] = generate_pullback_signals(df_feat, config.signals)

    # 2. Synchronized bar simulation loop
    all_timestamps = sorted(list(set(b.timestamp for bars in data.values() for b in bars)))

    tracker = PortfolioTracker(initial_cash=config.portfolio.initial_cash)
    simulator = ExecutionSimulator(cost_config=config.costs)
    pending_orders: list[Order] = []
    equity_curve: list[float] = []
    time_index: list[str] = []

    for t_idx, ts in enumerate(all_timestamps):
        current_prices = {}
        bars_at_ts = {}

        # Collect current bars
        for sym, bars in data.items():
            for b in bars:
                if b.timestamp == ts:
                    current_prices[sym] = b.close
                    bars_at_ts[sym] = b
                    break

        account_state = tracker.get_account_state(ts, current_prices)
        equity_curve.append(account_state.equity)
        time_index.append(ts.isoformat())

        # A. Execute pending orders generated at previous bar close
        unfilled_orders = []
        for ord in pending_orders:
            bar = bars_at_ts.get(ord.symbol)
            if bar:
                fill = simulator.execute_order(ord, bar)
                if fill:
                    tracker.apply_fill(fill, exit_reason=ord.tag)
                else:
                    unfilled_orders.append(ord)
        pending_orders = unfilled_orders

        # B. Check exits on active positions
        for sym, pos in list(tracker.positions.items()):
            bar = bars_at_ts.get(sym)
            if not bar:
                continue
            entry_time = tracker.entry_times.get(sym, ts)
            df_sym = features_by_sym[sym]
            atr = float(df_sym.loc[ts, "atr"]) if ts in df_sym.index else 1.0
            should_exit, reason = check_exit_condition(
                entry_price=pos.avg_price,
                entry_time=entry_time,
                current_bar=bar,
                atr=atr,
                config=config.exits,
            )
            if should_exit:
                pending_orders.append(
                    Order(
                        order_id=str(uuid.uuid4())[:8],
                        symbol=sym,
                        timestamp=ts,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=pos.quantity,
                        tag=reason,
                    )
                )

        # C. Generate entry orders for next bar
        for sym, sigs in signals_by_sym.items():
            if sym in tracker.positions:
                continue  # Single layer for base test
            bar = bars_at_ts.get(sym)
            if not bar:
                continue
            # Look for signal confirmed at ts
            matching_sigs = [s for s in sigs if s.timestamp == ts and s.action == "ENTER_LONG"]
            if matching_sigs:
                sig = matching_sigs[0]
                df_sym = features_by_sym[sym]
                atr = float(df_sym.loc[ts, "atr"]) if ts in df_sym.index else 1.0
                stop_p = bar.close - (config.exits.stop_atr * atr)
                qty = calculate_position_size(
                    symbol=sym,
                    price=bar.close,
                    stop_price=stop_p,
                    account_state=account_state,
                    config=config.portfolio,
                )
                if qty > 0:
                    pending_orders.append(
                        Order(
                            order_id=str(uuid.uuid4())[:8],
                            symbol=sym,
                            timestamp=ts,
                            side=OrderSide.BUY,
                            order_type=OrderType.MARKET,
                            quantity=qty,
                            tag=sig.reason,
                        )
                    )

    final_prices = {sym: bars[-1].close for sym, bars in data.items() if bars}
    final_state = tracker.get_account_state(all_timestamps[-1], final_prices)

    return BacktestResult(
        initial_cash=config.portfolio.initial_cash,
        final_equity=final_state.equity,
        total_trades=len(tracker.closed_trades),
        trades=tracker.closed_trades,
        equity_curve=equity_curve,
        timestamps=time_index,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_backtest_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tactical_engine/backtest/state.py src/tactical_engine/backtest/engine.py tests/test_backtest_engine.py
git commit -m "feat(backtest): implement deterministic multi-asset backtest loop"
```

---

### Task 11: Performance Metrics & Attribution

**Files:**
- Create: `src/tactical_engine/reports/metrics.py`
- Create: `src/tactical_engine/reports/attribution.py`
- Test: `tests/test_metrics.py`

**Interfaces:**
- Consumes: `BacktestResult`
- Produces: `PerformanceMetrics` model (total return, max drawdown, win rate, profit factor, turnover, cost ratio).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_metrics.py
from datetime import datetime, timezone
from tactical_engine.backtest.engine import BacktestResult
from tactical_engine.backtest.state import TradeRecord
from tactical_engine.reports.metrics import calculate_metrics


def test_performance_metrics_calculation():
    t0 = datetime(2026, 1, 5, 14, 30, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 5, 15, 30, tzinfo=timezone.utc)
    result = BacktestResult(
        initial_cash=100_000.0,
        final_equity=105_000.0,
        total_trades=2,
        trades=[
            TradeRecord(
                symbol="MU",
                entry_time=t0,
                exit_time=t1,
                entry_price=100.0,
                exit_price=106.0,
                quantity=100.0,
                gross_pnl=600.0,
                net_pnl=590.0,
                exit_reason="target_hit",
            ),
            TradeRecord(
                symbol="MU",
                entry_time=t0,
                exit_time=t1,
                entry_price=100.0,
                exit_price=98.0,
                quantity=100.0,
                gross_pnl=-200.0,
                net_pnl=-210.0,
                exit_reason="stop_loss_hit",
            ),
        ],
        equity_curve=[100_000.0, 102_000.0, 99_000.0, 105_000.0],
        timestamps=[
            "2026-01-05T14:30:00Z",
            "2026-01-05T14:31:00Z",
            "2026-01-05T14:32:00Z",
            "2026-01-05T14:33:00Z",
        ],
    )
    metrics = calculate_metrics(result)
    assert metrics.total_return_pct == 5.0
    assert metrics.win_rate == 0.5
    assert metrics.profit_factor > 1.0
    assert metrics.max_drawdown_pct > 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_metrics.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tactical_engine.reports.metrics'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tactical_engine/reports/metrics.py
import numpy as np
from pydantic import BaseModel
from tactical_engine.backtest.engine import BacktestResult


class PerformanceMetrics(BaseModel):
    initial_cash: float
    final_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    total_trades: int
    win_rate: float
    profit_factor: float
    expectancy_per_trade: float
    gross_pnl: float
    net_pnl: float
    cost_drag_pct: float


def calculate_metrics(result: BacktestResult) -> PerformanceMetrics:
    init_c = result.initial_cash
    final_eq = result.final_equity
    tot_ret = ((final_eq - init_c) / init_c) * 100.0 if init_c > 0 else 0.0

    # Max Drawdown
    eq = np.array(result.equity_curve)
    if len(eq) > 0:
        peaks = np.maximum.accumulate(eq)
        drawdowns = (peaks - eq) / peaks
        max_dd = float(np.max(drawdowns)) * 100.0
    else:
        max_dd = 0.0

    # Trade stats
    trades = result.trades
    total_trades = len(trades)
    if total_trades > 0:
        wins = [t for t in trades if t.net_pnl > 0]
        losses = [t for t in trades if t.net_pnl <= 0]
        win_rate = len(wins) / total_trades
        gross_profit = sum(t.net_pnl for t in wins)
        gross_loss = abs(sum(t.net_pnl for t in losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")
        net_pnl = sum(t.net_pnl for t in trades)
        gross_pnl = sum(t.gross_pnl for t in trades)
        expectancy = net_pnl / total_trades
        cost_drag = ((gross_pnl - net_pnl) / abs(gross_pnl)) * 100.0 if gross_pnl != 0 else 0.0
    else:
        win_rate = 0.0
        profit_factor = 0.0
        net_pnl = 0.0
        gross_pnl = 0.0
        expectancy = 0.0
        cost_drag = 0.0

    return PerformanceMetrics(
        initial_cash=init_c,
        final_equity=final_eq,
        total_return_pct=round(tot_ret, 2),
        max_drawdown_pct=round(max_dd, 2),
        total_trades=total_trades,
        win_rate=round(win_rate, 4),
        profit_factor=round(profit_factor, 2),
        expectancy_per_trade=round(expectancy, 2),
        gross_pnl=round(gross_pnl, 2),
        net_pnl=round(net_pnl, 2),
        cost_drag_pct=round(cost_drag, 2),
    )
```

```python
# src/tactical_engine/reports/attribution.py
from collections import defaultdict
from tactical_engine.backtest.engine import BacktestResult


def attribute_pnl_by_ticker(result: BacktestResult) -> dict[str, float]:
    pnl_by_sym = defaultdict(float)
    for t in result.trades:
        pnl_by_sym[t.symbol] += t.net_pnl
    return {k: round(v, 2) for k, v in pnl_by_sym.items()}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_metrics.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tactical_engine/reports/metrics.py src/tactical_engine/reports/attribution.py tests/test_metrics.py
git commit -m "feat(reports): implement performance metrics and ticker attribution"
```

---

### Task 12: Markdown Report Renderer & CLI Entry Point

**Files:**
- Create: `src/tactical_engine/reports/renderer.py`
- Create: `src/tactical_engine/__main__.py`
- Test: `tests/test_cli_and_report.py`

**Interfaces:**
- Consumes: `PerformanceMetrics`, `RunManifest`, `attribution`
- Produces: Formatted Markdown report string and runnable CLI: `python -m tactical_engine --config configs/base.yaml`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli_and_report.py
from tactical_engine.backtest.manifest import RunManifest
from tactical_engine.reports.metrics import PerformanceMetrics
from tactical_engine.reports.renderer import render_markdown_report


def test_markdown_report_rendering():
    manifest = RunManifest(
        config_hash="abc1234",
        strategy_variant="risk_controlled",
        symbols=["MU"],
        timeframe="1m",
        random_seed=42,
    )
    metrics = PerformanceMetrics(
        initial_cash=100000.0,
        final_equity=105000.0,
        total_return_pct=5.0,
        max_drawdown_pct=2.1,
        total_trades=10,
        win_rate=0.6,
        profit_factor=1.8,
        expectancy_per_trade=500.0,
        gross_pnl=5500.0,
        net_pnl=5000.0,
        cost_drag_pct=9.1,
    )
    report = render_markdown_report(metrics, manifest, {"MU": 5000.0})
    assert "# Tactical Research Engine — Backtest Report" in report
    assert "risk_controlled" in report
    assert "5.0%" in report
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli_and_report.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tactical_engine.reports.renderer'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/tactical_engine/reports/renderer.py
from tactical_engine.backtest.manifest import RunManifest
from tactical_engine.reports.metrics import PerformanceMetrics


def render_markdown_report(
    metrics: PerformanceMetrics,
    manifest: RunManifest,
    ticker_attribution: dict[str, float],
) -> str:
    lines = [
        "# Tactical Research Engine — Backtest Report",
        "",
        "## Run Metadata",
        f"- **Run ID:** `{manifest.run_id}`",
        f"- **Git Commit:** `{manifest.git_commit}`",
        f"- **Config Hash:** `{manifest.config_hash}`",
        f"- **Strategy Variant:** `{manifest.strategy_variant}`",
        f"- **Symbols:** {', '.join(manifest.symbols)}",
        f"- **Timeframe:** `{manifest.timeframe}`",
        f"- **Timestamp (UTC):** `{manifest.created_at_utc}`",
        "",
        "## Performance Summary",
        "| Metric | Value |",
        "|---|---|",
        f"| Initial Capital | ${metrics.initial_cash:,.2f} |",
        f"| Final Equity | ${metrics.final_equity:,.2f} |",
        f"| Total Return | {metrics.total_return_pct:.2f}% |",
        f"| Max Drawdown | {metrics.max_drawdown_pct:.2f}% |",
        f"| Total Closed Trades | {metrics.total_trades} |",
        f"| Win Rate | {metrics.win_rate * 100:.2f}% |",
        f"| Profit Factor | {metrics.profit_factor:.2f} |",
        f"| Expectancy / Trade | ${metrics.expectancy_per_trade:,.2f} |",
        f"| Net P&L | ${metrics.net_pnl:,.2f} |",
        f"| Cost Drag | {metrics.cost_drag_pct:.2f}% |",
        "",
        "## Ticker P&L Attribution",
        "| Ticker | Net Realized P&L |",
        "|---|---|",
    ]
    for sym, pnl in ticker_attribution.items():
        lines.append(f"| {sym} | ${pnl:,.2f} |")

    lines.append("")
    lines.append("> [!NOTE]")
    lines.append(
        "> All metrics reflect deterministic execution under explicit cost and slippage models."
    )
    return "\n".join(lines)
```

```python
# src/tactical_engine/__main__.py
import argparse
from pathlib import Path
from tactical_engine.backtest.engine import run_backtest
from tactical_engine.backtest.manifest import create_manifest
from tactical_engine.config import load_config
from tactical_engine.data.synthetic import generate_synthetic_bars
from tactical_engine.reports.attribution import attribute_pnl_by_ticker
from tactical_engine.reports.metrics import calculate_metrics
from tactical_engine.reports.renderer import render_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(description="High-Beta Tactical Research Engine")
    parser.add_argument(
        "--config", type=str, default="configs/base.yaml", help="Path to YAML config"
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=200,
        help="Number of synthetic bars per ticker if using fixtures",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Loaded config: {args.config} (variant={config.strategy.variant})")

    # Generate synthetic fixtures for symbols
    data = {
        sym: generate_synthetic_bars(
            symbol=sym, num_bars=args.bars, seed=config.project.random_seed + i
        )
        for i, sym in enumerate(config.strategy.universe)
    }

    manifest = create_manifest(config)
    result = run_backtest(data, config)
    metrics = calculate_metrics(result)
    attribution = attribute_pnl_by_ticker(result)

    report_md = render_markdown_report(metrics, manifest, attribution)

    out_dir = Path(config.outputs.root)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / f"run_{manifest.run_id[:8]}.md"
    report_file.write_text(report_md, encoding="utf-8")

    print(
        f"Backtest completed: {metrics.total_trades} trades. Final Equity: ${metrics.final_equity:,.2f}"
    )
    print(f"Report generated: {report_file}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli_and_report.py -v`
Expected: PASS

- [ ] **Step 5: Run full CLI smoke test**

Run: `python -m tactical_engine --config configs/base.yaml`
Expected: Outputs report file in `reports/` and prints summary without errors.

- [ ] **Step 6: Commit**

```bash
git add src/tactical_engine/reports/renderer.py src/tactical_engine/__main__.py tests/test_cli_and_report.py
git commit -m "feat(cli): add Markdown report renderer and CLI entrypoint"
```
