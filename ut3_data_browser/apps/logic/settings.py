from __future__ import annotations

from platformdirs import user_data_dir
from pathlib import Path
from configparser import ConfigParser

from dotenv import dotenv_values
from os import environ

import toml

from ..types import ConfigurationDict

def load_config() -> ConfigurationDict:
    return UserDataConfiguration().load()

def save_config(form_data: dict) -> None:
    UserDataConfiguration().save(form_data)

class Configuration:
    def __init__(self):
        pass

    def save(self) -> None:
        raise NotImplementedError("Subclasses must implement this method")
    
    def load(self) -> ConfigurationDict:
        raise NotImplementedError("Subclasses must implement this method")

class DotenvConfiguration(Configuration):
    """Saves and loads configuration from a .env file
    """
    def save(self, form_data: dict):
        raise NotImplementedError("Cannot save to .env file")
    
    def load(self) -> ConfigurationDict:
        env = dotenv_values()
        return {
            'directories': {
                'epics_daq_test_folder_path': env.get('EPICS_DAQ_TEST_FOLDER_PATH', ''),
            },
            'measurement_db': {
                'driver': env.get('MEASUREMENT_DB_SQLALCHEMY_DRIVER', ''),
                'host': env.get('MEASUREMENT_DB_HOST', ''),
                'port': env.get('MEASUREMENT_DB_PORT', ''),
                'dbname': env.get('MEASUREMENT_DB_DBNAME', ''),
                'username': env.get('MEASUREMENT_DB_USERNAME', ''),
                'password': env.get('MEASUREMENT_DB_PASSWORD', ''),
            }
        }

class OSEnvConfiguration(Configuration):
    """Saves and loads configuration from operating system environment variables
    """
    def save(self):
        raise NotImplementedError("Cannot save to OS environment variables")

    def load(self) -> ConfigurationDict:
        return {
            'directories': {
                'epics_daq_test_folder_path': environ.get('EPICS_DAQ_TEST_FOLDER_PATH', ''),
            },
            'measurement_db': {
                'driver': environ.get('MEASUREMENT_DB_SQLALCHEMY_DRIVER', 'postgresql+psycopg2'),
                'host': environ.get('MEASUREMENT_DB_HOST', ''),
                'port': environ.get('MEASUREMENT_DB_PORT', ''),
                'dbname': environ.get('MEASUREMENT_DB_DBNAME', ''),
                'username': environ.get('MEASUREMENT_DB_USERNAME', ''),
                'password': environ.get('MEASUREMENT_DB_PASSWORD', ''),
            }
        }


class UserDataConfiguration(Configuration):
    """Uses platformdirs.user_data_dir to store configuration
    """

    def config_path(self) -> Path:
        return Path(user_data_dir(appname="ut3_data_browser", appauthor="TAUSystems")) / "config.toml"


    def save(self, form_data: dict):
        config = ConfigurationDict({})

        config['scalars'] = {
            'variables_shown': form_data['variables_shown'].split('\n'),
        }

        config['directories'] = {
            'epics_daq_test_folder_path': form_data['epics_daq_test_folder_path'],
        }

        config['measurement_db'] = {
            'driver': form_data['measurement_db_driver'],
            'host': form_data['measurement_db_host'],
            'port': form_data['measurement_db_port'],
            'dbname': form_data['measurement_db_dbname'],
            'username': form_data['measurement_db_username'],
            'password': form_data['measurement_db_password'],
        }

        self.config_path().parent.mkdir(parents=True, exist_ok=True)

        with self.config_path().open('w') as f:
            toml.dump(config, f)

    def load(self) -> ConfigurationDict:
        try:
            return toml.load(self.config_path())
        except FileNotFoundError:
            return {}
