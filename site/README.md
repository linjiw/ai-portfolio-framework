# AI Framework Website

Static dashboard for the trusted-execution framework.

Open:

```bash
site/index.html
```

The site has no build step. Research content lives in `research-data.js`; layout
and interaction live in `styles.css` and `app.js`.

Published Pages target:

```text
https://linjiw.github.io/ai-portfolio-framework/
```

The dashboard includes the portfolio, decision process, research monitor, memory
watchlist, control-right map, signals, research notes, and source provenance.

The personal performance panel reads generated `portfolio-data.json`. Generate
it from the repo root:

```bash
uv run python -m scripts.update_portfolio
uv run python -m scripts.build_research_monitor
uv run python -m scripts.build_site
```

The monitor is intentionally rules-first: it reads config YAML plus
`data/decision_log.yml`, `data/evidence_log.yml`, and
`data/thesis_changelog.yml`; emits `research-monitor-data.json` and
`provenance-coverage.json`; generates a scored review queue; and keeps LLMs out
of the portfolio-action path.

The daily GitHub workflow publishes the generated portfolio JSON and plot images
to GitHub Pages.

Validate the data contract:

```bash
uv run python -m scripts.validate_site --site-dir public --require-portfolio
```

Implementation and design-system notes for review:

```bash
docs/website_design.md
```
