from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, FloatField, IntegerField, TextAreaField
from wtforms.validators import InputRequired, Regexp

class SettingsForm(FlaskForm):
    variables_shown = TextAreaField("Variables shown",
        description="List of variables to be shown on the scan page"
    )

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

    measurement_db_password = StringField("Measurement DB password",
        description="Password to access the measurement database server",
    )

    plot_pointing_intensity_max = FloatField("Pointing image intensity max",
        description="Upper limit of color scale for pointing image, in AU/mrad^2",
        default=1.0,
    )

    plot_spectrum_intensity_max = FloatField("Spectrum image intensity max",
        description="Upper limit of color scale for spectrum image, in AU/MeV/mrad",
        default=0.1,
    )

    plot_spectrum_lineout_max = FloatField("Spectrum lineout max",
        description="Upper limit of y-axis for spectrum lineout plot, in AU/MeV",
        default=200.0,
    )

    submit = SubmitField("Save settings")
