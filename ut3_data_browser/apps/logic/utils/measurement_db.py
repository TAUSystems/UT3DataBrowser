from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import MetaData, create_engine, URL

from ..settings import load_config

if TYPE_CHECKING:
    from sqlalchemy.schema import Table

def get_sqlalchemy_engine():
    config = load_config()
    measurement_db_config = config['measurement_db']

    return create_engine(URL.create(config.get('MEASUREMENT_DB_SQLALCHEMY_DRIVER'),
                            host=measurement_db_config.get('MEASUREMENT_DB_HOST'),
                            port=measurement_db_config.get('MEASUREMENT_DB_PORT'),  
                            database=measurement_db_config.get('MEASUREMENT_DB_DBNAME'),
                            username=measurement_db_config.get('MEASUREMENT_DB_USERNAME'),
                            password=measurement_db_config.get('MEASUREMENT_DB_PASSWORD'),
                        ))

def get_tables() -> dict[str, Table]:
    sqlalchemy_engine = get_sqlalchemy_engine()

    measurement_db_metadata = MetaData()
    measurement_db_metadata.reflect(sqlalchemy_engine)

    return measurement_db_metadata.tables

