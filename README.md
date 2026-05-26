# Econ Track

A static GitHub Pages dashboard for tracking ETF trend signals and monthly DCA allocation suggestions.

The free v1 architecture uses GitHub Actions as the scheduled data engine and GitHub Pages as the static host. Python fetches public market data, computes metrics and allocations, writes static JSON, and a React + Vite frontend renders the dashboard.

## Local Commands

```bash
uv run python -m unittest discover -s tests
uv run python -m econ_track.cli generate --config config/funds.json --output frontend/public/data/latest.json
npm --prefix frontend install
npm --prefix frontend run build
```

## Build System

- Python is managed with `uv`.
- Python packaging uses the `setuptools` PEP 517 backend declared in `pyproject.toml`.
- The frontend is built with Vite.
- GitHub Actions runs tests, refreshes static data, and deploys the built site to GitHub Pages.

## Disclaimer

This project is for personal education and research. It is not financial advice.
