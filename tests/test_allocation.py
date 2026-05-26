import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from econ_track.allocation import allocate
from econ_track.models import AppConfig, AssetConfig, AssetMetrics


def metric(symbol: str, score: float) -> AssetMetrics:
    return AssetMetrics(
        symbol=symbol,
        name=symbol,
        latest_date=date(2025, 1, 1),
        latest_close=100,
        sma_50=100,
        sma_100=100,
        sma_200=100,
        distance_sma_50=0,
        distance_sma_100=0,
        distance_sma_200=0,
        return_1m=0,
        return_3m=0,
        return_6m=0,
        drawdown_52w=0,
        signal_score=score,
        signal_label="neutral",
        reasons=("test",),
    )


class AllocationTests(unittest.TestCase):
    def test_allocates_monthly_dollars_and_normalizes(self) -> None:
        config = AppConfig(
            monthly_contribution=1000,
            lookback_years=5,
            tilt_strength=0.12,
            max_monthly_shift=0.15,
            assets=(
                AssetConfig("VGT", "VGT", 0.34, 0.15, 0.6),
                AssetConfig("VTI", "VTI", 0.33, 0.15, 0.6),
                AssetConfig("VOO", "VOO", 0.33, 0.15, 0.6),
            ),
        )

        allocations = allocate(config, [metric("VGT", 1), metric("VTI", 0), metric("VOO", -1)])

        self.assertAlmostEqual(sum(item.final_weight for item in allocations), 1.0, places=6)
        self.assertAlmostEqual(sum(item.dollars for item in allocations), 1000.0, places=2)
        self.assertGreater(allocations[0].final_weight, allocations[2].final_weight)


if __name__ == "__main__":
    unittest.main()
