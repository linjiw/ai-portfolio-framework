# AI Framework Website

Static dashboard for the trusted-execution framework.

Open:

```bash
site/index.html
```

The site has no build step. Research content lives in `research-data.js`; layout
and interaction live in `styles.css` and `app.js`.

The personal performance panel reads generated `portfolio-data.json`. Generate
it from the repo root:

```bash
uv run python -m scripts.update_portfolio
uv run python -m scripts.build_site
```

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
