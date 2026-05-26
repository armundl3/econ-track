from __future__ import annotations

import json
import logging
from pathlib import Path

from econ_track.models import AppConfig, AssetConfig

VALID_STRATEGIES = {"dip_uptrend", "momentum", "mean_reversion"}
logger = logging.getLogger(__name__)


def load_config(path: str | Path) -> AppConfig:
    """Load and validate the application config from a JSON file."""
    config_path = Path(path)
    logger.info("Loading config from %s", config_path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    allocation = raw.get("allocation", {})
    market_indicators = raw.get("market_indicators", {})
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
        contribution_per_asset=float(raw["contribution_per_asset"]),
        runs_per_month=tuple(str(item) for item in raw.get("runs_per_month", ["beginning", "middle"])),
        reserve_cash_per_run=float(raw.get("reserve_cash_per_run", 0)),
        default_strategy=str(raw.get("default_strategy", "mean_reversion")),
        volatility_symbol=str(market_indicators.get("volatility_symbol", "^VIX")),
        lookback_years=int(raw.get("lookback_years", 5)),
        tilt_strength=float(allocation.get("tilt_strength", 0.12)),
        max_monthly_shift=float(allocation.get("max_monthly_shift", 0.15)),
        assets=assets,
    )
    validate_config(config)
    logger.info(
        "Loaded config with %d assets, default strategy %s, %d DCA runs per month",
        len(config.assets),
        config.default_strategy,
        len(config.runs_per_month),
    )
    return config


def validate_config(config: AppConfig) -> None:
    """Raise ValueError when config values are missing, inconsistent, or unsafe."""
    logger.info("Validating config for %d assets", len(config.assets))
    if config.contribution_per_asset <= 0:
        raise ValueError("contribution_per_asset must be positive")
    if config.reserve_cash_per_run < 0:
        raise ValueError("reserve_cash_per_run cannot be negative")
    if not config.runs_per_month:
        raise ValueError("at least one DCA run per month is required")
    if config.default_strategy not in VALID_STRATEGIES:
        raise ValueError(f"default_strategy must be one of {sorted(VALID_STRATEGIES)}")
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
    logger.info("Config validation passed")
