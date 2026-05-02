from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.pipeline.report_notes import build_usage_notes
from src.pipeline.schemas import ReportIndexContext, UsageNote, YearReportContext, YearSection


def _jinja_env(repo_root: Path) -> Environment:
    templates_dir = repo_root / "templates"
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_index_markdown(
    repo_root: Path,
    context: ReportIndexContext,
    *,
    prefix_gen: str = "",
    prefix_root: str = "",
) -> str:
    return _jinja_env(repo_root).get_template("report_index.md.j2").render(
        **context,
        prefix_gen=prefix_gen,
        prefix_root=prefix_root,
    )


def render_year_report_markdown(
    repo_root: Path,
    context: YearReportContext,
    *,
    prefix_gen: str = "",
    prefix_root: str = "",
) -> str:
    return _jinja_env(repo_root).get_template("report_year.md.j2").render(
        **context,
        prefix_gen=prefix_gen,
        prefix_root=prefix_root,
    )


def build_index_context(
    years: list[int],
    generated_at: str,
    *,
    years_with_usage_notes: list[int] | None = None,
) -> ReportIndexContext:
    ywn = sorted({int(y) for y in (years_with_usage_notes or [])}, reverse=True)
    return {
        "generated_at": generated_at,
        "years": years,
        "years_with_usage_notes": ywn,
    }


def build_year_file_context(
    section: YearSection,
    generated_at: str,
    *,
    usage_notes: list[UsageNote] | None = None,
) -> YearReportContext:
    yr = int(section["year"])
    notes = usage_notes if usage_notes is not None else build_usage_notes(section["usage_rows"])
    return {
        "generated_at": generated_at,
        "year": yr,
        "section": section,
        "usage_notes": notes,
    }
