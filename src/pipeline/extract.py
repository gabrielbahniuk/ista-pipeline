from __future__ import annotations

import os
from typing import Any

from pyecotrend_ista import PyEcotrendIsta


def extract_from_ista() -> dict[str, Any]:
    email = os.environ["ISTA_EMAIL"]
    password = os.environ["ISTA_PASSWORD"]

    client = PyEcotrendIsta(email, password)
    payload: dict[str, Any] = {}

    try:
        client.login()
        uuids = client.get_uuids() or []
        payload["uuids"] = uuids
        payload["items"] = {}

        for unit_uuid in uuids:
            consumption = client.get_consumption_data(unit_uuid)
            details = client.get_consumption_unit_details()
            payload["items"][unit_uuid] = {
                "consumption": consumption,
                "details": details,
            }
    finally:
        client.logout()

    return payload
