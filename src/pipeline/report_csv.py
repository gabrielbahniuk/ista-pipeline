from __future__ import annotations

import csv
from pathlib import Path

from src.pipeline.schemas import UsageTableRow, YearSection

COMBINED_CSV_FILENAME = "ista_usage_all.csv"


def _csv_float_cell(v: float | None) -> str:
    if v is None:
        return ""
    if abs(float(v) - round(float(v))) < 1e-9:
        return str(int(round(float(v))))
    return f"{float(v):.4f}".rstrip("0").rstrip(".") or "0"


def combined_usage_csv_path(repo_root: Path) -> Path:
    return repo_root / "generated" / "exports" / COMBINED_CSV_FILENAME


def _usage_row_dict(row: UsageTableRow, year: int) -> dict[str, str]:
    cv = row.get("consumption_value")
    cz = row.get("cost_value")
    return {
        "year": str(year),
        "month": str(int(row["month"])),
        "metric": str(row["metric_label"]),
        "consumption_value": _csv_float_cell(float(cv) if cv is not None else None),
        "consumption_unit": ""
        if row.get("consumption_unit") is None
        else str(row["consumption_unit"]),
        "cost_eur": _csv_float_cell(float(cz) if cz is not None else None),
    }


def write_all_usage_csv(sections: list[YearSection], path: Path) -> Path:
    """One CSV for all years: same columns as the per-year usage tables, sections in year order (newest first).

    UTF-8; period as decimal separator.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        "year",
        "month",
        "metric",
        "consumption_value",
        "consumption_unit",
        "cost_eur",
    )

    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for section in sections:
            year = int(section["year"])
            for row in section.get("usage_rows") or []:
                w.writerow(_usage_row_dict(row, year))

    return path

