from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import InputRequired, Regexp

class SettingsForm(FlaskForm):
    epics_daq_test_folder_path = StringField("EPICS-DAQ-Test folder path",
        description="Folder containing data and analysis folders for the EPICS-DAQ-Test experiment", 
    )
    
    submit = SubmitField("Save settings")
