from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.pipeline.extract import extract_from_ista
from src.pipeline.normalize import normalize
from src.pipeline.report_charts import generate_chart_assets
from src.pipeline.report_data import build_sections, enrich_records
from src.pipeline.report_csv import combined_usage_csv_path, write_all_usage_csv
from src.pipeline.report_render import (
    build_index_context,
    build_year_file_context,
    render_index_markdown,
    render_year_report_markdown,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_fixture_payload(fixture_path: Path) -> dict[str, Any]:
    raw = fixture_path.read_text(encoding="utf-8")
    data = json.loads(raw)

    if isinstance(data, dict) and "items" not in data and data:
        first_key = next(iter(data))
        if isinstance(data[first_key], dict) and "consumption" in data[first_key]:
            return {
                "uuids": list(data.keys()),
                "items": {
                    uuid: {"consumption": payload["consumption"], "details": payload.get("details", {})}
                    for uuid, payload in data.items()
                },
            }

    return data


def main() -> int:
    load_dotenv()

    fixture = os.getenv("REPORT_FIXTURE_JSON")
    if fixture:
        payload = load_fixture_payload(Path(fixture))
        records = normalize(payload)
    else:
        payload = extract_from_ista()
        records = normalize(payload)

    root = repo_root()
    enriched = enrich_records(records)

    charts_dir = root / "assets" / "charts"
    chart_paths = generate_chart_assets(enriched, charts_dir)

    years = sorted({int(r["year"]) for r in enriched}, reverse=True)
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    sections_all = build_sections(enriched, chart_paths)
    sections_by_year = {int(s["year"]): s for s in sections_all}

    write_all_usage_csv(sections_all, combined_usage_csv_path(root))

    written_years = []
    for year in years:
        section = sections_by_year.get(year)
        if section is None:
            raise RuntimeError(f"No section built for year {year}")
        ctx_year = build_year_file_context(section, generated_at)
        year_path = root / f"REPORT_{year}.md"
        year_path.write_text(render_year_report_markdown(root, ctx_year) + "\n", encoding="utf-8")
        written_years.append(year)

    index_ctx = build_index_context(enriched, years, generated_at)
    (root / "REPORT.md").write_text(render_index_markdown(root, index_ctx) + "\n", encoding="utf-8")

    print(
        "Report:",
        {"index": str(root / "REPORT.md"), "year_files": written_years, "chart_count": len(chart_paths), "rows": len(enriched)},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
