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
                                    "additionalValue": "503,0",
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
    assert records[0]["value"] == 503.0
    assert records[0]["period_end"] == "2026-04-30T23:59:59+00:00"
    assert records[0]["metric"] == "heating"
    assert records[0]["unit"] == "kWh"
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


def test_normalize_extracts_monthly_costs() -> None:
    payload = {
        "uuids": ["unit-1"],
        "items": {
            "unit-1": {
                "consumption": {
                    "costs": [
                        {
                            "date": {"month": 3, "year": 2026},
                            "costsByEnergyType": [
                                {"type": "heating", "value": 95, "unit": "EUR"},
                                {"type": "warmwater", "value": 80, "unit": "EUR"},
                                {"type": None, "value": None, "unit": None},
                            ],
                        }
                    ]
                },
                "details": {},
            }
        },
    }

    records = normalize(payload)

    assert len(records) == 2
    assert records[0]["metric"] == "heating_cost"
    assert records[0]["unit"] == "EUR"
    assert records[0]["period_end"] == "2026-03-31T23:59:59+00:00"
    assert records[1]["metric"] == "hot_water_cost"


def test_normalize_extracts_average_consumption_benchmark() -> None:
    payload = {
        "uuids": ["unit-1"],
        "items": {
            "unit-1": {
                "consumption": {
                    "consumptions": [
                        {
                            "date": {"month": 2, "year": 2026},
                            "readings": [
                                {
                                    "type": "heating",
                                    "value": 100,
                                    "unit": "Einheiten",
                                    "averageConsumption": {
                                        "averageConsumptionValue": 80,
                                        "unit": "Einheiten",
                                    },
                                }
                            ],
                        }
                    ]
                },
                "details": {},
            }
        },
    }

    records = normalize(payload)

    assert len(records) == 2
    assert records[0]["metric"] == "heating" and records[0]["value"] == 100.0
    assert records[1]["metric"] == "heating_benchmark"
    assert records[1]["value"] == 80.0
    assert records[1]["unit"] == "units"


def test_normalize_heating_stays_einheiten_without_additional_kwh() -> None:
    payload = {
        "uuids": ["unit-1"],
        "items": {
            "unit-1": {
                "consumption": {
                    "consumptions": [
                        {
                            "date": {"month": 5, "year": 2026},
                            "readings": [
                                {
                                    "type": "heating",
                                    "value": "42",
                                    "unit": "Einheiten",
                                }
                            ],
                        }
                    ]
                },
                "details": {},
            }
        },
    }

    records = normalize(payload)
    assert len(records) == 1
    assert records[0]["value"] == 42.0
    assert records[0]["unit"] == "units"


def test_normalize_benchmark_heating_prefers_kwh_inside_average_consumption() -> None:
    payload = {
        "uuids": ["unit-1"],
        "items": {
            "unit-1": {
                "consumption": {
                    "consumptions": [
                        {
                            "date": {"month": 2, "year": 2026},
                            "readings": [
                                {
                                    "type": "heating",
                                    "value": "100",
                                    "unit": "Einheiten",
                                    "additionalValue": "800,0",
                                    "additionalUnit": "kWh",
                                    "averageConsumption": {
                                        "averageConsumptionValue": 80,
                                        "unit": "Einheiten",
                                        "additionalValue": "640,5",
                                        "additionalUnit": "kWh",
                                    },
                                }
                            ],
                        }
                    ]
                },
                "details": {},
            }
        },
    }

    records = normalize(payload)
    assert len(records) == 2
    assert records[0]["value"] == 800.0
    assert records[0]["unit"] == "kWh"
    assert records[1]["metric"] == "heating_benchmark"
    assert records[1]["value"] == 640.5
    assert records[1]["unit"] == "kWh"


def test_normalize_heating_benchmark_uses_additional_average_kwh() -> None:
    """Real EcoTrend shape: average kWh in additionalAverageConsumptionValue, not nested additionalValue."""
    payload = {
        "uuids": ["unit-1"],
        "items": {
            "unit-1": {
                "consumption": {
                    "consumptions": [
                        {
                            "date": {"month": 12, "year": 2025},
                            "readings": [
                                {
                                    "type": "heating",
                                    "value": "316",
                                    "unit": "Einheiten",
                                    "additionalValue": "343,5",
                                    "additionalUnit": "kWh",
                                    "averageConsumption": {
                                        "averageConsumptionValue": "519",
                                        "residentConsumptionValue": "316",
                                        "additionalAverageConsumptionValue": "564,4",
                                        "additionalResidentConsumptionValue": "343,5",
                                    },
                                }
                            ],
                        }
                    ]
                },
                "details": {},
            }
        },
    }

    records = normalize(payload)
    assert len(records) == 2
    assert records[0]["value"] == 343.5
    assert records[0]["unit"] == "kWh"
    assert records[1]["metric"] == "heating_benchmark"
    assert records[1]["value"] == 564.4
    assert records[1]["unit"] == "kWh"
