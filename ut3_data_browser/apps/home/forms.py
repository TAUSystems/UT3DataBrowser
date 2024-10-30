from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, IntegerField
from wtforms.validators import InputRequired, Regexp

class SettingsForm(FlaskForm):
    epics_daq_test_folder_path = StringField("EPICS-DAQ-Test folder path",
        description="Folder containing data and analysis folders for the EPICS-DAQ-Test experiment", 
    )
    
    measurement_db_driver = StringField("Measurement DB SQLAlchemy driver",
        description="SQLAlchemy driver to connect to the measurement database server",
    )

    measurement_db_host = StringField("Measurement DB host",
        description="IP address or hostname of the measurement database server",
    )

    measurement_db_port = IntegerField("Measurement DB port",
        description="Port of the measurement database server",
        default=3306,
    )

    measurement_db_dbname = StringField("Measurement DB database name",
        description="Name of the database in the measurement database server",
        default="",
    )

    measurement_db_username = StringField("Measurement DB username",
        description="Username to access the measurement database server",
    )

    measurement_db_password = PasswordField("Measurement DB password",
        description="Password to access the measurement database server",
    )

    submit = SubmitField("Save settings")
