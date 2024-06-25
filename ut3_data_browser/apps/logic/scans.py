from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple
from datetime import datetime
from datetime import timezone as tz

from sqlalchemy import select
if TYPE_CHECKING:
    from sqlalchemy import Row

from .settings import load_config
from .utils.measurement_db import get_scan_table, get_sqlalchemy_engine

sqlalchemy_engine = get_sqlalchemy_engine()
scan_table = get_scan_table()

class Scan(NamedTuple):
    timestamp: datetime
    title: str
    session_timestamp: datetime
    seq: int
    notes: str

def row_to_scan(row: Row) -> Scan:
    return Scan(
                timestamp = row.timestamp.replace(tzinfo=tz.utc),
                title = row.title,
                session_timestamp = row.session_timestamp.replace(tzinfo=tz.utc),
                seq = row.seq,
                notes = row.notes,
            )

def get_scans() -> list[Scan]:
    with sqlalchemy_engine.connect() as connection:
        return [row_to_scan(row) for row in connection.execute(select(scan_table))]

def get_scan(timestamp: datetime) -> Scan:
    with sqlalchemy_engine.connect() as connection:
        row = connection.execute(select(scan_table).where(scan_table.c.timestamp == timestamp)).fetchone()
        if row is None:
            raise ValueError(f"Scan with timestamp {timestamp} not found.")
        
        return row_to_scan(row)
