from pathlib import Path

from src.pipeline.report_data import build_sections, enrich_records
from src.pipeline.report_render import (
    build_index_context,
    build_year_file_context,
    render_index_markdown,
    render_year_report_markdown,
)

_PREFIX_GEN = "../"
_PREFIX_ROOT = "../../"


def test_render_year_report_contains_tables_and_title():
    repo_root = Path(__file__).resolve().parents[1]
    records = enrich_records(
        [
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating", "value": 165.0, "unit": "units"},
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating_cost", "value": 95.0, "unit": "EUR"},
        ]
    )
    sections = build_sections(records, chart_paths={})
    ctx = build_year_file_context(sections[0], "01.01.2099 00:00")
    markdown = render_year_report_markdown(
        repo_root, ctx, prefix_gen=_PREFIX_GEN, prefix_root=_PREFIX_ROOT
    )

    assert "# ISTA EcoTrend 2026" in markdown
    assert "docs/images/csv-report.svg" not in markdown
    assert "ista_usage_all" not in markdown
    assert "## Consumption & costs" in markdown
    assert "| 3 | Heating | 165.0 | units | 95.0 |" in markdown


def test_render_index_lists_years_without_recent_table():
    repo_root = Path(__file__).resolve().parents[1]
    ctx = build_index_context(years=[2026, 2025], generated_at="01.01.2099 00:00")
    md = render_index_markdown(
        repo_root, ctx, prefix_gen=_PREFIX_GEN, prefix_root=_PREFIX_ROOT
    )

    assert "[Report 2026](2026.md)" in md
    assert "[Report 2025](2025.md)" in md
    assert "../exports/ista_usage_all.csv" in md
    assert "CSV Report" in md and "../../docs/images/csv-report.svg" in md
    assert "## By year" in md
    assert "## Recent entries" not in md


def test_render_year_shows_cost_note_when_heating_sparse():
    repo_root = Path(__file__).resolve().parents[1]
    records = enrich_records(
        [
            {"period_end": "2025-12-31T23:59:59+00:00", "metric": "heating", "value": 1.0, "unit": "kWh"},
            {"period_end": "2025-12-31T23:59:59+00:00", "metric": "heating_cost", "value": 140.0, "unit": "EUR"},
        ]
    )
    sections = build_sections(records, chart_paths={})
    ctx = build_year_file_context(sections[0], "01.01.2099 00:00")
    md = render_year_report_markdown(
        repo_root, ctx, prefix_gen=_PREFIX_GEN, prefix_root=_PREFIX_ROOT
    )

    assert "⚠️ <strong>Anomaly notes</strong> · 1" in md
    assert "Months below often reflect" not in md
    assert "**Dec · Heating**" in md


def test_render_index_shows_banner_when_flags_present():
    repo_root = Path(__file__).resolve().parents[1]
    md = render_index_markdown(
        repo_root,
        build_index_context(
            years=[2025],
            generated_at="01.01.2099 00:00",
            years_with_usage_notes=[2025],
        ),
        prefix_gen=_PREFIX_GEN,
        prefix_root=_PREFIX_ROOT,
    )

    assert "Anomaly detected: Billed vs. Used" in md
    assert "[Report 2025](2025.md)" in md
