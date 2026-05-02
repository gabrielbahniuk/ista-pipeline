"""Inject report links + “last updated” into README markers (CI and local runs)."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_BERLIN = ZoneInfo("Europe/Berlin")

MARKER_BEGIN = "<!-- ista-report-nav:begin -->"
MARKER_END = "<!-- ista-report-nav:end -->"
_BLOCK_PATTERN = re.compile(
    re.escape(MARKER_BEGIN) + r".*?" + re.escape(MARKER_END),
    re.DOTALL,
)


def _open_report_heading(*, label: str) -> str:
    """Repo-root README banner → generated index (avoid naming it README.md under generated/)."""
    return f'<h3 align="center"><a href="./generated/reports/REPORT.md">{label}</a></h3>'


def _build_block_en(generated_at: str) -> str:
    return (
        f"{MARKER_BEGIN}\n"
        f'{_open_report_heading(label="Open Report")}\n'
        f'<p align="center"><sup>Last updated · {generated_at}</sup></p>\n'
        f"{MARKER_END}"
    )


def _build_block_de(generated_at: str) -> str:
    return (
        f"{MARKER_BEGIN}\n"
        f'{_open_report_heading(label="Report öffnen")}\n'
        f'<p align="center"><sup>Zuletzt erstellt · {generated_at}</sup></p>\n'
        f"{MARKER_END}"
    )


def _patch_file(path: Path, new_block: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER_BEGIN not in text or MARKER_END not in text:
        return False
    new_text, n = _BLOCK_PATTERN.subn(new_block, text, count=1)
    if n != 1:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def _format_generated_at_berlin() -> str:
    """DD.MM.YYYY HH:MM in Europe/Berlin (CET/CEST)."""
    return datetime.now(_BERLIN).strftime("%d.%m.%Y %H:%M")


def patch_report_readmes(root: Path) -> bool:
    """Return True only if both README files were patched."""
    generated_at = _format_generated_at_berlin()
    en = root / "README.md"
    de = root / "README.de.md"
    if not en.is_file() or not de.is_file():
        return False
    return _patch_file(en, _build_block_en(generated_at)) and _patch_file(
        de, _build_block_de(generated_at)
    )


def _repo_root_here() -> Path:
    """Repository root when this file lives under src/pipeline/."""
    return Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    import sys

    raise SystemExit(0 if patch_report_readmes(_repo_root_here()) else 1)
