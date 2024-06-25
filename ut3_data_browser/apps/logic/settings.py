from __future__ import annotations

from platformdirs import user_data_dir
from pathlib import Path
from configparser import ConfigParser

def config_path() -> Path:
    return Path(user_data_dir(appname="ut3_data_browser", appauthor="TAUSystems")) / "config.ini"


def save_config(form_data: dict):
    cp = ConfigParser()
    cp['directories'] = {
        'epics_daq_test_folder_path': form_data['epics_daq_test_folder_path'],
    }

    cp['Database'] = {
        'measurement_db_host': form_data['measurement_db_host'],
        'measurement_db_port': form_data['measurement_db_port'],
        'measurement_db_dbname': form_data['measurement_db_dbname'],
        'measurement_db_username': form_data['measurement_db_username'],
        'measurement_db_password': form_data['measurement_db_password'],
    }

    config_path().parent.mkdir(parents=True, exist_ok=True)

    with config_path().open('w') as f:
        cp.write(f)

def load_config() -> dict[str, dict[str, str]]:
    cp = ConfigParser()

    try:
        if not config_path().exists():
            raise FileNotFoundError("Config file does not exist.")

        cp.read(config_path())

        if 'directories' not in cp.sections():
            raise ValueError("directories not found in config")

        if 'measurement_db' not in cp.sections():
            raise ValueError("measurement_db not found in config")

        return {section_name: dict(cp.items(section_name)) for section_name in cp.sections()}

    except:
        return {'directories': {
                    'epics_daq_test_folder_path': "",
                }, 
                'measurement_db': {
                    'host': "",
                    'port': "",
                    'dbname': "",
                    'username': "",
                    'password': "",
                }
        }
