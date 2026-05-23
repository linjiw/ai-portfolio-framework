# Portfolio Tracker

This tracker turns the framework allocation into a public $1,000 paper portfolio
on GitHub Pages.

## Persistence Model

The initial lots are versioned so the cost basis does not reset on every GitHub
Actions run:

```text
data/manual/ai_portfolio_lots.json
```

Daily history is also versioned:

```text
data/portfolio/ai_portfolio_summary.csv
data/portfolio/ai_portfolio_snapshots.csv
```

The workflow commits changed history rows back to `main` after a successful
refresh/test pass. The generated site JSON and plot images are rebuilt each run
and published through the GitHub Pages artifact.

## Daily Update

The daily website workflow runs:

```bash
uv run python -m scripts.update_portfolio
uv run python -m scripts.build_site
uv run python -m scripts.validate_site --site-dir public --require-portfolio
```

Portfolio pricing uses Yahoo Finance directly in the standalone package.
`000660.KS` is priced in KRW and converted to USD with `KRW=X`. The `CASH` row
stays fixed at USD cash. Weekend and holiday runs use the latest available close
at or before the run date.

## Generated Site Files

These files are generated and gitignored locally, then included in the Pages
artifact:

```text
site/portfolio-data.json
site/portfolio/portfolio-value.png
site/portfolio/portfolio-allocation.png
```

The public dashboard reads the generated JSON from the same GitHub Pages site:

```text
portfolio-data.json
```

## Manual Commands

Update the portfolio locally:

```bash
uv run python -m scripts.update_portfolio
```

Reset the initial cost basis only when intentionally starting a new paper
portfolio:

```bash
uv run python -m scripts.update_portfolio --force-reinitialize
```

After reinitializing, commit the updated `data/manual/ai_portfolio_lots.json`.
