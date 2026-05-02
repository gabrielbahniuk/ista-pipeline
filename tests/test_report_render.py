from pathlib import Path

from src.pipeline.report_data import build_sections, enrich_records
from src.pipeline.report_render import (
    build_index_context,
    build_year_file_context,
    render_index_markdown,
    render_year_report_markdown,
)


def test_render_year_report_contains_tables_and_title():
    repo_root = Path(__file__).resolve().parents[1]
    records = enrich_records(
        [
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating", "value": 165.0, "unit": "units"},
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating_cost", "value": 95.0, "unit": "EUR"},
        ]
    )
    sections = build_sections(records, chart_paths={})
    ctx = build_year_file_context(sections[0], "2099-01-01 00:00:00 UTC")
    markdown = render_year_report_markdown(repo_root, ctx)

    assert "# ISTA EcoTrend 2026" in markdown
    assert "docs/images/csv-report.svg" not in markdown
    assert "ista_usage_all" not in markdown
    assert "## Consumption & costs" in markdown
    assert "| 3 | Heating | 165.0 | units | 95.0 |" in markdown


def test_render_index_lists_years_and_summary():
    repo_root = Path(__file__).resolve().parents[1]
    records = enrich_records(
        [
            {"period_end": "2025-12-31T23:59:59+00:00", "metric": "heating", "value": 1.0, "unit": "units"},
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating", "value": 2.0, "unit": "units"},
        ]
    )
    ctx = build_index_context(records, years=[2026, 2025], generated_at="2099-01-01 00:00:00 UTC")
    md = render_index_markdown(repo_root, ctx)

    assert "[Report 2026](REPORT_2026.md)" in md
    assert "[Report 2025](REPORT_2025.md)" in md
    assert "exports/ista_usage_all.csv" in md
    assert "CSV Report" in md and "docs/images/csv-report.svg" in md
    assert "## By year" in md
    assert "## Recent entries" in md
