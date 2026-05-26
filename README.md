# Econ Track

A static GitHub Pages dashboard for tracking ETF trend signals and monthly DCA allocation suggestions.

The free v1 architecture uses GitHub Actions as the scheduled data engine and GitHub Pages as the static host. Python fetches public market data, computes metrics and allocations, writes static JSON, and a React + Vite frontend renders the dashboard.

## Local Commands

```bash
python -m unittest discover -s tests
python -m econ_track.cli generate --config config/funds.json --output frontend/public/data/latest.json
npm --prefix frontend install
npm --prefix frontend run build
```

## Disclaimer

This project is for personal education and research. It is not financial advice.
