from __future__ import annotations

import json
from pathlib import Path

from econ_track.models import AppConfig, AssetConfig


def load_config(path: str | Path) -> AppConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    allocation = raw.get("allocation", {})
    assets = tuple(
        AssetConfig(
            symbol=str(item["symbol"]).upper(),
            name=str(item.get("name") or item["symbol"]).strip(),
            base_weight=float(item["base_weight"]),
            min_weight=float(item["min_weight"]),
            max_weight=float(item["max_weight"]),
        )
        for item in raw["assets"]
    )
    config = AppConfig(
        monthly_contribution=float(raw["monthly_contribution"]),
        lookback_years=int(raw.get("lookback_years", 5)),
        tilt_strength=float(allocation.get("tilt_strength", 0.12)),
        max_monthly_shift=float(allocation.get("max_monthly_shift", 0.15)),
        assets=assets,
    )
    validate_config(config)
    return config


def validate_config(config: AppConfig) -> None:
    if config.monthly_contribution <= 0:
        raise ValueError("monthly_contribution must be positive")
    if not config.assets:
        raise ValueError("at least one asset is required")

    total = sum(asset.base_weight for asset in config.assets)
    if abs(total - 1.0) > 0.001:
        raise ValueError(f"base weights must sum to 1.0, got {total:.4f}")

    symbols = set()
    for asset in config.assets:
        if asset.symbol in symbols:
            raise ValueError(f"duplicate asset symbol: {asset.symbol}")
        symbols.add(asset.symbol)
        if not 0 <= asset.min_weight <= asset.base_weight <= asset.max_weight <= 1:
            raise ValueError(f"invalid weight bounds for {asset.symbol}")
