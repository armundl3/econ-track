from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from econ_track.allocation import allocate_all_strategies
from econ_track.config import load_config
from econ_track.metrics import compute_metrics, compute_volatility
from econ_track.provider import MarketDataError, YahooChartProvider, fetch_all


def build_dataset(config_path: str | Path) -> dict[str, Any]:
    """Build the complete static dashboard dataset from config and market data."""
    config = load_config(config_path)
    symbols = [asset.symbol for asset in config.assets]
    provider = YahooChartProvider()
    prices = fetch_all(provider, symbols + [config.volatility_symbol], config.lookback_years)
    metrics = [compute_metrics(asset, prices[asset.symbol]) for asset in config.assets]
    volatility = compute_volatility(config.volatility_symbol, prices[config.volatility_symbol])
    strategy_allocations = allocate_all_strategies(config, metrics, volatility)
    latest_date = max(item.latest_date for item in metrics)
    base_per_run = config.contribution_per_asset * len(config.assets)

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "latest_market_date": latest_date.isoformat(),
        "status": {"ok": True, "warnings": []},
        "config": {
            "contribution_per_asset": config.contribution_per_asset,
            "runs_per_month": list(config.runs_per_month),
            "reserve_cash_per_run": config.reserve_cash_per_run,
            "default_strategy": config.default_strategy,
            "tilt_strength": config.tilt_strength,
            "max_monthly_shift": config.max_monthly_shift,
            "base_deployment_per_run": base_per_run,
            "base_deployment_per_month": base_per_run * len(config.runs_per_month),
            "assets": [asdict(asset) for asset in config.assets],
        },
        "volatility": _serialize_metrics(volatility),
        "metrics": [_serialize_metrics(item) for item in metrics],
        "strategy_allocations": {
            strategy: [asdict(item) for item in allocations]
            for strategy, allocations in strategy_allocations.items()
        },
        "allocations": [asdict(item) for item in strategy_allocations[config.default_strategy]],
        "disclaimer": "For personal education and research only. Not financial advice.",
    }


def write_dataset(config_path: str | Path, output_path: str | Path, keep_last_good: bool = True) -> dict[str, Any]:
    """Write the dashboard dataset, optionally preserving stale data on refresh failure."""
    output = Path(output_path)
    try:
        dataset = build_dataset(config_path)
    except (MarketDataError, OSError, ValueError) as exc:
        if keep_last_good and output.exists():
            dataset = json.loads(output.read_text(encoding="utf-8"))
            warnings = list(dataset.get("status", {}).get("warnings", []))
            warnings.append(f"Refresh failed at {datetime.now(tz=UTC).isoformat()}: {exc}")
            dataset["status"] = {"ok": False, "warnings": warnings}
            dataset["generated_at"] = datetime.now(tz=UTC).isoformat()
        else:
            raise

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return dataset


def _serialize_metrics(metrics: Any) -> dict[str, Any]:
    """Convert dataclass metrics into JSON-serializable dictionaries."""
    data = asdict(metrics)
    for key, value in list(data.items()):
        if isinstance(value, date):
            data[key] = value.isoformat()
    return data
