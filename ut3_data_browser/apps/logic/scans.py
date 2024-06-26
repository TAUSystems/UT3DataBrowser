from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple
from datetime import datetime
from datetime import timezone as tz

from sqlalchemy import select
if TYPE_CHECKING:
    from sqlalchemy import Row

from .utils.measurement_db import get_sqlalchemy_engine, get_tables

sqlalchemy_engine = get_sqlalchemy_engine()
tables = get_tables()

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
    select_stmt = select(tables['scan']).order_by(tables['scan'].c.timestamp.desc())
    with sqlalchemy_engine.connect() as connection:
        return [row_to_scan(row) for row in connection.execute(select_stmt)]

def get_scan(timestamp: datetime) -> Scan:
    with sqlalchemy_engine.connect() as connection:
        row = connection.execute(select(tables['scan']).where(tables['scan'].c.timestamp == timestamp)).fetchone()
        if row is None:
            raise ValueError(f"Scan with timestamp {timestamp} not found.")
        
        return row_to_scan(row)


def get_scan_measurements(scan_timestamp: datetime = None) -> dict[datetime: dict[str, float]]:
    """
    
    Returns
    -------
    dict[datetime: dict[str, float]
        measurement values organized in a dict of dicts. Outer dict keys are 
        shot timestamp, inner dict keys are variables names
    """
    select_stmt = (
        select(tables['variable'].c.name.label('variable_name'), 
               tables['shot'].c.timestamp.label('shot_timestamp'), 
               tables['measurement'].c.value
              )
            .join_from(tables['measurement'], tables['shot'])
            .join_from(tables['measurement'], tables['variable'])
            .join_from(tables['shot'], tables['burst'])
            .join_from(tables['burst'], tables['scan'])
    )

    if scan_timestamp is not None:
        select_stmt = select_stmt.where(tables['scan'].c.timestamp == scan_timestamp)
    
    scan_measurements = {}

    with sqlalchemy_engine.connect() as connection:
        for row in connection.execute(select_stmt):

            if row.shot_timestamp not in scan_measurements:
                scan_measurements[row.shot_timestamp] = {}

            scan_measurements[row.shot_timestamp][row.variable_name] = row.value

    return scan_measurements

