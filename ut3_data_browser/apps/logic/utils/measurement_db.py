from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import MetaData, create_engine, URL

from ..settings import load_config
from ...types import ConfigurationDict, MeasurementDBConfigurationDict 

if TYPE_CHECKING:
    from sqlalchemy.schema import Table

def get_sqlalchemy_engine():
    config: ConfigurationDict = load_config()
    measurement_db_config: MeasurementDBConfigurationDict = config['measurement_db']

    return create_engine(URL.create(measurement_db_config.get('driver'),
                            host=measurement_db_config.get('host'),
                            port=measurement_db_config.get('port'),  
                            database=measurement_db_config.get('dbname'),
                            username=measurement_db_config.get('username'),
                            password=measurement_db_config.get('password'),
                        ))

def get_tables() -> dict[str, Table]:
    sqlalchemy_engine = get_sqlalchemy_engine()

    measurement_db_metadata = MetaData()
    measurement_db_metadata.reflect(sqlalchemy_engine)

    return measurement_db_metadata.tables

