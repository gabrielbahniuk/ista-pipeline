from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    # bool is a subclass of int in Python and should never be treated as a measurement
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", ".").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _find_first_numeric(value: Any) -> float | None:
    if isinstance(value, dict):
        preferred_keys = (
            "value",
            "consumption",
            "amount",
            "reading",
            "current_value",
            "currentValue",
            "reading_value",
            "readingValue",
            "cost",
            "co2",
            "emission",
        )
        for key in preferred_keys:
            if key in value:
                found = _to_float(value.get(key))
                if found is not None:
                    return found
        for nested in value.values():
            found = _find_first_numeric(nested)
            if found is not None:
                return found
        return None
    if isinstance(value, list):
        for item in value:
            found = _find_first_numeric(item)
            if found is not None:
                return found
        return None
    return _to_float(value)


def _guess_metric(key: str, item: Any) -> str:
    text = f"{key} {json.dumps(item, ensure_ascii=True)}".lower()
    if "water" in text and "hot" in text:
        return "hot_water"
    if "water" in text:
        return "water"
    if "heat" in text or "heating" in text:
        return "heating"
    return "unknown"


def _guess_unit(item: Any) -> str:
    text = json.dumps(item, ensure_ascii=True).lower()
    if "kwh" in text:
        return "kWh"
    if "m3" in text:
        return "m3"
    if "l" in text and "liter" in text:
        return "L"
    return "unknown"


def _iter_measurements(consumption: Any) -> list[tuple[str, Any]]:
    if isinstance(consumption, list):
        return [(f"item_{idx}", value) for idx, value in enumerate(consumption)]
    if isinstance(consumption, dict):
        measurements: list[tuple[str, Any]] = []
        for key, value in consumption.items():
            # Skip flags and empty values from the provider payload
            if value is None or isinstance(value, bool):
                continue
            # Expand nested lists/dicts because useful readings are often nested
            if isinstance(value, list):
                measurements.extend((f"{key}_{idx}", entry) for idx, entry in enumerate(value))
                continue
            measurements.append((key, value))
        return measurements
    return [("value", consumption)]


def normalize(payload: dict[str, Any], source: str = "ista") -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    now = datetime.now(UTC)

    items = payload.get("items", {})
    for unit_uuid, unit_payload in items.items():
        details = unit_payload.get("details")
        consumption = unit_payload.get("consumption")

        for key, raw_item in _iter_measurements(consumption):
            value = _find_first_numeric(raw_item)
            if value is None:
                continue

            metric = _guess_metric(key, raw_item)
            unit = _guess_unit(raw_item)
            period_start = None
            period_end = None
            if isinstance(raw_item, dict):
                period_start = (
                    raw_item.get("period_start")
                    or raw_item.get("periodStart")
                    or raw_item.get("start")
                    or raw_item.get("from")
                )
                period_end = (
                    raw_item.get("period_end")
                    or raw_item.get("periodEnd")
                    or raw_item.get("end")
                    or raw_item.get("to")
                )
            meter_name = None
            if isinstance(details, dict):
                meter_name = details.get("name") or details.get("meter_name")

            fingerprint_raw = f"{unit_uuid}|{metric}|{period_end}|{value}|{unit}"
            fingerprint = hashlib.sha256(fingerprint_raw.encode("utf-8")).hexdigest()

            records.append(
                {
                    "source": source,
                    "unit_uuid": str(unit_uuid),
                    "meter_name": meter_name,
                    "metric": metric,
                    "period_start": period_start,
                    "period_end": period_end,
                    "value": value,
                    "unit": unit,
                    "raw_payload": raw_item,
                    "collected_at": now,
                    "fingerprint": fingerprint,
                }
            )

    return records
