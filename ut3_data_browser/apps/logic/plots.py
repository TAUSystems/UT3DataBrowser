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

    def stitch_spectrum_images(low_energy_image: ImageWithAxes, high_energy_image: ImageWithAxes) -> tuple[ImageWithAxes, ImageWithAxes, ImageWithAxes]:
        """ Stitches the low and high energy images, which overlap in energy axis

        Parameters
        ----------
        low_energy_image : ImageWithAxes
        high_energy_image : ImageWithAxes

        Returns
        -------
        low_energy_only: ImageWithAxes
            The part of the low energy image that does not overlap with the high energy image
        low_high_energy_overlap: ImageWithAxes
            The stitched part of the low and high energy images
        high_energy_only: ImageWithAxes
            The part of the high energy image that does not overlap with the low energy image

        """
        def sort_axes_if_necessary(image: ImageWithAxes) -> ImageWithAxes:
            if np.any(np.diff(image.x_axis) < 0):
                x_sort_i = np.argsort(image.x_axis)
                image.image = ImageWithAxes(image.image[:, x_sort_i], image.x_axis[x_sort_i], image.y_axis)
            
            if np.any(np.diff(image.y_axis) < 0):
                y_sort_i = np.argsort(image.y_axis)
                image.image = ImageWithAxes(image.image[y_sort_i, :], image.x_axis, image.y_axis[y_sort_i])

            return image

        sort_axes_if_necessary(low_energy_image)
        sort_axes_if_necessary(high_energy_image)

        assert low_energy_image.x_axis[0] < high_energy_image.x_axis[0] and low_energy_image.x_axis[-1] < high_energy_image.x_axis[-1], "Low energy image should have lower energy axis than high energy image"
         
        def interpolate_and_stitch_image_in_overlap_region(image_with_common_y_axis: ImageWithAxes, image_to_interpolate: ImageWithAxes) -> ImageWithAxes:
            """ Interpolate the image_to_interpolate onto the common axis of image_with_common_axis """
            
            def interpolate_one_column(image_column_values: np.ndarray) -> np.ndarray:
                return np.interp(image_with_common_y_axis.y_axis,  image_to_interpolate.y_axis, image_column_values, left=np.nan, right=np.nan)
            interpolated_image = np.apply_along_axis(interpolate_one_column, axis=0, arr=image_to_interpolate.image)

            image = np.hstack([image_with_common_y_axis.image, interpolated_image])
            x_axis = np.concatenate([image_with_common_y_axis.x_axis, image_to_interpolate.x_axis])
            x_sort_i = np.argsort(x_axis)

            stitched_image = ImageWithAxes(
                image[:, x_sort_i],
                x_axis[x_sort_i],
                image_with_common_y_axis.y_axis
            )

            return stitched_image

        def split_image_along_x_axis(image: ImageWithAxes, x_split: float) -> tuple[ImageWithAxes, ImageWithAxes]:
            return ImageWithAxes(
                image.image[:, image.x_axis < x_split],
                image.x_axis[image.x_axis < x_split],
                image.y_axis
            ), ImageWithAxes(
                image.image[:, image.x_axis >= x_split],
                image.x_axis[image.x_axis >= x_split],
                image.y_axis    
            )

        low_energy_image_nonoverlap_region, low_energy_image_overlap_region = split_image_along_x_axis(low_energy_image, high_energy_image.x_axis[0])
        high_energy_image_nonoverlap_region, high_energy_image_overlap_region = split_image_along_x_axis(high_energy_image, low_energy_image.x_axis[-1])

        # use the finer y-axis of the two for the common y-axis
        def mean_y_axis_resolution(image: ImageWithAxes) -> float:
            return (image.y_axis[-1] - image.y_axis[0]) / (len(image.y_axis) - 1)
        if mean_y_axis_resolution(low_energy_image) < mean_y_axis_resolution(high_energy_image):
            overlap_image = interpolate_and_stitch_image_in_overlap_region(low_energy_image_overlap_region, high_energy_image_overlap_region)
        else:
            overlap_image = interpolate_and_stitch_image_in_overlap_region(high_energy_image_overlap_region, low_energy_image_overlap_region)

        return low_energy_image_nonoverlap_region, overlap_image, high_energy_image_nonoverlap_region
    
    low_energy_image_nonoverlap_region, overlap_image, high_energy_image_nonoverlap_region = stitch_spectrum_images(low_energy_image, high_energy_image)

    p = ax_pointing.pcolormesh(pointing_image.x_axis[::3], pointing_image.y_axis[::3], pointing_image.image[::3, ::3])
    p.set_clim(0, config['plot']['pointing_intensity_max'])
    
    def plot_spectrum_image(image: ImageWithAxes) -> None:
        p = ax_spectrum.pcolormesh(image.x_axis[::3], image.y_axis[::3], image.image[::3, ::3])
        p.set_clim(0, config['plot']['spectrum_intensity_max'])

    plot_spectrum_image(low_energy_image_nonoverlap_region)
    plot_spectrum_image(overlap_image)
    plot_spectrum_image(high_energy_image_nonoverlap_region)

    ax_pointing.set(xlabel="horizontal angle [mrad]", ylabel="vertical angle [mrad]")
    ax_spectrum.set(xlabel="energy [MeV]", ylabel="horizontal angle [mrad]")

    ax_spectrum_lineout = ax_spectrum.twinx()
    ax_spectrum_lineout.set(yticks=[])
    ax_spectrum_lineout.plot(spectrum_lineout_energy_axis, spectrum_lineout, color='yellow', alpha=0.7)
    ax_spectrum_lineout.set_ylim(0, config['plot']['spectrum_lineout_max'])

    return fig
