from __future__ import annotations

from typing import NewType, TypedDict

class DirectoriesConfigurationDict(TypedDict):
    epics_daq_test_folder_path: str

class MeasurementDBConfigurationDict(TypedDict):
    driver: str
    host: str
    port: str
    dbname: str
    username: str
    password: str

class PlotConfigurationDict(TypedDict):
    pointing_intensity_max: float
    spectrum_intensity_max: float
    spectrum_lineout_max: float

class ConfigurationDict(TypedDict):
    directories: DirectoriesConfigurationDict
    measurement_db: MeasurementDBConfigurationDict
    plot: PlotConfigurationDict

VariableName = NewType('VariableName', str)
