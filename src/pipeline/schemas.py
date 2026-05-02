from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict


class NormalizedRecord(TypedDict):
    source: str
    unit_uuid: str
    meter_name: str | None
    metric: str
    period_start: object | None
    period_end: object | None
    value: float
    unit: str
    raw_payload: Any
    collected_at: datetime
    fingerprint: str


class EnrichedRecord(NormalizedRecord):
    year: int
    month: int


class FigureRef(TypedDict):
    title: str
    path: str
    metric_key: str


class UsageTableRow(TypedDict):
    month: int
    metric_label: str
    consumption_value: float | None
    consumption_unit: str | None
    cost_value: float | None
    cost_unit: str | None


class YearSection(TypedDict):
    year: int
    figures: list[FigureRef]
    usage_rows: list[UsageTableRow]


class UsageNote(TypedDict):
    month: int
    month_short: str
    metric_label: str
    message: str


class ReportIndexContext(TypedDict):
    generated_at: str
    years: list[int]
    years_with_usage_notes: list[int]


class YearReportContext(TypedDict):
    generated_at: str
    year: int
    section: YearSection
    usage_notes: list[UsageNote]
