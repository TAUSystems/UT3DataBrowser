from __future__ import annotations

from typing import NamedTuple
from pathlib import Path
from .settings import load_config
from datetime import datetime, timedelta

Scan = NamedTuple("Scan", [("timestamp", datetime), ("description", str), ("session_timestamp", datetime), ("seq", int)])

def get_scans() -> list[Scan]:
    config = load_config()

    session_timestamp = datetime.now()

    scans = [
        Scan(
            timestamp = datetime.now(),
            description = "broad Z-scan",
            session_timestamp = session_timestamp,
            seq = 1,
        ),
        Scan(
            timestamp = datetime.now() + timedelta(seconds=123),
            description = "narrower Z-scan",
            session_timestamp = session_timestamp,
            seq = 2,
        ),
    ]

    return scans


def get_scan(scan_name: str) -> Scan:
    config = load_config()

    return Scan(
                name = "some_scan",
                description = "description of some_scan",
            )
