from __future__ import annotations

from operator import attrgetter
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, NewType, Optional
from datetime import datetime
from datetime import timezone as tz

from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy import Row

from .utils.measurement_db import get_sqlalchemy_engine, get_tables
from .settings import load_config
from ..types import VariableName

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


def get_scan_measurements_from_db(scan_timestamp: datetime, variable_names: Optional[list[str]] = None) -> list[Row]:
    """
    
    Returns
    -------
    list[Row]
        List of rows with the following attributes:
        - variable_name
        - burst_timestamp
        - burst_seq
        - shot_timestamp
        - shot_seq
        - value
    """
    select_stmt = (
        select(tables['variable'].c.name.label('variable_name'), 
               tables['burst'].c.timestamp.label('burst_timestamp'),
               tables['burst'].c.seq.label('burst_seq'),
               tables['shot'].c.timestamp.label('shot_timestamp'),
               tables['shot'].c.seq.label('shot_seq'),
               tables['measurement'].c.value
              )
            .join_from(tables['measurement'], tables['shot'])
            .join_from(tables['measurement'], tables['variable'])
            .join_from(tables['shot'], tables['burst'])
            .join_from(tables['burst'], tables['scan'])
            .where(tables['scan'].c.timestamp == scan_timestamp)
            .order_by(tables['shot'].c.timestamp)
    )

    if variable_names is not None:
        select_stmt = select_stmt.where(tables['variable'].c.name.in_(variable_names))

    with sqlalchemy_engine.connect() as connection:
        return connection.execute(select_stmt).fetchall()


class ShotData(NamedTuple):
    timestamp: datetime
    seq: int
    measurements: dict[str, float]
    pointing_and_spectrum_path: str | None

class BurstData(NamedTuple):
    timestamp: datetime
    seq: int
    shots: list[ShotData]
    averages: dict[VariableName, float]

class ScanData(NamedTuple):
    timestamp: datetime
    bursts: list[BurstData]

def organize_scan_measurements(scan_measurements: list[Row]) -> list[BurstData]:
    """ Organizes measurements obtained with get_scan_measurements_from_db into 
        a list of BurstData objects.

        Does not calculate burst_averages

    """

    bursts = {}
    for row in scan_measurements:

        if row.burst_timestamp not in bursts:
            bursts[row.burst_timestamp] = BurstData(
                timestamp = row.burst_timestamp.replace(tzinfo=tz.utc),
                seq = row.burst_seq,
                shots = [],
                averages = {},
            )

        # temporary dict to organize shots before making a list of shots
        bursts[row.burst_timestamp].shots_dict = {}

        if row.shot_timestamp not in bursts[row.burst_timestamp].shots_dict:
            bursts[row.burst_timestamp].shots_dict[row.shot_timestamp] = ShotData(
                timestamp = row.shot_timestamp.replace(tzinfo=tz.utc),
                seq = row.shot_seq,
                pointing_and_spectrum_path = None,
                measurements = {},
            )

        bursts[row.burst_timestamp].shots_dict[row.shot_timestamp].measurements[row.variable_name] = row.value

    for burst_timestamp, burst in bursts.items():
        burst.shots = sorted(burst.shots_dict.values(), key=attrgetter('timestamp'))
        del burst.shots_dict

    return sorted(bursts.values(), key=attrgetter('timestamp'))

def calculate_burst_averages(burst: BurstData) -> dict[VariableName, float]:
    """ Calculates the average of each variable across all shots in a burst
    """
    measurements: dict[VariableName, list[float]] = {}
    for shot in burst.shots:
        for variable_name, value in shot.measurements.items():
            if variable_name not in measurements:
                measurements[variable_name] = []
            measurements[variable_name].append(value)

    averages = {variable_name: sum(values) / len(values) 
                for variable_name, values in measurements.items()
               }

    return averages



def get_scan_results_for_scan_page(scan_timestamp: datetime, variable_names: Optional[list[str]] = None) -> ScanData:

    if variable_names is None:
        # TODO: get variable names from configuration
        variable_names = ['Plasma:Position:HorizontalX:Absolute_GET', 
                          'Plasma:Position:VerticalY:Absolute_GET', 
                          'Plasma:Position:LongitudinalZ:Absolute_GET', 

                          'E:Spectrometer:LowEnergy:mean_energy_MeV',
                          'E:Spectrometer:LowEnergy:std_energy_MeV',
                          'E:Spectrometer:LowEnergy:dE_over_E',

                          'E:Spectrometer:LowEnergy:pointing_deviation_x',
                          'E:Spectrometer:LowEnergy:pointing_deviation_y',
                          'E:Spectrometer:LowEnergy:divergence_x',
                          'E:Spectrometer:LowEnergy:divergence_y',
                         ]

    config = load_config()
    epics_daq_test_folder_path: str | None = config.get('directories', {}).get('epics_daq_test_folder_path', None)

    scan_measurements: list[Row] = get_scan_measurements_from_db(scan_timestamp, variable_names)
    scan_data = ScanData(
        timestamp = scan_timestamp,
        bursts = organize_scan_measurements(scan_measurements)
    )

    for burst in scan_data.bursts:
        burst.averages = calculate_burst_averages(burst)

        for shot in burst.shots:
            shot.pointing_and_spectrum_path = ((f"burst-{burst.timestamp:%Y-%m-%dT%H-%M-%S-%fZ}/" 
                                                f"shot-{shot.timestamp:%Y-%m-%dT%H-%M-%S-%fZ}/"
                                                "E-Spectrometer-LowEnergy/" 
                                                "pointing_and_spectrum.png"
                                               ) if epics_daq_test_folder_path else None
                                              )

    return scan_data
