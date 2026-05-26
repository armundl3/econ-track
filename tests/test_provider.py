import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from econ_track.provider import parse_yahoo_chart


class ProviderTests(unittest.TestCase):
    def test_parse_yahoo_chart_skips_missing_closes(self) -> None:
        payload = {
            "chart": {
                "result": [
                    {
                        "timestamp": [1704153600, 1704240000, 1704326400],
                        "indicators": {"quote": [{"close": [100.0, None, 103.0]}]},
                    }
                ],
                "error": None,
            }
        }

        points = parse_yahoo_chart("VGT", payload)

        self.assertEqual(len(points), 2)
        self.assertEqual(points[-1].close, 103.0)


if __name__ == "__main__":
    unittest.main()
