from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from src.pipeline.schemas import (
    EnrichedRecord,
    FigureRef,
    NormalizedRecord,
    ReportTableRow,
    SummaryRow,
    UsageTableRow,
    YearSection,
)

METRIC_LABELS: dict[str, str] = {
    "heating": "Heating",
    "hot_water": "Warm water",
    "water": "Water",
    "heating_cost": "Heating (cost)",
    "hot_water_cost": "Warm water (cost)",
}

# Consumption chart key pairs with sibling cost metric (same chart, EUR in bar labels).
CHART_METRIC_PAIRS: list[tuple[str, str, str]] = [
    ("heating", "heating_cost", "Heating"),
    ("hot_water", "hot_water_cost", "Warm water"),
]


def _parse_year_month(period_end: str | None) -> tuple[int, int] | None:
    if not period_end or not isinstance(period_end, str):
        return None
    normalized = period_end.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    return dt.year, dt.month


def enrich_records(records: list[NormalizedRecord]) -> list[EnrichedRecord]:
    out: list[EnrichedRecord] = []
    for r in records:
        pe = r.get("period_end")
        ym = None if pe is None else _parse_year_month(str(pe))
        if ym is None:
            continue
        year, month = ym
        enriched: EnrichedRecord = {**r, "year": year, "month": month}
        out.append(enriched)
    return out


def _is_cost(metric: str) -> bool:
    return metric.endswith("_cost")


def _is_benchmark(metric: str) -> bool:
    return metric.endswith("_benchmark")


def _metric_label(metric: str) -> str:
    return METRIC_LABELS.get(metric, metric)


def _row_index(rows: list[ReportTableRow]) -> dict[tuple[int, str], ReportTableRow]:
    return {(r["month"], r["metric_key"]): r for r in rows}


def _merge_usage_rows(
    consumption_rows: list[ReportTableRow], cost_rows: list[ReportTableRow]
) -> list[UsageTableRow]:
    cons_ix = _row_index(consumption_rows)
    cost_ix = _row_index(cost_rows)
    months = {m for (m, _) in cons_ix} | {m for (m, _) in cost_ix}
    known_cons = {p[0] for p in CHART_METRIC_PAIRS}
    known_cost = {p[1] for p in CHART_METRIC_PAIRS}

    merged: list[UsageTableRow] = []
    for month in sorted(months, reverse=True):
        for consumption_key, cost_key, label in CHART_METRIC_PAIRS:
            c = cons_ix.get((month, consumption_key))
            k = cost_ix.get((month, cost_key))
            if c is None and k is None:
                continue
            merged.append(
                {
                    "month": month,
                    "metric_label": label,
                    "consumption_value": None if c is None else c["value"],
                    "consumption_unit": None if c is None else c["unit"],
                    "cost_value": None if k is None else k["value"],
                    "cost_unit": None if k is None else k["unit"],
                }
            )

    orphans: list[UsageTableRow] = []
    for row in consumption_rows:
        if row["metric_key"] in known_cons:
            continue
        orphans.append(
            {
                "month": row["month"],
                "metric_label": row["metric_label"],
                "consumption_value": row["value"],
                "consumption_unit": row["unit"],
                "cost_value": None,
                "cost_unit": None,
            }
        )
    for row in cost_rows:
        if row["metric_key"] in known_cost:
            continue
        orphans.append(
            {
                "month": row["month"],
                "metric_label": row["metric_label"],
                "consumption_value": None,
                "consumption_unit": None,
                "cost_value": row["value"],
                "cost_unit": row["unit"],
            }
        )
    orphans.sort(key=lambda x: (-x["month"], x["metric_label"]))
    return merged + orphans


def build_sections(
    enriched: list[EnrichedRecord], chart_paths: dict[tuple[int, str], str]
) -> list[YearSection]:
    by_year: dict[int, dict[str, list[ReportTableRow]]] = defaultdict(
        lambda: {"consumption": [], "costs": []}
    )
    for r in enriched:
        year = r["year"]
        metric = str(r["metric"])
        if _is_benchmark(metric):
            continue
        bucket = by_year[year]["costs" if _is_cost(metric) else "consumption"]
        row: ReportTableRow = {
            "month": int(r["month"]),
            "metric_key": metric,
            "metric_label": _metric_label(metric),
            "value": float(r["value"]),
            "unit": str(r["unit"]),
        }
        bucket.append(row)

    def sort_bucket(rows: list[ReportTableRow]) -> list[ReportTableRow]:
        return sorted(rows, key=lambda x: (-x["month"], x["metric_key"]))

    sections: list[YearSection] = []
    for year in sorted(by_year.keys(), reverse=True):
        consumption_rows = sort_bucket(by_year[year]["consumption"])
        cost_rows = sort_bucket(by_year[year]["costs"])
        usage_rows = _merge_usage_rows(consumption_rows, cost_rows)

        figures: list[FigureRef] = []
        for consumption_key, _cost_key, chart_title in CHART_METRIC_PAIRS:
            path = chart_paths.get((year, consumption_key))
            if path:
                figures.append({"title": chart_title, "path": path, "metric_key": consumption_key})

        sections.append(
            {
                "year": year,
                "figures": figures,
                "usage_rows": usage_rows,
            }
        )

    return sections


def compute_chart_series(enriched: list[EnrichedRecord]) -> dict[tuple[int, str], tuple[list[int], list[float]]]:
    """For each year+metric build sorted month/value series (best single value per month)."""
    buckets: dict[tuple[int, str], dict[int, float]] = defaultdict(dict)
    for r in enriched:
        key = (int(r["year"]), str(r["metric"]))
        buckets[key][int(r["month"])] = float(r["value"])

    out: dict[tuple[int, str], tuple[list[int], list[float]]] = {}
    for key, months_map in buckets.items():
        months = sorted(months_map.keys())
        values = [months_map[m] for m in months]
        out[key] = (months, values)
    return out


def report_summary_recent(enriched: list[EnrichedRecord], max_rows: int = 12) -> list[SummaryRow]:
    """Latest rows across all years/metrics for preview table."""
    if not enriched:
        return []

    def sort_key(r: EnrichedRecord) -> tuple[int, int, str]:
        return int(r["year"]), int(r["month"]), str(r["metric"])

    ranked = sorted(enriched, key=sort_key, reverse=True)
    ranked_nb = [r for r in ranked if not _is_benchmark(str(r["metric"]))]
    summary: list[SummaryRow] = []
    for r in ranked_nb[:max_rows]:
        summary.append(
            {
                "year": r["year"],
                "month": r["month"],
                "metric_label": _metric_label(str(r["metric"])),
                "value": float(r["value"]),
                "unit": str(r["unit"]),
            }
        )
    return summary
