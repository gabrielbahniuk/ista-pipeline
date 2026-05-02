from src.pipeline.report_data import build_sections, compute_chart_series, enrich_records


def test_enrich_records_parses_period_end():
    rows = enrich_records(
        [
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating", "value": 1.0, "unit": "units"},
            {"period_end": None},
        ]
    )
    assert len(rows) == 1
    assert rows[0]["year"] == 2026 and rows[0]["month"] == 3


def test_build_sections_merges_usage_table():
    enriched = enrich_records(
        [
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating", "value": 10.0, "unit": "units"},
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating_cost", "value": 95.0, "unit": "EUR"},
        ]
    )
    sections = build_sections(enriched, chart_paths={(2026, "heating"): "assets/heating_2026.svg"})
    assert len(sections) == 1
    assert sections[0]["year"] == 2026
    rows = sections[0]["usage_rows"]
    assert len(rows) == 1
    assert rows[0]["metric_label"] == "Heating"
    assert rows[0]["consumption_value"] == 10.0
    assert rows[0]["cost_value"] == 95.0


def test_compute_chart_series():
    enriched = enrich_records(
        [
            {"period_end": "2026-01-31T23:59:59+00:00", "metric": "heating", "value": 1.0, "unit": "units"},
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating", "value": 3.0, "unit": "units"},
        ]
    )
    series = compute_chart_series(enriched)
    assert series[(2026, "heating")] == ([1, 3], [1.0, 3.0])


def test_build_sections_skips_benchmark_metrics():
    enriched = enrich_records(
        [
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating", "value": 10.0, "unit": "units"},
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating_benchmark", "value": 8.0, "unit": "units"},
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating_cost", "value": 95.0, "unit": "EUR"},
        ]
    )
    sections = build_sections(enriched, chart_paths={})
    rows = sections[0]["usage_rows"]
    assert len(rows) == 1
    assert rows[0]["consumption_value"] == 10.0

