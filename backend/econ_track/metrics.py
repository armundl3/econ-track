from __future__ import annotations

from statistics import mean

from econ_track.models import AssetConfig, AssetMetrics, PricePoint


def compute_metrics(asset: AssetConfig, points: list[PricePoint]) -> AssetMetrics:
    if len(points) < 2:
        raise ValueError(f"{asset.symbol} needs at least two price points")

    latest = points[-1]
    closes = [point.close for point in points]
    sma_50 = _sma(closes, 50)
    sma_100 = _sma(closes, 100)
    sma_200 = _sma(closes, 200)
    distance_50 = _distance(latest.close, sma_50)
    distance_100 = _distance(latest.close, sma_100)
    distance_200 = _distance(latest.close, sma_200)
    return_1m = _trailing_return(closes, 21)
    return_3m = _trailing_return(closes, 63)
    return_6m = _trailing_return(closes, 126)
    drawdown_52w = _drawdown(closes, 252)

    score, reasons = _score_signal(distance_50, distance_200, return_3m, drawdown_52w)
    return AssetMetrics(
        symbol=asset.symbol,
        name=asset.name,
        latest_date=latest.date,
        latest_close=latest.close,
        sma_50=sma_50,
        sma_100=sma_100,
        sma_200=sma_200,
        distance_sma_50=distance_50,
        distance_sma_100=distance_100,
        distance_sma_200=distance_200,
        return_1m=return_1m,
        return_3m=return_3m,
        return_6m=return_6m,
        drawdown_52w=drawdown_52w,
        signal_score=score,
        signal_label=_label(score),
        reasons=tuple(reasons),
    )


def _sma(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return mean(values[-window:])


def _distance(price: float, average: float | None) -> float | None:
    if average is None or average == 0:
        return None
    return (price / average) - 1


def _trailing_return(values: list[float], sessions: int) -> float | None:
    if len(values) <= sessions:
        return None
    base = values[-sessions - 1]
    if base == 0:
        return None
    return (values[-1] / base) - 1


def _drawdown(values: list[float], sessions: int) -> float | None:
    window = values[-sessions:] if len(values) >= sessions else values
    high = max(window)
    if high == 0:
        return None
    return (values[-1] / high) - 1


def _score_signal(
    distance_50: float | None,
    distance_200: float | None,
    return_3m: float | None,
    drawdown_52w: float | None,
) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    if distance_200 is not None:
        if distance_200 > 0.04:
            score += 0.45
            reasons.append("above 200-day trend")
        elif distance_200 < -0.04:
            score -= 0.25
            reasons.append("below 200-day trend")

    if distance_50 is not None:
        if -0.06 <= distance_50 <= -0.015:
            score += 0.25
            reasons.append("near-term pullback")
        elif distance_50 > 0.08:
            score -= 0.15
            reasons.append("extended above 50-day average")

    if return_3m is not None:
        if return_3m > 0.05:
            score += 0.25
            reasons.append("positive 3-month momentum")
        elif return_3m < -0.05:
            score -= 0.25
            reasons.append("negative 3-month momentum")

    if drawdown_52w is not None:
        if -0.18 <= drawdown_52w <= -0.08:
            score += 0.15
            reasons.append("moderate 52-week discount")
        elif drawdown_52w < -0.25:
            score -= 0.15
            reasons.append("deep drawdown risk")

    if not reasons:
        reasons.append("neutral signal mix")

    return max(-1.0, min(1.0, score)), reasons


def _label(score: float) -> str:
    if score >= 0.35:
        return "overweight"
    if score <= -0.25:
        return "underweight"
    return "neutral"
