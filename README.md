# AI Portfolio Framework

Standalone dashboard for the “trusted execution of intelligence” portfolio framework.

The project keeps the thesis, source-linked dashboard, and $1,000 public paper portfolio in
one clean repo. It is a research and review artifact, not investment, tax, legal, or financial
advice.

## Structure

- `site/`: static website served by GitHub Pages.
- `data/manual/`: versioned framework inputs and initial portfolio lot seed.
- `data/portfolio/`: daily portfolio history committed by the workflow.
- `src/ai_portfolio_framework/`: standalone refresh, build, and validation code.
- `docs/`: design and methodology notes.
- `.github/workflows/daily-pages.yml`: scheduled morning refresh and Pages deploy.

## Local Commands

```bash
uv sync --extra dev
uv run python -m scripts.update_portfolio
uv run python -m scripts.build_site
uv run python -m scripts.validate_site --site-dir public --require-portfolio
uv run ruff check .
uv run pytest
```

Preview the built site:

```bash
python3 -m http.server 8766 -d public
```

Open `http://127.0.0.1:8766/`.

## Portfolio Model

The tracker reads fixed quantities from `data/manual/ai_portfolio_lots.json`, fetches the
latest available Yahoo Finance prices, converts `000660.KS` from KRW to USD using `KRW=X`,
updates CSV history, writes `site/portfolio-data.json`, and regenerates PNG plots.

Because markets close on weekends and holidays, the “today” refresh uses the latest available
market price at or before the run date.

