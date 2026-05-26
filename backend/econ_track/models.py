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
    monthly_contribution: float
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
    sma_50: float | None
    sma_100: float | None
    sma_200: float | None
    distance_sma_50: float | None
    distance_sma_100: float | None
    distance_sma_200: float | None
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
    base_weight: float
    final_weight: float
    dollars: float
    tilt: float
