# AI Portfolio Framework

Standalone dashboard for the “trusted execution of intelligence” portfolio framework.

The project keeps the thesis, source-linked dashboard, and $1,000 public paper portfolio in
one clean repo. It is a research and review artifact, not investment, tax, legal, or financial
advice.

## Published Site

GitHub Pages is configured to publish the generated static dashboard:

```text
https://linjiw.github.io/ai-portfolio-framework/
```

The repo uses GitHub Actions rather than a committed `public/` folder so the same workflow can
refresh prices, validate the artifact, run tests, and deploy Pages from one auditable path.

## Structure

- `site/`: static website served by GitHub Pages.
- `data/manual/`: versioned framework inputs and initial portfolio lot seed.
- `data/portfolio/`: daily portfolio history committed by the workflow.
- `src/ai_portfolio_framework/`: standalone refresh, build, and validation code.
- `docs/`: design, methodology, and decision-process notes.
- `.github/workflows/daily-pages.yml`: scheduled morning refresh and Pages deploy.

## Portfolio Decision Process

The portfolio starts from the framework question: if intelligence keeps getting cheaper, which
public companies control trusted execution around it? Each holding must map to at least one
control-right layer: capacity, cost, authority, outcome verification, physical AI optionality, or
risk-control cash.

Current sizing reflects five roles:

- Core compounders: 57% for enterprise distribution, model infrastructure, authority, and
  workflow control.
- Bottleneck cyclicals: 18% for HBM, accelerators, foundry, packaging, and AI factory constraints.
- Vertical verifiers: 8% for ratings, data, analytics, and regulated workflow outcome control.
- Optionality: 7% for semiconductor test and physical-AI exposure.
- Cash: 10% as dry powder and regime-change risk control.

Signals are review prompts, not automatic trades. Capability, economics, trust, and valuation
gates are documented in `docs/decision_process.md` and surfaced on the website.

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
