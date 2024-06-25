# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from __future__ import annotations

from apps.home import blueprint
from flask import render_template, redirect

from datetime import datetime

from ..logic.scans import get_scans, get_scan
from .forms import SettingsForm
from ..logic.settings import save_config, load_config

@blueprint.route('/index')
def index():
    return render_template('home/index.html', segment='index')

@blueprint.route('/')
@blueprint.route('/scans')
def list_scans():
    return render_template("home/scans.html", scans_table_items=get_scans())

@blueprint.route('/scans/<timestamp>')
def show_scan(timestamp: str):
    return render_template("home/scan.html", scan=get_scan(datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')))

@blueprint.route('/settings', methods=['GET', 'POST'])
def settings():

    form = SettingsForm()

    if form.validate_on_submit():
        save_config(form.data)
        return redirect("/")

    else:
        config = load_config()

        form.epics_daq_test_folder_path.data = config['directories']['epics_daq_test_folder_path']
        
        form.measurement_db_host.data = config['measurement_db']['host']
        form.measurement_db_port.data = config['measurement_db']['port']
        form.measurement_db_dbname.data = config['measurement_db']['dbname']
        form.measurement_db_username.data = config['measurement_db']['username']
        form.measurement_db_password.data = config['measurement_db']['password']

        return render_template("home/settings.html", form=form)


@blueprint.app_errorhandler(404) 
def not_found(e): 
  # defining function 
  return render_template("home/page-404.html"), 404

@blueprint.app_errorhandler(500) 
def unspecified_error(e): 
  # defining function 
  return render_template("home/page-500.html"), 500
