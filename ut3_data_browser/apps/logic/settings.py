from __future__ import annotations

from platformdirs import user_data_dir
from pathlib import Path
from configparser import ConfigParser

def config_path() -> Path:
    return Path(user_data_dir(appname="ut3_data_browser", appauthor="TAUSystems")) / "config.ini"


def save_config(form_data: dict):
    cp = ConfigParser()
    cp['Directories'] = {
        'epics_daq_test_folder_path': form_data['epics_daq_test_folder_path'],
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

        if 'Directories' not in cp.sections():
            raise ValueError("Directories not found in config")

        return {section_name: dict(cp.items(section_name)) for section_name in cp.sections()}

    except:
        return {'Directories': {
            'epics_daq_test_folder_path': "",
        }}
