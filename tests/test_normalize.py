from src.pipeline.normalize import normalize


def test_normalize_ignores_boolean_flags() -> None:
    payload = {
        "uuids": ["unit-1"],
        "items": {
            "unit-1": {
                "consumption": {
                    "isSCEedBasicForCurrentMonth": True,
                    "consumptions": [],
                },
                "details": {},
            }
        },
    }

    records = normalize(payload)

    assert records == []


def test_normalize_extracts_numeric_from_nested_payload() -> None:
    payload = {
        "uuids": ["unit-1"],
        "items": {
            "unit-1": {
                "consumption": {
                    "consumptions": [
                        {
                            "date": {"month": 4, "year": 2026},
                            "readings": [
                                {
                                    "type": "heating",
                                    "value": "123,45",
                                    "unit": "Einheiten",
                                    "additionalUnit": "kWh",
                                }
                            ],
                        }
                    ]
                },
                "details": {"meter_name": "Main Meter"},
            }
        },
    }

    records = normalize(payload)

    assert len(records) == 1
    assert records[0]["value"] == 123.45
    assert records[0]["period_end"] == "2026-04-30T23:59:59+00:00"
    assert records[0]["metric"] == "heating"
    assert records[0]["unit"] == "units"
    assert records[0]["meter_name"] == "Main Meter"


def test_normalize_fingerprint_is_stable_for_same_payload() -> None:
    payload = {
        "uuids": ["unit-1"],
        "items": {
            "unit-1": {
                "consumption": {"value": 10, "period_end": "2026-04-01T00:00:00Z"},
                "details": {},
            }
        },
    }

    first = normalize(payload)
    second = normalize(payload)

    assert len(first) == 1
    assert len(second) == 1
    assert first[0]["fingerprint"] == second[0]["fingerprint"]
