from __future__ import annotations

import os

from dotenv import load_dotenv

from src.pipeline.extract import extract_from_ista
from src.pipeline.load_postgres import write_records
from src.pipeline.normalize import normalize


def main() -> None:
    load_dotenv()
    source = os.getenv("PIPELINE_SOURCE", "ista")

    payload = extract_from_ista()
    records = normalize(payload, source=source)
    inserted = write_records(records)
    unknown_metric = sum(1 for r in records if r.get("metric") == "unknown")
    unknown_unit = sum(1 for r in records if r.get("unit") == "unknown")
    missing_period_end = sum(1 for r in records if not r.get("period_end"))
    sample = records[0] if records else None

    print(
        "Pipeline completed:",
        {
            "units": len(payload.get("uuids", [])),
            "records_generated": len(records),
            "records_inserted": inserted,
            "unknown_metric": unknown_metric,
            "unknown_unit": unknown_unit,
            "missing_period_end": missing_period_end,
            "sample_record": sample,
        },
    )


if __name__ == "__main__":
    main()
