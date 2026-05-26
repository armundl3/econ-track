# AGENTS.md

## Project
Econ Track is a personal finance dashboard for tracking ETF trend signals and rule-based monthly DCA allocations.

## Commands
- Python tests: `python -m unittest discover -s tests`
- Generate data: `python -m econ_track.cli generate --config config/funds.json --output frontend/public/data/latest.json`
- Frontend install: `npm --prefix frontend install`
- Frontend build: `npm --prefix frontend run build`

## Coding Guidelines
- Keep changes minimal, focused, and consistent with the existing project structure.
- Fix root causes rather than masking symptoms.
- Avoid unrelated refactors, renames, formatting churn, or dependency changes.
- Prefer standard-library Python unless a dependency clearly pays for itself.
- Keep finance logic in the Python package so it can later move behind a FastAPI service without rewriting calculations.

## Testing And Verification
- Run the narrowest relevant validation after each change.
- For backend changes, run `python -m unittest discover -s tests`.
- For frontend changes, run `npm --prefix frontend run build`.
- For generated data changes, run the data generation command and inspect the output schema.
- If validation cannot run because of missing dependencies, credentials, services, or network access, report that clearly.

## Git
- Use git incrementally and atomically.
- Keep commits focused and avoid mixing unrelated changes in one commit.
- Keep `main` clean and deployable; do implementation work on feature branches.
- Do not commit unless explicitly asked or the project workflow requires incremental implementation commits.
- Do not revert user changes unless explicitly asked.
