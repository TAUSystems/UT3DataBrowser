# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
from __future__ import annotations

from apps.home import blueprint
from flask import render_template, redirect, Response, request

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


@blueprint.route('/image')
def image():
    """Get image data to be used in image tags

    Query Parameters
    ----------
    burst_timestamp : str
        in format %Y-%m-%dT%H:%M:%S.%f
    shot_timestamp : str
        in format %Y-%m-%dT%H:%M:%S.%f
    device : str
        device name, as it is in the file system (so not colons but hyphens, e.g. 
        E-Spectrometer)
    subject : str
        file name of the image, including extension (e.g. pointing_and_spectrum.png)

    """
    burst_timestamp: str = request.args.get('burst_timestamp')
    shot_timestamp: str = request.args.get('shot_timestamp')
    device: str = request.args.get('device')
    subject: str = request.args.get('subject')

    if burst_timestamp is None or shot_timestamp is None:
        raise ValueError("burst_timestamp and shot_timestamp must be provided")

    if device is None or subject is None:
        raise ValueError("device and subject must be provided")

    try: 
        burst_timestamp_dt = datetime.strptime(burst_timestamp, '%Y-%m-%dT%H:%M:%S.%f')
        shot_timestamp_dt = datetime.strptime(shot_timestamp, '%Y-%m-%dT%H:%M:%S.%f')
    except ValueError:
        raise ValueError("burst_timestamp and shot_timestamp must be in format %Y-%m-%dT%H:%M:%S.%f")


    ALLOWED_IMAGES = [
        ('E-Spectrometer', 'pointing_and_spectrum.png'),
    ]

    if (device, subject) not in ALLOWED_IMAGES:
        raise ValueError(f"device {device} and subject {subject} not supported")

    file_path_relative_to_data_folder = Path(
        f"burst-{burst_timestamp_dt:%Y-%m-%dT%H-%M-%S-%fZ}",
        f"shot-{shot_timestamp_dt:%Y-%m-%dT%H-%M-%S-%fZ}",
        device,
        subject
    )
    
    config = load_config()
    local_image_path = Path(config['directories']['epics_daq_test_folder_path']) / 'data' / file_path_relative_to_data_folder

    if local_image_path.exists():
        return Response(local_image_path.read_bytes(), mimetype='image/png')
    else:
        raise ValueError(f"Image {file_path_relative_to_data_folder} not found")


@blueprint.app_errorhandler(404) 
def not_found(e): 
  # defining function 
  return render_template("home/page-404.html"), 404

@blueprint.app_errorhandler(500) 
def unspecified_error(e): 
  # defining function 
  return render_template("home/page-500.html"), 500
