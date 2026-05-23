"""Project paths for the standalone AI portfolio framework."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
MANUAL_DIR = DATA_DIR / "manual"
PORTFOLIO_DATA_DIR = DATA_DIR / "portfolio"
REPORTS_DIR = PROJECT_ROOT / "reports"
SITE_DIR = PROJECT_ROOT / "site"
PUBLIC_DIR = PROJECT_ROOT / "public"


def ensure_directories() -> None:
    """Create the directories used by generated portfolio artifacts."""

    for path in (DATA_DIR, MANUAL_DIR, PORTFOLIO_DATA_DIR, REPORTS_DIR, SITE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def display_path(path: Path) -> str:
    """Return a repo-relative path where possible."""

    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)
