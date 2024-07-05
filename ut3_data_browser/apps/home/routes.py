# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from __future__ import annotations

from apps.home import blueprint
from flask import render_template, redirect, Response

from datetime import datetime
from pathlib import Path
import re

from ..logic.scans import get_scans, get_scan, get_scan_results_for_scan_page
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
    scan_timestamp: datetime = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')
    scan = get_scan(scan_timestamp)
    scan_results = get_scan_results_for_scan_page(scan_timestamp)
    return render_template("home/scan.html", scan=scan, scan_results=scan_results)

@blueprint.route('/settings', methods=['GET', 'POST'])
def settings():

    form = SettingsForm()

    if form.validate_on_submit():
        save_config(form.data)
        return redirect("/")

    else:
        config = load_config()

        form.epics_daq_test_folder_path.data = config['directories']['epics_daq_test_folder_path']
        
        form.measurement_db_driver.data = config['measurement_db']['driver']
        form.measurement_db_host.data = config['measurement_db']['host']
        form.measurement_db_port.data = config['measurement_db']['port']
        form.measurement_db_dbname.data = config['measurement_db']['dbname']
        form.measurement_db_username.data = config['measurement_db']['username']
        form.measurement_db_password.data = config['measurement_db']['password']

        return render_template("home/settings.html", form=form)


@blueprint.route('/image/<path:image_path>')
def image(image_path: str):
    config = load_config()

    if not re.match(r'^burst-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{6}Z/shot-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{6}Z/[\w\-]+/[\w_\.]+$', image_path):
        raise ValueError(f"Invalid image path {image_path}")

    local_image_path = Path(config['directories']['epics_daq_test_folder_path']) / 'data' / image_path

    if local_image_path.suffix == '.png':
        return Response(local_image_path.read_bytes(), mimetype='image/png')
    else:
        raise NotImplementedError(f"Image type {local_image_path.suffix} not supported")

@blueprint.app_errorhandler(404) 
def not_found(e): 
  # defining function 
  return render_template("home/page-404.html"), 404

@blueprint.app_errorhandler(500) 
def unspecified_error(e): 
  # defining function 
  return render_template("home/page-500.html"), 500
