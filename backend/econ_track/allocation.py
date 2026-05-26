from __future__ import annotations

from econ_track.models import Allocation, AppConfig, AssetMetrics


def allocate(config: AppConfig, metrics: list[AssetMetrics]) -> list[Allocation]:
    metrics_by_symbol = {item.symbol: item for item in metrics}
    raw_weights: dict[str, float] = {}
    for asset in config.assets:
        score = metrics_by_symbol[asset.symbol].signal_score
        desired_tilt = score * config.tilt_strength
        capped_tilt = max(-config.max_monthly_shift, min(config.max_monthly_shift, desired_tilt))
        raw = asset.base_weight + capped_tilt
        raw_weights[asset.symbol] = max(asset.min_weight, min(asset.max_weight, raw))

    normalized = _normalize_with_bounds(raw_weights, config)
    allocations = []
    for asset in config.assets:
        final_weight = normalized[asset.symbol]
        allocations.append(
            Allocation(
                symbol=asset.symbol,
                name=asset.name,
                base_weight=asset.base_weight,
                final_weight=final_weight,
                dollars=round(config.monthly_contribution * final_weight, 2),
                tilt=final_weight - asset.base_weight,
            )
        )
    return allocations


def _normalize_with_bounds(weights: dict[str, float], config: AppConfig) -> dict[str, float]:
    assets = {asset.symbol: asset for asset in config.assets}
    result = dict(weights)

    for _ in range(20):
        total = sum(result.values())
        diff = 1.0 - total
        if abs(diff) < 0.000001:
            break

        if diff > 0:
            adjustable = [symbol for symbol, weight in result.items() if weight < assets[symbol].max_weight]
        else:
            adjustable = [symbol for symbol, weight in result.items() if weight > assets[symbol].min_weight]
        if not adjustable:
            break

        share = diff / len(adjustable)
        changed = False
        for symbol in adjustable:
            asset = assets[symbol]
            updated = max(asset.min_weight, min(asset.max_weight, result[symbol] + share))
            changed = changed or abs(updated - result[symbol]) > 0.000001
            result[symbol] = updated
        if not changed:
            break

    total = sum(result.values())
    if total == 0:
        raise ValueError("allocation weights sum to zero")
    return {symbol: weight / total for symbol, weight in result.items()}
