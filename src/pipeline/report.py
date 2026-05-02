from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src.pipeline.extract import extract_from_ista
from src.pipeline.normalize import normalize
from src.pipeline.report_charts import generate_chart_assets
from src.pipeline.report_data import build_sections, enrich_records
from src.pipeline.report_csv import combined_usage_csv_path, write_all_usage_csv
from src.pipeline.report_notes import build_usage_notes
from src.pipeline.readme_nav import patch_report_readmes
from src.pipeline.report_render import (
    build_index_context,
    build_year_file_context,
    render_index_markdown,
    render_year_report_markdown,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


_GENERATED_SUBDIR = "generated"
_REPORTS_SUBDIRNAME = "reports"
_REPORT_INDEX_DOC = "REPORT.md"
# Markdown under generated/reports/ → siblings under generated/ (../) vs repo root (../../)
_MARKDOWN_PREFIX_GEN = "../"
_MARKDOWN_PREFIX_REPO_ROOT = "../../"


def main() -> int:
    load_dotenv()

    payload = extract_from_ista()
    records = normalize(payload)

    root = repo_root()
    reports_dir = root / _GENERATED_SUBDIR / _REPORTS_SUBDIRNAME
    reports_dir.mkdir(parents=True, exist_ok=True)
    enriched = enrich_records(records)

    charts_dir = root / _GENERATED_SUBDIR / "assets"
    chart_paths = generate_chart_assets(enriched, charts_dir)

    years = sorted({int(r["year"]) for r in enriched}, reverse=True)
    generated_at = datetime.now(ZoneInfo("Europe/Berlin")).strftime("%d.%m.%Y %H:%M")

    sections_all = build_sections(enriched, chart_paths)
    sections_by_year = {int(s["year"]): s for s in sections_all}

    write_all_usage_csv(sections_all, combined_usage_csv_path(root))

    usage_notes_by_year = {int(s["year"]): build_usage_notes(s["usage_rows"]) for s in sections_all}
    years_with_usage_notes = sorted(
        (y for y, notes in usage_notes_by_year.items() if notes), reverse=True
    )

    written_years = []
    for year in years:
        section = sections_by_year.get(year)
        if section is None:
            raise RuntimeError(f"No section built for year {year}")
        ctx_year = build_year_file_context(
            section, generated_at, usage_notes=usage_notes_by_year[year]
        )
        year_path = reports_dir / f"{year}.md"
        year_path.write_text(
            render_year_report_markdown(
                root,
                ctx_year,
                prefix_gen=_MARKDOWN_PREFIX_GEN,
                prefix_root=_MARKDOWN_PREFIX_REPO_ROOT,
            )
            + "\n",
            encoding="utf-8",
        )
        written_years.append(year)

    index_ctx = build_index_context(
        years,
        generated_at,
        years_with_usage_notes=years_with_usage_notes,
    )
    index_path = reports_dir / _REPORT_INDEX_DOC
    index_path.write_text(
        render_index_markdown(
            root,
            index_ctx,
            prefix_gen=_MARKDOWN_PREFIX_GEN,
            prefix_root=_MARKDOWN_PREFIX_REPO_ROOT,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "Report:",
        {"index": str(index_path), "year_files": written_years, "chart_count": len(chart_paths), "rows": len(enriched)},
    )
    if patch_report_readmes(root):
        print("README:", {"nav": "updated"})
    else:
        print(
            "README: nav markers skipped (missing README.md / README.de.md or <!-- ista-report-nav --> markers)",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
