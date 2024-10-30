from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import NamedTuple

import matplotlib.pyplot as plt
import numpy as np
import tifffile

from .settings import load_config

class ImageWithAxes(NamedTuple):
    """ 2D array with specified x and y axes """
    image: np.ndarray
    x_axis: np.ndarray
    y_axis: np.ndarray

def load_spectrum_image(tiff_file: Path) -> ImageWithAxes:
    if not tiff_file.exists():
        raise FileNotFoundError(f"File not found: {tiff_file}")

    with tifffile.TiffFile(tiff_file) as tf:
        image, x_axis, y_axis = (page.asarray() for page in tf.pages)
    assert x_axis.shape == (1, image.shape[1]), f"Unexpected shape for x_axis from {tiff_file}: x_axis.shape = {x_axis.shape}, expected {(1, image.shape[1])}"
    assert y_axis.shape == (image.shape[0], 1), f"Unexpected shape for y_axis from {tiff_file}: y_axis.shape = {y_axis.shape}, expected {(image.shape[0], 1)}"
    return ImageWithAxes(image, x_axis[0, :], y_axis[:, 0])


def plot_pointing_and_spectrum(burst_timestamp: datetime, shot_timestamp: datetime):
    """ Plot pointing image and spectrum image side by side 

    Returns
    -------
    figure : matplotlib Figure

    """

    config = load_config()
    e_spectrometer_folder = Path(config['directories']['epics_daq_test_folder_path']) / 'data' / f"burst-{burst_timestamp:%Y-%m-%dT%H-%M-%S-%fZ}" / f"shot-{shot_timestamp:%Y-%m-%dT%H-%M-%S-%fZ}" / 'E-Spectrometer'

    pointing_image = load_spectrum_image(e_spectrometer_folder / 'pointing.tiff')
    low_energy_image = load_spectrum_image(e_spectrometer_folder / 'low_energy_spectrum.tiff')
    high_energy_image = load_spectrum_image(e_spectrometer_folder / 'high_energy_spectrum.tiff')

    spectrum_lineout = np.loadtxt(e_spectrometer_folder / 'spectrum_AU_per_MeV.dat')
    spectrum_lineout_energy_axis = np.loadtxt(e_spectrometer_folder / 'spectrum_energy_axis_MeV.dat')

    fig = plt.figure(figsize=(18, 4.5), num='pointing_and_spectrum'); fig.clf()
    ax_pointing = fig.add_axes((0.05, 0.10, 0.20, 0.80))
    ax_spectrum = fig.add_axes((0.30, 0.10, 0.68, 0.80))

    p = ax_pointing.pcolormesh(pointing_image.x_axis[::3], pointing_image.y_axis[::3], pointing_image.image[::3, ::3])
    p.set_clim(0, config['plot']['pointing_intensity_max'])
    p = ax_spectrum.pcolormesh(low_energy_image.x_axis[::3], low_energy_image.y_axis[::3], low_energy_image.image[::3, ::3], alpha=0.7)
    p.set_clim(0, config['plot']['spectrum_intensity_max'])
    p = ax_spectrum.pcolormesh(high_energy_image.x_axis[::3], high_energy_image.y_axis[::3], high_energy_image.image[::3, ::3], alpha=0.7)
    p.set_clim(0, config['plot']['spectrum_intensity_max'])

    ax_pointing.set(xlabel="horizontal angle [mrad]", ylabel="vertical angle [mrad]")
    ax_spectrum.set(xlabel="energy [MeV]", ylabel="horizontal angle [mrad]")

    ax_spectrum_lineout = ax_spectrum.twinx()
    ax_spectrum_lineout.set(yticks=[])
    ax_spectrum_lineout.plot(spectrum_lineout_energy_axis, spectrum_lineout, color='yellow', alpha=0.7)
    ax_spectrum_lineout.set_ylim(0, config['plot']['spectrum_lineout_max'])

    return fig
