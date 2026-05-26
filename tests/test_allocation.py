import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from econ_track.allocation import allocate, allocate_all_strategies
from econ_track.models import AppConfig, AssetConfig, AssetMetrics, VolatilityMetrics


def metric(symbol: str, score: float) -> AssetMetrics:
    return AssetMetrics(
        symbol=symbol,
        name=symbol,
        latest_date=date(2025, 1, 1),
        latest_close=100,
        sma_5=100,
        sma_10=100,
        sma_15=100,
        sma_50=100,
        sma_100=100,
        sma_200=100,
        distance_sma_5=-0.05 if score > 0 else 0.05,
        distance_sma_10=-0.04 if score > 0 else 0.04,
        distance_sma_15=-0.03 if score > 0 else 0.03,
        distance_sma_50=0,
        distance_sma_100=0,
        distance_sma_200=0,
        sma_5_change=-0.01 if score > 0 else 0.01,
        sma_10_change=-0.01 if score > 0 else 0.01,
        sma_15_change=-0.01 if score > 0 else 0.01,
        return_1m=0,
        return_3m=0,
        return_6m=0,
        drawdown_52w=0,
        signal_score=score,
        signal_label="neutral",
        reasons=("test",),
    )


def volatility(regime: str = "normal") -> VolatilityMetrics:
    return VolatilityMetrics("^VIX", date(2025, 1, 1), 18, 17, regime)


class AllocationTests(unittest.TestCase):
    def test_allocates_base_dollars_and_caps_reserve(self) -> None:
        config = AppConfig(
            contribution_per_asset=1000,
            runs_per_month=("beginning", "middle"),
            reserve_cash_per_run=750,
            default_strategy="mean_reversion",
            volatility_symbol="^VIX",
            lookback_years=5,
            tilt_strength=0.12,
            max_monthly_shift=0.15,
            assets=(
                AssetConfig("VGT", "VGT", 0.34, 0.15, 0.6),
                AssetConfig("VTI", "VTI", 0.33, 0.15, 0.6),
                AssetConfig("VOO", "VOO", 0.33, 0.15, 0.6),
            ),
        )

        allocations = allocate(config, [metric("VGT", 1), metric("VTI", 0), metric("VOO", -1)], volatility(), "mean_reversion")

        self.assertTrue(all(item.base_dollars == 1000 for item in allocations))
        self.assertLessEqual(sum(item.reserve_dollars for item in allocations), 750)
        self.assertAlmostEqual(sum(item.total_dollars for item in allocations), 3750.0, places=2)
        self.assertAlmostEqual(sum(item.final_weight for item in allocations), 1.0, places=6)
        self.assertGreater(allocations[0].total_dollars, allocations[2].total_dollars)

    def test_allocates_all_three_strategies(self) -> None:
        config = AppConfig(
            contribution_per_asset=1000,
            runs_per_month=("beginning", "middle"),
            reserve_cash_per_run=750,
            default_strategy="mean_reversion",
            volatility_symbol="^VIX",
            lookback_years=5,
            tilt_strength=0.12,
            max_monthly_shift=0.15,
            assets=(
                AssetConfig("VGT", "VGT", 0.34, 0.15, 0.6),
                AssetConfig("VTI", "VTI", 0.33, 0.15, 0.6),
                AssetConfig("VOO", "VOO", 0.33, 0.15, 0.6),
            ),
        )

        allocations = allocate_all_strategies(
            config, [metric("VGT", 1), metric("VTI", 0), metric("VOO", -1)], volatility("elevated")
        )

        self.assertEqual(set(allocations), {"dip_uptrend", "momentum", "mean_reversion"})
        self.assertLessEqual(sum(item.reserve_dollars for item in allocations["momentum"]), 750 * 0.7)


if __name__ == "__main__":
    unittest.main()
