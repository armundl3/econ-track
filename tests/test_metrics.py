import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from econ_track.metrics import compute_metrics, compute_volatility
from econ_track.models import AssetConfig, PricePoint


class MetricsTests(unittest.TestCase):
    def test_computes_moving_averages_and_signal(self) -> None:
        start = date(2024, 1, 1)
        points = [PricePoint(start + timedelta(days=index), 100 + index * 0.5) for index in range(260)]
        asset = AssetConfig("VGT", "Vanguard Tech", 0.34, 0.15, 0.6)

        metrics = compute_metrics(asset, points)

        self.assertIsNotNone(metrics.sma_5)
        self.assertIsNotNone(metrics.sma_10)
        self.assertIsNotNone(metrics.sma_15)
        self.assertIsNotNone(metrics.sma_5_change)
        self.assertIsNotNone(metrics.sma_50)
        self.assertIsNotNone(metrics.sma_200)
        self.assertGreater(metrics.distance_sma_200 or 0, 0)
        self.assertIn(metrics.signal_label, {"overweight", "neutral", "underweight"})

    def test_classifies_volatility_regime(self) -> None:
        start = date(2024, 1, 1)
        points = [PricePoint(start + timedelta(days=index), 32.0) for index in range(30)]

        volatility = compute_volatility("^VIX", points)

        self.assertEqual(volatility.regime, "stressed")
        self.assertEqual(volatility.latest_close, 32.0)


if __name__ == "__main__":
    unittest.main()
