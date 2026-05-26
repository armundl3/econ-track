from __future__ import annotations

import json
import time
from datetime import UTC, date, datetime
from urllib.parse import quote
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from econ_track.models import PricePoint


class MarketDataError(RuntimeError):
    """Raised when market data cannot be fetched or parsed safely."""
    pass


class YahooChartProvider:
    base_url = "https://query2.finance.yahoo.com/v8/finance/chart/{symbol}"

    def __init__(self, user_agent: str = "Mozilla/5.0 econ-track/0.1") -> None:
        """Create a Yahoo chart provider with a configurable User-Agent."""
        self.user_agent = user_agent

    def fetch_daily(self, symbol: str, lookback_years: int) -> list[PricePoint]:
        """Fetch daily closing prices for a symbol over the configured lookback."""
        encoded_symbol = quote(symbol.upper(), safe="")
        url = f"{self.base_url.format(symbol=encoded_symbol)}?range={lookback_years}y&interval=1d"
        request = Request(url, headers={"User-Agent": self.user_agent, "Accept": "application/json"})
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise MarketDataError(f"failed to fetch {symbol}: {exc}") from exc
        return parse_yahoo_chart(symbol, payload)


def parse_yahoo_chart(symbol: str, payload: dict) -> list[PricePoint]:
    """Parse Yahoo chart JSON into sorted daily closing price points."""
    error = payload.get("chart", {}).get("error")
    if error:
        raise MarketDataError(f"{symbol} returned provider error: {error}")

    results = payload.get("chart", {}).get("result") or []
    if not results:
        raise MarketDataError(f"{symbol} returned no chart result")

    result = results[0]
    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []

    points: list[PricePoint] = []
    for timestamp, close in zip(timestamps, closes):
        if close is None:
            continue
        day = datetime.fromtimestamp(int(timestamp), tz=UTC).date()
        points.append(PricePoint(date=day, close=float(close)))

    if not points:
        raise MarketDataError(f"{symbol} returned no closing prices")
    return sorted(points, key=lambda point: point.date)


def fetch_all(provider: YahooChartProvider, symbols: list[str], lookback_years: int) -> dict[str, list[PricePoint]]:
    """Fetch daily prices for each symbol with a small delay between requests."""
    prices: dict[str, list[PricePoint]] = {}
    for index, symbol in enumerate(symbols):
        if index:
            time.sleep(0.5)
        prices[symbol] = provider.fetch_daily(symbol, lookback_years)
    return prices
