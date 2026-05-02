from src.pipeline.report_notes import build_usage_notes
from src.pipeline.schemas import UsageTableRow


def _row(
    *,
    month: int = 12,
    metric_label: str = "Heating",
    consumption_value: float | None = 100.0,
    consumption_unit: str | None = "kWh",
    cost_value: float | None = 50.0,
    cost_unit: str | None = "EUR",
) -> UsageTableRow:
    return {
        "month": month,
        "metric_label": metric_label,
        "consumption_value": consumption_value,
        "consumption_unit": consumption_unit,
        "cost_value": cost_value,
        "cost_unit": cost_unit,
    }


def test_heating_low_kwh_high_cost_triggers_note():
    rows = [
        _row(month=10, consumption_value=180.0, consumption_unit="kWh", cost_value=90.0),
        _row(month=11, consumption_value=200.0, consumption_unit="kWh", cost_value=100.0),
        _row(month=12, consumption_value=1.0, consumption_unit="kWh", cost_value=144.0),
    ]
    notes = build_usage_notes(rows)
    assert len(notes) == 1
    assert notes[0]["month_short"] == "Dec"
    assert notes[0]["metric_label"] == "Heating"
    assert "kWh" in notes[0]["message"]
    assert "yearly median" in notes[0]["message"]


def test_heating_balanced_month_is_silent():
    rows = [_row(consumption_value=200.0, consumption_unit="kWh", cost_value=120.0)]
    assert build_usage_notes(rows) == []


def test_sparse_physical_unit_uses_conservative_fallback():
    rows = [_row(consumption_value=1.0, consumption_unit="kWh", cost_value=144.0)]
    notes = build_usage_notes(rows)
    assert len(notes) == 1
    assert "No stable yearly baseline yet" in notes[0]["message"]


def test_generic_units_need_yearly_baseline():
    rows = [_row(consumption_value=100.0, consumption_unit="units", cost_value=95.0)]
    assert build_usage_notes(rows) == []


def test_heating_missing_consumption_with_cost_triggers():
    rows = [_row(consumption_value=None, consumption_unit=None, cost_value=80.0)]
    notes = build_usage_notes(rows)
    assert len(notes) == 1
    assert "no consumption" in notes[0]["message"].lower()


def test_zero_consumption_uses_zero_consumption_baseline():
    rows = [
        _row(month=8, consumption_value=0.0, consumption_unit="kWh", cost_value=5.0),
        _row(month=7, consumption_value=0.0, consumption_unit="kWh", cost_value=5.0),
        _row(month=6, consumption_value=0.0, consumption_unit="kWh", cost_value=5.0),
        _row(month=5, consumption_value=0.0, consumption_unit="kWh", cost_value=15.0),
        _row(month=4, consumption_value=0.0, consumption_unit="kWh", cost_value=29.0),
        _row(month=3, consumption_value=109.9, consumption_unit="kWh", cost_value=66.0),
    ]
    notes = build_usage_notes(rows)

    assert [(n["month"], n["metric_label"]) for n in notes] == [(4, "Heating")]
