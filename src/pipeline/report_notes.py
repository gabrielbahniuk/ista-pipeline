from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from src.pipeline.schemas import UsageNote, UsageTableRow

_MONTH_ABBR = (
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)

# Baseline-driven rules. Absolute floors only avoid noisy notes on tiny amounts
# or sparse years where a meaningful yearly median cannot yet be computed.
_RATIO_MULTIPLIER = 3.0
_LOW_CONSUMPTION_SHARE = 0.45
_NO_CONS_COST_MULTIPLIER = 3.0
_MIN_RATIO_BASELINE_ROWS = 2
_MIN_COST_EUR = 35.0
_MIN_NO_CONS_COST_EUR = 20.0
_FALLBACK_HEATING_EUR_PER_KWH = 8.0
_FALLBACK_WARM_WATER_EUR_PER_M3 = 60.0
_FALLBACK_WARM_WATER_EUR_PER_L = 0.10


@dataclass(frozen=True)
class _MetricStats:
    ratio_median: float | None
    cost_median: float | None
    no_consumption_cost_median: float | None
    consumption_median: float | None
    ratio_count: int
    no_consumption_count: int


def _unit_key(unit: str | None) -> str:
    u = (unit or "").strip().replace("³", "3").lower().replace(" ", "")
    if u == "kwh":
        return "kwh"
    if u == "m3" or u.endswith("m3"):
        return "m3"
    if u in ("l", "liter", "liters", "litre", "litres") or u.startswith("lit"):
        return "l"
    return u or "unit"


def _unit_display(unit: str | None) -> str:
    u = (unit or "").strip()
    return u if u else "unit"


def _stats_key(row: UsageTableRow) -> tuple[str, str]:
    return row["metric_label"], _unit_key(row.get("consumption_unit"))


def _format_cost(value: float) -> str:
    return f"€{value:.0f}" if value >= 10 else f"€{value:.2f}"


def _format_ratio(value: float, unit: str) -> str:
    return f"{_format_cost(value)}/{unit}"


def _build_metric_stats(rows: list[UsageTableRow]) -> dict[tuple[str, str], _MetricStats]:
    values: dict[tuple[str, str], dict[str, list[float]]] = {}
    for row in rows:
        label = row["metric_label"]
        if label not in {"Heating", "Warm water"}:
            continue

        cost = row.get("cost_value")
        if cost is None:
            continue

        key = _stats_key(row)
        bucket = values.setdefault(
            key,
            {"ratios": [], "costs": [], "no_consumption_costs": [], "consumptions": []},
        )
        cost_f = float(cost)
        bucket["costs"].append(cost_f)

        cons = row.get("consumption_value")
        if cons is None or cons <= 0:
            bucket["no_consumption_costs"].append(cost_f)
            continue

        cons_f = float(cons)
        bucket["consumptions"].append(cons_f)
        bucket["ratios"].append(cost_f / cons_f)

    stats: dict[tuple[str, str], _MetricStats] = {}
    for key, bucket in values.items():
        ratios = bucket["ratios"]
        costs = bucket["costs"]
        no_consumption_costs = bucket["no_consumption_costs"]
        consumptions = bucket["consumptions"]
        stats[key] = _MetricStats(
            ratio_median=median(ratios) if ratios else None,
            cost_median=median(costs) if costs else None,
            no_consumption_cost_median=median(no_consumption_costs)
            if no_consumption_costs
            else None,
            consumption_median=median(consumptions) if consumptions else None,
            ratio_count=len(ratios),
            no_consumption_count=len(no_consumption_costs),
        )
    return stats


def _fallback_ratio_limit(label: str, unit_key: str) -> float | None:
    if label == "Heating":
        if unit_key == "kwh":
            return _FALLBACK_HEATING_EUR_PER_KWH
        return None
    if unit_key == "m3":
        return _FALLBACK_WARM_WATER_EUR_PER_M3
    if unit_key == "l":
        return _FALLBACK_WARM_WATER_EUR_PER_L
    return None


