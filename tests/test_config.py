import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from econ_track.config import load_config


class ConfigTests(unittest.TestCase):
    def test_loads_default_config(self) -> None:
        config = load_config("config/funds.json")

        self.assertEqual(config.contribution_per_asset, 1000)
        self.assertEqual(config.runs_per_month, ("beginning", "middle"))
        self.assertEqual(config.reserve_cash_per_run, 750)
        self.assertEqual(config.default_strategy, "mean_reversion")
        self.assertEqual(config.volatility_symbol, "^VIX")
        self.assertEqual([asset.symbol for asset in config.assets], ["VGT", "VTI", "VOO"])

    def test_rejects_weights_that_do_not_sum_to_one(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write(
                """
                {
                  "contribution_per_asset": 1000,
                  "assets": [
                    {"symbol": "VGT", "base_weight": 0.7, "min_weight": 0.1, "max_weight": 0.8},
                    {"symbol": "VTI", "base_weight": 0.2, "min_weight": 0.1, "max_weight": 0.8}
                  ]
                }
                """
            )
            path = handle.name

        with self.assertRaises(ValueError):
            load_config(path)


if __name__ == "__main__":
    unittest.main()
