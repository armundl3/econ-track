from __future__ import annotations

from econ_track.models import Allocation, AppConfig, AssetMetrics, VolatilityMetrics


STRATEGIES = ("dip_uptrend", "momentum", "mean_reversion")


def allocate(config: AppConfig, metrics: list[AssetMetrics], volatility: VolatilityMetrics, strategy: str) -> list[Allocation]:
    """Allocate a single DCA run across assets for the selected strategy."""
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy: {strategy}")

    scores = {item.symbol: _strategy_score(item, strategy) for item in metrics}
    positive_total = sum(max(score, 0.0) for score in scores.values())
    throttle = _volatility_throttle(volatility.regime, strategy)
    reserve_budget = round(config.reserve_cash_per_run * throttle, 2)
    base_total = config.contribution_per_asset * len(config.assets)
    deployed_total = base_total + (reserve_budget if positive_total > 0 else 0)

    allocations: list[Allocation] = []
    for asset in config.assets:
        score = scores[asset.symbol]
        reserve_dollars = 0.0
        if positive_total > 0:
            reserve_dollars = round(reserve_budget * max(score, 0.0) / positive_total, 2)
        total_dollars = round(config.contribution_per_asset + reserve_dollars, 2)
        allocations.append(
            Allocation(
                symbol=asset.symbol,
                name=asset.name,
                strategy=strategy,
                base_dollars=config.contribution_per_asset,
                reserve_dollars=reserve_dollars,
                total_dollars=total_dollars,
                final_weight=total_dollars / deployed_total if deployed_total else 0,
                opportunity_score=score,
            )
        )
    return allocations


def allocate_all_strategies(
    config: AppConfig, metrics: list[AssetMetrics], volatility: VolatilityMetrics
) -> dict[str, list[Allocation]]:
    """Build allocation recommendations for every supported strategy."""
    return {strategy: allocate(config, metrics, volatility, strategy) for strategy in STRATEGIES}


def _strategy_score(metrics: AssetMetrics, strategy: str) -> float:
    """Score one asset's opportunity under a strategy using short-term trend inputs."""
    distances = [metrics.distance_sma_5, metrics.distance_sma_10, metrics.distance_sma_15]
    changes = [metrics.sma_5_change, metrics.sma_10_change, metrics.sma_15_change]
    usable_distances = [value for value in distances if value is not None]
    usable_changes = [value for value in changes if value is not None]

    if not usable_distances:
        return 0.0

    avg_distance = sum(usable_distances) / len(usable_distances)
    avg_change = sum(usable_changes) / len(usable_changes) if usable_changes else 0.0
    distance_15 = metrics.distance_sma_15 or 0.0
    change_15 = metrics.sma_15_change or 0.0

    if strategy == "dip_uptrend":
        pullback = max(0.0, min(0.12, -avg_distance)) / 0.12
        trend = 1.0 if change_15 > 0 and distance_15 > -0.08 else 0.35
        return round(max(0.0, pullback * trend), 4)

    if strategy == "momentum":
        trend_distance = max(0.0, min(0.12, avg_distance)) / 0.12
        trend_change = max(0.0, min(0.05, avg_change)) / 0.05
        return round((trend_distance * 0.6) + (trend_change * 0.4), 4)

    mean_gap = max(0.0, min(0.15, -avg_distance)) / 0.15
    falling_average_bonus = max(0.0, min(0.05, -avg_change)) / 0.05
    risk_floor = 0.55 if change_15 < -0.06 else 1.0
    return round(((mean_gap * 0.75) + (falling_average_bonus * 0.25)) * risk_floor, 4)


def _volatility_throttle(regime: str, strategy: str) -> float:
    """Return the reserve-cash deployment fraction allowed by volatility regime."""
    if regime == "calm":
        return 1.0
    if regime == "normal":
        return 1.0
    if regime == "elevated":
        return 0.85 if strategy == "mean_reversion" else 0.7
    return 0.65 if strategy == "mean_reversion" else 0.4
