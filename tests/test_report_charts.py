from pathlib import Path

from src.pipeline.report_charts import generate_chart_assets
from src.pipeline.report_data import enrich_records


def test_generate_chart_assets_writes_svg(tmp_path: Path):
    enriched = enrich_records(
        [
            {"period_end": "2026-02-28T23:59:59+00:00", "metric": "heating", "value": 20.0, "unit": "units"},
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating", "value": 30.0, "unit": "units"},
            {"period_end": "2026-03-31T23:59:59+00:00", "metric": "heating_cost", "value": 95.0, "unit": "EUR"},
        ]
    )

    charts_dir = tmp_path / "charts"
    paths = generate_chart_assets(enriched, charts_dir)

    key_heating = (2026, "heating")
    assert key_heating in paths
    svg_path = charts_dir / "heating_2026.svg"
    assert svg_path.is_file()
    assert paths[key_heating].endswith("heating_2026.svg")

    svg_text = svg_path.read_text(encoding="utf-8")
    assert "€" in svg_text
    assert "Feb" in svg_text and "Mar" in svg_text


def test_chart_shows_ecotrend_legend_when_benchmark_matches_unit(tmp_path: Path):
    enriched = enrich_records(
        [
            {"period_end": "2026-02-28T23:59:59+00:00", "metric": "heating", "value": 20.0, "unit": "units"},
            {"period_end": "2026-02-28T23:59:59+00:00", "metric": "heating_benchmark", "value": 15.0, "unit": "units"},
            {"period_end": "2026-02-28T23:59:59+00:00", "metric": "heating_cost", "value": 50.0, "unit": "EUR"},
        ]
    )
    charts_dir = tmp_path / "charts"
    generate_chart_assets(enriched, charts_dir)
    svg_text = (charts_dir / "heating_2026.svg").read_text(encoding="utf-8")
    assert "Average consumption" in svg_text
    assert "You" in svg_text


def test_benchmark_euro_omitted_when_average_dwarfs_your_use(tmp_path: Path):
    """Fixed charges + ~0 kWh ⇒ implied €/use is meaningless; do not label the avg bar."""
    enriched = enrich_records(
        [
            {"period_end": "2025-09-30T23:59:59+00:00", "metric": "heating", "value": 1.0, "unit": "kWh"},
            {"period_end": "2025-09-30T23:59:59+00:00", "metric": "heating_benchmark", "value": 64.6, "unit": "kWh"},
            {"period_end": "2025-09-30T23:59:59+00:00", "metric": "heating_cost", "value": 13.0, "unit": "EUR"},
        ]
    )
    charts_dir = tmp_path / "charts"
    generate_chart_assets(enriched, charts_dir)
    svg_text = (charts_dir / "heating_2025.svg").read_text(encoding="utf-8")
    assert "839.8" not in svg_text.replace(",", ".")
    assert "839,8" not in svg_text


def test_benchmark_euro_is_rule_of_three_from_your_invoice(tmp_path: Path):
    enriched = enrich_records(
        [
            {"period_end": "2026-02-28T23:59:59+00:00", "metric": "heating", "value": 20.0, "unit": "units"},
            {"period_end": "2026-02-28T23:59:59+00:00", "metric": "heating_benchmark", "value": 15.0, "unit": "units"},
            {"period_end": "2026-02-28T23:59:59+00:00", "metric": "heating_cost", "value": 50.0, "unit": "EUR"},
        ]
    )
    charts_dir = tmp_path / "charts"
    generate_chart_assets(enriched, charts_dir)
    svg_text = (charts_dir / "heating_2026.svg").read_text(encoding="utf-8")
    # 50 € * (15 / 20) = 37.5 €
    assert "37.5 €" in svg_text or "37,5 €" in svg_text
