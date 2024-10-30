from __future__ import annotations

from typing import NewType, TypedDict

VariableName = NewType('VariableName', str)

class ScalarsConfigurationDict(TypedDict):
    variables_shown: list[VariableName]

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
    scalars: ScalarsConfigurationDict
    directories: DirectoriesConfigurationDict
    measurement_db: MeasurementDBConfigurationDict
    plot: PlotConfigurationDict
