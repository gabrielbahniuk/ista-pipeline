from pathlib import Path

from src.pipeline.report_csv import COMBINED_CSV_FILENAME, combined_usage_csv_path, write_all_usage_csv


def test_combined_csv_filename_constant():
    assert COMBINED_CSV_FILENAME == "ista_usage_all.csv"


def test_write_all_usage_csv_multi_year(tmp_path: Path):
    sections = [
        {
            "year": 2026,
            "figures": [],
            "usage_rows": [
                {
                    "month": 3,
                    "metric_label": "Heating",
                    "consumption_value": 100.0,
                    "consumption_unit": "kWh",
                    "cost_value": 50.0,
                    "cost_unit": "EUR",
                },
            ],
        },
        {
            "year": 2025,
            "figures": [],
            "usage_rows": [
                {
                    "month": 12,
                    "metric_label": "Heating",
                    "consumption_value": 200.0,
                    "consumption_unit": "kWh",
                    "cost_value": 90.0,
                    "cost_unit": "EUR",
                },
            ],
        },
    ]
    out = tmp_path / COMBINED_CSV_FILENAME
    write_all_usage_csv(sections, out)
    text = out.read_text(encoding="utf-8")
    assert "year,month,metric" in text
    assert "2026,3,Heating,100,kWh,50" in text
    assert "2025,12,Heating,200,kWh,90" in text


def test_write_all_usage_csv_empty_sections_header_only(tmp_path: Path):
    out = tmp_path / COMBINED_CSV_FILENAME
    write_all_usage_csv([], out)
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("year,")


def test_combined_usage_csv_path(tmp_path: Path):
    p = combined_usage_csv_path(tmp_path)
    assert p.name == COMBINED_CSV_FILENAME
    assert p.parent.name == "exports"

