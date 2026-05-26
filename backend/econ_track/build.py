from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from econ_track.allocation import allocate
from econ_track.config import load_config
from econ_track.metrics import compute_metrics
from econ_track.provider import MarketDataError, YahooChartProvider, fetch_all


def build_dataset(config_path: str | Path) -> dict[str, Any]:
    config = load_config(config_path)
    symbols = [asset.symbol for asset in config.assets]
    provider = YahooChartProvider()
    prices = fetch_all(provider, symbols, config.lookback_years)
    metrics = [compute_metrics(asset, prices[asset.symbol]) for asset in config.assets]
    allocations = allocate(config, metrics)
    latest_date = max(item.latest_date for item in metrics)

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "latest_market_date": latest_date.isoformat(),
        "status": {"ok": True, "warnings": []},
        "config": {
            "monthly_contribution": config.monthly_contribution,
            "tilt_strength": config.tilt_strength,
            "max_monthly_shift": config.max_monthly_shift,
            "assets": [asdict(asset) for asset in config.assets],
        },
        "metrics": [_serialize_metrics(item) for item in metrics],
        "allocations": [asdict(item) for item in allocations],
        "disclaimer": "For personal education and research only. Not financial advice.",
    }


def write_dataset(config_path: str | Path, output_path: str | Path, keep_last_good: bool = True) -> dict[str, Any]:
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
    data = asdict(metrics)
    for key, value in list(data.items()):
        if isinstance(value, date):
            data[key] = value.isoformat()
    return data
