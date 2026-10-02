from datetime import datetime
from pathlib import Path
from typing import Literal, Protocol

import pandas as pd
from pydantic import BaseModel

from tactical_engine.data.models import Bar


class RegimeState(BaseModel, frozen=True):
    timestamp: datetime
    sector_symbol: str = "SMH"
    broad_symbol: str = "SPY"
    sector_return: float = 0.0
    broad_return: float = 0.0
    sector_trend_ok: bool = True
    broad_trend_ok: bool = True
    relative_strength: float = 0.0  # sector_return - broad_return
    volatility_regime: str = "NORMAL"
    regime_allows_trade: bool = True


class RegimeProvider(Protocol):
    def get_regime_state(self, timestamp: datetime) -> RegimeState: ...


class DefaultRegimeProvider:
    """Neutral regime provider that permits all trading."""

    def get_regime_state(self, timestamp: datetime) -> RegimeState:
        return RegimeState(timestamp=timestamp, regime_allows_trade=True)


class BenchmarkRegimeProvider:
    """Computes genuine sector (SMH) and broad-market (SPY) trend and relative strength."""

    def __init__(
        self,
        sector_bars: list[Bar],
        broad_bars: list[Bar],
        sector_symbol: str = "SMH",
        broad_symbol: str = "SPY",
        trend_window: int = 60,
        filter_mode: Literal["none", "sector", "broad", "combined"] = "sector",
    ):
        self.sector_symbol = sector_symbol
        self.broad_symbol = broad_symbol
        self.trend_window = trend_window
        self.filter_mode = filter_mode
        self._states: dict[datetime, RegimeState] = {}
        self._precompute(sector_bars, broad_bars)

    def _precompute(self, sector_bars: list[Bar], broad_bars: list[Bar]) -> None:
        if not sector_bars and not broad_bars:
            return

        df_sec = self._make_df(sector_bars)
        df_brd = self._make_df(broad_bars)

        # Merge on timestamp
        all_ts = sorted(list(set(df_sec.index).union(set(df_brd.index))))
        for ts in all_ts:
            sec_row = df_sec.loc[ts] if ts in df_sec.index else None
            brd_row = df_brd.loc[ts] if ts in df_brd.index else None

            sec_ret = float(sec_row["ret"]) if sec_row is not None else 0.0
            brd_ret = float(brd_row["ret"]) if brd_row is not None else 0.0
            sec_ok = bool(sec_row["trend_ok"]) if sec_row is not None else True
            brd_ok = bool(brd_row["trend_ok"]) if brd_row is not None else True
            rel_strength = sec_ret - brd_ret

            # Volatility proxy: annualized rolling std of broad index
            brd_vol = float(brd_row["rolling_vol"]) if brd_row is not None else 0.15
            if brd_vol > 0.30:
                vol_regime = "HIGH"
            elif brd_vol < 0.10:
                vol_regime = "LOW"
            else:
                vol_regime = "NORMAL"

            if self.filter_mode == "none":
                allows = True
            elif self.filter_mode == "sector":
                allows = sec_ok
            elif self.filter_mode == "broad":
                allows = brd_ok
            elif self.filter_mode == "combined":
                allows = sec_ok and brd_ok
            else:
                allows = True

            self._states[ts] = RegimeState(
                timestamp=ts,
                sector_symbol=self.sector_symbol,
                broad_symbol=self.broad_symbol,
                sector_return=round(sec_ret, 6),
                broad_return=round(brd_ret, 6),
                sector_trend_ok=sec_ok,
                broad_trend_ok=brd_ok,
                relative_strength=round(rel_strength, 6),
                volatility_regime=vol_regime,
                regime_allows_trade=allows,
            )

    def _make_df(self, bars: list[Bar]) -> pd.DataFrame:
        if not bars:
            return pd.DataFrame()
        data = [{"timestamp": b.timestamp, "close": b.close} for b in bars]
        df = pd.DataFrame(data).set_index("timestamp").sort_index()
        df["ret"] = df["close"].pct_change().fillna(0.0)
        fast_ma = df["close"].rolling(window=max(5, self.trend_window // 4), min_periods=1).mean()
        slow_ma = df["close"].rolling(window=self.trend_window, min_periods=1).mean()
        df["trend_ok"] = fast_ma >= slow_ma
        df["rolling_vol"] = df["ret"].rolling(window=20, min_periods=5).std().fillna(0.15) * (
            252**0.5
        )
        return df

    def get_regime_state(self, timestamp: datetime) -> RegimeState:
        if timestamp in self._states:
            return self._states[timestamp]
        # Return fallback neutral state if timestamp not found
        return RegimeState(timestamp=timestamp, regime_allows_trade=True)


class ExternalRegimeProvider:
    """Optional adapter that loads precomputed regime classifications (e.g. from RS2/MRI)."""

    def __init__(self, file_path: Path | str):
        self.file_path = Path(file_path)
        self._states: dict[datetime, RegimeState] = {}
        if self.file_path.is_file():
            self._load()

    def _load(self) -> None:
        if self.file_path.suffix.lower() == ".csv":
            df = pd.read_csv(self.file_path)
        elif self.file_path.suffix.lower() == ".json":
            df = pd.read_json(self.file_path)
        else:
            return

        df.columns = [c.strip().lower() for c in df.columns]
        time_col = next((c for c in ["timestamp", "date"] if c in df.columns), None)
        if not time_col:
            return
        df[time_col] = pd.to_datetime(df[time_col], utc=True)
        for _, row in df.iterrows():
            ts = row[time_col].to_pydatetime()
            allows = bool(row["regime_allows_trade"]) if "regime_allows_trade" in row else True
            vol_regime = str(row.get("volatility_regime", "NORMAL"))
            self._states[ts] = RegimeState(
                timestamp=ts,
                regime_allows_trade=allows,
                volatility_regime=vol_regime,
            )

    def get_regime_state(self, timestamp: datetime) -> RegimeState:
        return self._states.get(
            timestamp, RegimeState(timestamp=timestamp, regime_allows_trade=True)
        )
