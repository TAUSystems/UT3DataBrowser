from __future__ import annotations

from platformdirs import user_data_dir
from pathlib import Path
from configparser import ConfigParser

from dotenv import dotenv_values
from os import environ

from ..types import ConfigurationDict

def load_config() -> ConfigurationDict:
    return DotenvConfiguration().load()

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
        return Path(user_data_dir(appname="ut3_data_browser", appauthor="TAUSystems")) / "config.ini"


    def save(self, form_data: dict):
        cp = ConfigParser()
        cp['directories'] = {
            'epics_daq_test_folder_path': form_data['epics_daq_test_folder_path'],
        }

        cp['Database'] = {
            'measurement_db_driver': form_data['measurement_db_driver'],
            'measurement_db_host': form_data['measurement_db_host'],
            'measurement_db_port': form_data['measurement_db_port'],
            'measurement_db_dbname': form_data['measurement_db_dbname'],
            'measurement_db_username': form_data['measurement_db_username'],
            'measurement_db_password': form_data['measurement_db_password'],
        }

        cp['plot'] = {
            'pointing_intensity_max': form_data['plot_pointing_intensity_max'],
            'spectrum_intensity_max': form_data['plot_spectrum_intensity_max'],
            'spectrum_lineout_max': form_data['plot_spectrum_lineout_max'],
        }

        self.config_path().parent.mkdir(parents=True, exist_ok=True)

        with self.config_path().open('w') as f:
            cp.write(f)

    def load(self) -> ConfigurationDict:
        cp = ConfigParser()

        try:
            if not self.config_path().exists():
                raise FileNotFoundError("Config file does not exist.")

            cp.read(self.config_path())

            if 'directories' not in cp.sections():
                raise ValueError("directories not found in config")

            if 'measurement_db' not in cp.sections():
                raise ValueError("measurement_db not found in config")

            if 'plot' not in cp.sections():
                raise ValueError("plot not found in config")

            return {section_name: dict(cp.items(section_name)) for section_name in cp.sections()}

        except:
            return {'directories': {
                        'epics_daq_test_folder_path': "",
                    }, 
                    'measurement_db': {
                        'driver': "mariadb+pymysql",
                        'host': "",
                        'port': "",
                        'dbname': "",
                        'username': "",
                        'password': "",
                    }, 
                    'plot': {
                        'pointing_intensity_max': 1.0,
                        'spectrum_intensity_max': 0.1,
                        'spectrum_lineout_max': 200.0,
                    }
            }
