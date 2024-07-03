from __future__ import annotations

from typing import TypedDict

class DirectoriesConfigurationDict(TypedDict):
    epics_daq_test_folder_path: str

class MeasurementDBConfigurationDict(TypedDict):
    driver: str
    host: str
    port: str
    dbname: str
    username: str
    password: str

class ConfigurationDict(TypedDict):
    directories: DirectoriesConfigurationDict
    measurement_db: MeasurementDBConfigurationDict
