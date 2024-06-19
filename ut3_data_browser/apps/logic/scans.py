from __future__ import annotations

from typing import NamedTuple
from pathlib import Path
from .settings import load_config

Scan = NamedTuple("Scan", name=str, description=str)

def get_scans() -> list[Scan]:
    config = load_config()

    scans = []    

    return scans


def get_scan(scan_name: str) -> Scan:
    config = load_config()

    return Scan(
                name = "some_scan",
                description = "description of some_scan",
            )
