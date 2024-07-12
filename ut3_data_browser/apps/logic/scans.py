from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, Optional
from datetime import datetime
from datetime import timezone as tz

from sqlalchemy import select
if TYPE_CHECKING:
    from sqlalchemy import Row

from .utils.measurement_db import get_sqlalchemy_engine, get_tables
from .settings import load_config

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


def get_scan_measurements(scan_timestamp: datetime = None) -> dict[datetime, dict[str, float]]:
    """
    
    Returns
    -------
    dict[datetime, dict[str, float]]
        measurement values organized in a dict of dicts. Outer dict keys are 
        shot timestamp, inner dict keys are variables names
    """
    select_stmt = (
        select(tables['variable'].c.name.label('variable_name'), 
               tables['burst'].c.timestamp.label('burst_timestamp'),
               tables['shot'].c.timestamp.label('shot_timestamp'),
               tables['measurement'].c.value
              )
            .join_from(tables['measurement'], tables['shot'])
            .join_from(tables['measurement'], tables['variable'])
            .join_from(tables['shot'], tables['burst'])
            .join_from(tables['burst'], tables['scan'])
            .order_by(tables['shot'].c.timestamp)
    )

    if scan_timestamp is not None:
        select_stmt = select_stmt.where(tables['scan'].c.timestamp == scan_timestamp)
    
    scan_measurements = {}

    with sqlalchemy_engine.connect() as connection:
        for row in connection.execute(select_stmt):

            if row.shot_timestamp not in scan_measurements:
                scan_measurements[row.shot_timestamp] = {'burst_timestamp': row.burst_timestamp}

            scan_measurements[row.shot_timestamp][row.variable_name] = row.value

    return scan_measurements



class ShotData(NamedTuple):
    shot_timestamp: datetime
    pointing_and_spectrum_path: str | None

    measurements: dict[str, float]


def get_scan_results_for_scan_page(scan_timestamp: datetime, variable_names: Optional[list[str]] = None) -> list[ShotData]:

    if variable_names is None:
        # TODO: get variable names from configuration
        variable_names = ['Plasma:Position:HorizontalX:Absolute_GET', 
                          'Plasma:Position:VerticalY:Absolute_GET', 
                          'Plasma:Position:LongitudinalZ:Absolute_GET', 
                          
                          'E:Stats:Spectrometer:Pointing:CentroidX_RBV',
                          'E:Stats:Spectrometer:Pointing:CentroidY_RBV',
                          
                          'E:Spectrometer:LowEnergy:mean_energy_MeV',
                          'E:Spectrometer:LowEnergy:std_energy_MeV',
                          'E:Spectrometer:LowEnergy:dE_over_E',
                         ]

    config = load_config()
    epics_daq_test_folder_path: str | None = config.get('directories', {}).get('epics_daq_test_folder_path', None)

    scan_measurements = get_scan_measurements(scan_timestamp)

    scan_results: list[ShotData] = []
    for shot_timestamp, shot_measurements in scan_measurements.items():
        
        pointing_and_spectrum_path = ((f"burst-{shot_measurements['burst_timestamp']:%Y-%m-%dT%H-%M-%S-%fZ}/" 
                                       f"shot-{shot_timestamp:%Y-%m-%dT%H-%M-%S-%fZ}/"
                                       "E-Spectrometer-LowEnergy/" 
                                       "pointing_and_spectrum.png"
                                      ) if epics_daq_test_folder_path else None
                                     )
        
        # TODO: get variable display name
        measurements = {variable_name: shot_measurements.get(variable_name, float('nan'))
                        for variable_name in variable_names
                       }

        scan_results.append(ShotData(
            shot_timestamp = shot_timestamp,
            pointing_and_spectrum_path = pointing_and_spectrum_path,
            measurements = measurements,
        ))

    return scan_results
