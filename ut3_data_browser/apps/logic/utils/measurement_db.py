from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import MetaData, create_engine, URL

from ..settings import load_config
from ...types import ConfigurationDict, MeasurementDBConfigurationDict 

if TYPE_CHECKING:
    from sqlalchemy.schema import Table
    from sqlalchemy.engine.base import Engine as SQLAlchemyEngine

class MeasurementDBEngine:
    """ Class to manage the SQLAlchemy engine and tables for the measurement database 
    
    Meant to be used as a global instance. 

    Properties:
    -----------
    sqlalchemy_engine : SQLAlchemyEngine
    tables : dict[str, Table]

    """
    def __init__(self):
        self._sqlalchemy_engine: SQLAlchemyEngine = None
        self._tables: dict[str, Table] = {}
        self.load()

    def load(self):
        self.create_engine()
        self.get_tables()

    @property
    def sqlalchemy_engine(self) -> SQLAlchemyEngine:
        if not self._sqlalchemy_engine:
            self.create_engine()
        return self._sqlalchemy_engine

    @property
    def tables(self) -> dict[str, Table]:
        if not self._tables:
            self.get_tables()
        return self._tables

    def create_engine(self):
        config: ConfigurationDict = load_config()
        measurement_db_config: MeasurementDBConfigurationDict = config['measurement_db']

        try:
            self._sqlalchemy_engine = create_engine(URL.create(
                drivername=measurement_db_config.get('driver'),
                host=measurement_db_config.get('host'),
                port=measurement_db_config.get('port'),  
                database=measurement_db_config.get('dbname'),
                username=measurement_db_config.get('username'),
                password=measurement_db_config.get('password'),
            ))

        except Exception as err:
            print(f"Error creating SQLAlchemy engine: {err}")
            self._sqlalchemy_engine = None

    def get_tables(self):
        if not self._sqlalchemy_engine:
            self.create_engine()
        
        if not self._sqlalchemy_engine:
            self._tables = {}
            return

        measurement_db_metadata = MetaData()
        measurement_db_metadata.reflect(self._sqlalchemy_engine)

        self._tables = measurement_db_metadata.tables

measurement_db_engine = MeasurementDBEngine()
