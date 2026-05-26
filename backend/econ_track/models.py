from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AssetConfig:
    symbol: str
    name: str
    base_weight: float
    min_weight: float
    max_weight: float


@dataclass(frozen=True)
class AppConfig:
    contribution_per_asset: float
    runs_per_month: tuple[str, ...]
    reserve_cash_per_run: float
    default_strategy: str
    volatility_symbol: str
    lookback_years: int
    tilt_strength: float
    max_monthly_shift: float
    assets: tuple[AssetConfig, ...]


@dataclass(frozen=True)
class PricePoint:
    date: date
    close: float


@dataclass(frozen=True)
class AssetMetrics:
    symbol: str
    name: str
    latest_date: date
    latest_close: float
    sma_5: float | None
    sma_10: float | None
    sma_15: float | None
    sma_50: float | None
    sma_100: float | None
    sma_200: float | None
    distance_sma_5: float | None
    distance_sma_10: float | None
    distance_sma_15: float | None
    distance_sma_50: float | None
    distance_sma_100: float | None
    distance_sma_200: float | None
    sma_5_change: float | None
    sma_10_change: float | None
    sma_15_change: float | None
    return_1m: float | None
    return_3m: float | None
    return_6m: float | None
    drawdown_52w: float | None
    signal_score: float
    signal_label: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class Allocation:
    symbol: str
    name: str
    strategy: str
    base_dollars: float
    reserve_dollars: float
    total_dollars: float
    final_weight: float
    opportunity_score: float


@dataclass(frozen=True)
class VolatilityMetrics:
    symbol: str
    latest_date: date
    latest_close: float
    average_20d: float | None
    regime: str