def _ratio_note(row: UsageTableRow, *, cost: float, stats: _MetricStats) -> str | None:
    cons_raw = row.get("consumption_value")
    if cons_raw is None or cons_raw <= 0:
        return None

    cons = float(cons_raw)
    unit = _unit_display(row.get("consumption_unit"))
    unit_key = _unit_key(row.get("consumption_unit"))
    ratio = cost / cons

    if stats.ratio_median is not None and stats.ratio_count >= _MIN_RATIO_BASELINE_ROWS:
        ratio_limit = stats.ratio_median * _RATIO_MULTIPLIER
        cons_limit = (
            stats.consumption_median * _LOW_CONSUMPTION_SHARE
            if stats.consumption_median is not None
            else None
        )
        if cost >= _MIN_COST_EUR and ratio >= ratio_limit and (
            cons_limit is None or cons <= cons_limit
        ):
            multiple = ratio / stats.ratio_median
            return (
                f"**{cons:g} {unit}** vs **{_format_cost(cost)}** = "
                f"**{_format_ratio(ratio, unit)}**, about **{multiple:.1f}x** the yearly median. "
                "Could be fixed-share allocation, pooled cost, or a missing read."
            )

    fallback_limit = _fallback_ratio_limit(row["metric_label"], unit_key)
    if fallback_limit is not None and cost >= _MIN_COST_EUR and ratio >= fallback_limit:
        return (
            f"**{cons:g} {unit}** vs **{_format_cost(cost)}** = "
            f"**{_format_ratio(ratio, unit)}**. No stable yearly baseline yet, but this ratio is high enough "
            "to sanity-check against the statement."
        )
    return None


def _no_consumption_note(row: UsageTableRow, *, cost: float, stats: _MetricStats) -> str | None:
    threshold = _MIN_NO_CONS_COST_EUR
    if (
        stats.no_consumption_cost_median is not None
        and stats.no_consumption_count >= _MIN_RATIO_BASELINE_ROWS
    ):
        threshold = max(
            threshold,
            stats.no_consumption_cost_median * _NO_CONS_COST_MULTIPLIER,
        )

    if cost < threshold:
        return None

    return (
        f"**{_format_cost(cost)}** on the {row['metric_label'].lower()} line with **no consumption** "
        "paired for this month. Missing reads and fixed allocations often show up this way."
    )


def _maybe_note(row: UsageTableRow, *, cost: float, stats: _MetricStats) -> str | None:
    cons = row.get("consumption_value")
    if cons is None or cons <= 0:
        return _no_consumption_note(row, cost=cost, stats=stats)
    return _ratio_note(row, cost=cost, stats=stats)


def build_usage_notes(usage_rows: list[UsageTableRow]) -> list[UsageNote]:
    """Flags months where billed cost looks out of proportion to recorded heating / warm-water use."""

    eligible = {"Heating", "Warm water"}
    stats_by_metric = _build_metric_stats(usage_rows)
    notes: list[UsageNote] = []
    seen: set[tuple[int, str]] = set()

    for row in usage_rows:
        label = row["metric_label"]
        if label not in eligible:
            continue

        cost = row.get("cost_value")
        if cost is None:
            continue
        cost_f = float(cost)
        month = int(row["month"])

        stats = stats_by_metric.get(
            _stats_key(row),
            _MetricStats(
                ratio_median=None,
                cost_median=None,
                no_consumption_cost_median=None,
                consumption_median=None,
                ratio_count=0,
                no_consumption_count=0,
            ),
        )
        msg = _maybe_note(row, cost=cost_f, stats=stats)

        if not msg:
            continue

        key = (month, label)
        if key in seen:
            continue
        seen.add(key)
        ms = _MONTH_ABBR[month] if 1 <= month <= 12 else str(month)
        notes.append(
            {
                "month": month,
                "month_short": ms,
                "metric_label": label,
                "message": msg,
            }
        )

    notes.sort(key=lambda n: (-n["month"], n["metric_label"]))
    return notes
