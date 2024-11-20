from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import NamedTuple, Callable
from functools import partial

import matplotlib.pyplot as plt
import numpy as np
import tifffile

from .settings import load_config
from .utils.functools import compose

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
        # first check if axes need to be flipped
        if image.x_axis[-1] < image.x_axis[0]:
            image = ImageWithAxes(image.image[:, ::-1], image.x_axis[::-1], image.y_axis)

        if image.y_axis[-1] < image.y_axis[0]:
            image = ImageWithAxes(image.image[::-1, :], image.x_axis, image.y_axis[::-1])

        # only run sort operation if axes aren't sorted already
        if np.any(np.diff(image.x_axis) < 0):
            x_sort_i = np.argsort(image.x_axis)
            image = ImageWithAxes(image.image[:, x_sort_i], image.x_axis[x_sort_i], image.y_axis)

        if np.any(np.diff(image.y_axis) < 0):
            y_sort_i = np.argsort(image.y_axis)
            image = ImageWithAxes(image.image[y_sort_i, :], image.x_axis, image.y_axis[y_sort_i])

        return image

    low_energy_image = sort_axes_if_necessary(low_energy_image)
    high_energy_image = sort_axes_if_necessary(high_energy_image)

    assert low_energy_image.x_axis[0] < high_energy_image.x_axis[0] and low_energy_image.x_axis[-1] < high_energy_image.x_axis[-1], "Low energy image should have lower energy axis than high energy image"

    def interpolate_and_stitch_image_in_overlap_region(image_with_common_y_axis: ImageWithAxes, image_to_interpolate: ImageWithAxes) -> ImageWithAxes:
        """ Interpolate the image_to_interpolate onto the common axis of image_with_common_axis """

        def interpolate_one_column(image_column_values: np.ndarray) -> np.ndarray:
            return np.interp(image_with_common_y_axis.y_axis,  image_to_interpolate.y_axis, image_column_values, left=np.nan, right=np.nan)
        interpolated_image = ImageWithAxes(
            np.apply_along_axis(interpolate_one_column, axis=0, arr=image_to_interpolate.image),
            image_to_interpolate.x_axis,
            image_with_common_y_axis.y_axis
        )

        image = np.hstack([image_with_common_y_axis.image, interpolated_image.image])
        x_axis = np.concatenate([image_with_common_y_axis.x_axis, interpolated_image.x_axis])
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
    high_energy_image_overlap_region, high_energy_image_nonoverlap_region = split_image_along_x_axis(high_energy_image, low_energy_image.x_axis[-1])

    # use the finer y-axis of the two for the common y-axis
    def mean_y_axis_resolution(image: ImageWithAxes) -> float:
        return (image.y_axis[-1] - image.y_axis[0]) / (len(image.y_axis) - 1)
    if mean_y_axis_resolution(low_energy_image) < mean_y_axis_resolution(high_energy_image):
        overlap_image = interpolate_and_stitch_image_in_overlap_region(low_energy_image_overlap_region, high_energy_image_overlap_region)
    else:
        overlap_image = interpolate_and_stitch_image_in_overlap_region(high_energy_image_overlap_region, low_energy_image_overlap_region)

    return low_energy_image_nonoverlap_region, overlap_image, high_energy_image_nonoverlap_region

def preprocess_spectrum_images(low_energy_image: ImageWithAxes, high_energy_image: ImageWithAxes, 
                               low_energy_background: float = 1.674e-03, high_energy_background: float = 1.030e-03, intensity_scale_factor: float = 0.8221
                              ) -> tuple[ImageWithAxes, ImageWithAxes]:
    """ Background-subtracts and normalizes spectrum images

    Only used for data before 2024-11-01, because the data after that date is
    background-subtracted and normalized by energy bin width and angle bin width
    in the (Python) electron spectrometer image analyzer.

    Parameters
    ----------
    low_energy_image : ImageWithAxes
    high_energy_image : ImageWithAxes

    low_energy_background : float
    high_energy_background : float
        Subtract these background values from the spectrum image before adjusting 
        by energy and angle bin widths

    intensity_scale_factor : float
        Multiply the low energy image by this factor to match the intensity of 
        the high energy image

    Returns
    -------
    low_energy_image : ImageWithAxes
    high_energy_image : ImageWithAxes

    """
    
    def preprocess_spectrum_image(spectrum_image: ImageWithAxes, background: float = None) -> ImageWithAxes:
        """ Preprocess the spectrum image before analysis 
        
        Preprocessing involves the steps:
        - flip the axes if necessary
        - remove duplicate axes values
            if the x-axis or y-axis has duplicate values, remove those rows or 
            columns
        - adjust image values to axes
            adjust the image values from brightness/px^2 to brightness/MeV/mrad
        - remove values on x-axis edges

        Copied from https://github.com/TAUSystems/image-processing-backend/blob/6b024f1d138f66cdfbbe180d7d8bf5a74e581bbe/applications/rq_worker/src/analyzers/electron_spectrometer.py#L169

        """


        # flip axes if necessary
        def flip_axes(spectrum: ImageWithAxes) -> ImageWithAxes:
            spectrum_out = ImageWithAxes(
                image = spectrum.image,
                x_axis = spectrum.x_axis,
                y_axis = spectrum.y_axis
            )

            if spectrum_out.x_axis[0] > spectrum_out.x_axis[-1]:
                spectrum_out = ImageWithAxes(
                    image = np.flip(spectrum_out.image, axis=1),
                    x_axis = np.flip(spectrum_out.x_axis),
                    y_axis = spectrum_out.y_axis
                )

            if spectrum_out.y_axis[0] > spectrum_out.y_axis[-1]:
                spectrum_out = ImageWithAxes(
                    image = np.flip(spectrum_out.image, axis=0),
                    x_axis = spectrum_out.x_axis,
                    y_axis = np.flip(spectrum_out.y_axis)
                )

            assert np.all(np.diff(spectrum_out.x_axis) >= 0), "Error in flip_axes: x-axis is not monotonic."
            assert np.all(np.diff(spectrum_out.y_axis) >= 0), "Error in flip_axes: y-axis is not monotonic."

            return spectrum_out

        def remove_duplicate_axes_values(spectrum: ImageWithAxes) -> ImageWithAxes:
            # np.diff(x) > 0  is a boolean array that is one element shorter than x
            # add a True to the end so that the last element is always kept
            sx = np.append(np.diff(spectrum.x_axis) > 0, True)
            sy = np.append(np.diff(spectrum.y_axis) > 0, True)

            return ImageWithAxes(
                image = spectrum.image[sy][:, sx],
                x_axis = spectrum.x_axis[sx],
                y_axis = spectrum.y_axis[sy]
            )

        def subtract_background(spectrum: ImageWithAxes, background: float = None) -> ImageWithAxes:
            if background is None:
                # for now, just subtract the minimum column-wise average, keeping
                # the image non-negative. 
                # This must happen before adjusting image values because background 
                # is assumed to be constant per pixel, not per MeV/mrad
                # TODO: more advanced background subtraction
                background = np.min(np.mean(spectrum.image, axis=0))
                
            background_subtracted_image = spectrum.image - background
            return ImageWithAxes(
                image = background_subtracted_image,
                x_axis = spectrum.x_axis,
                y_axis = spectrum.y_axis
            )

        # adjust image values from brightness/px^2 to brightness/MeV/mrad
        def adjust_image_values_to_axes(spectrum: ImageWithAxes) -> ImageWithAxes:
            return ImageWithAxes(
                image = spectrum.image / np.gradient(spectrum.x_axis)[None, :] / np.gradient(spectrum.y_axis)[:, None],
                x_axis = spectrum.x_axis,
                y_axis = spectrum.y_axis
            )

        # remove values on x-axis edges, because they can have interpolation artifacts
        def remove_values_on_xaxis_edges(spectrum: ImageWithAxes) -> ImageWithAxes:
            return ImageWithAxes(
                image = spectrum.image[:, 1:-1],
                x_axis = spectrum.x_axis[1:-1],
                y_axis = spectrum.y_axis
            )

        process_spectrum: Callable[[ImageWithAxes], ImageWithAxes] = compose(
            flip_axes, 
            remove_duplicate_axes_values,
            partial(subtract_background, background=background),
            adjust_image_values_to_axes,
            remove_values_on_xaxis_edges,
        )

        return process_spectrum(spectrum_image)

    low_energy_image, high_energy_image = preprocess_spectrum_image(low_energy_image, background=low_energy_background), preprocess_spectrum_image(high_energy_image, background=high_energy_background)

    # scale low energy image to match intensity of high energy image
    low_energy_image = ImageWithAxes(
        image = low_energy_image.image * intensity_scale_factor,
        x_axis = low_energy_image.x_axis,
        y_axis = low_energy_image.y_axis
    )

    return low_energy_image, high_energy_image


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

    if burst_timestamp < datetime(2024, 11, 2, 1, 6, 32):  # deployed rq-worker:1231fa7 at this time
        low_energy_image, high_energy_image = preprocess_spectrum_images(low_energy_image, high_energy_image)

    low_energy_image_nonoverlap_region, overlap_image, high_energy_image_nonoverlap_region = stitch_spectrum_images(low_energy_image, high_energy_image)

    fig = plt.figure(figsize=(18, 4.5), num='pointing_and_spectrum'); fig.clf()
    ax_pointing = fig.add_axes((0.05, 0.10, 0.20, 0.80))
    ax_spectrum = fig.add_axes((0.30, 0.10, 0.68, 0.80))

    p = ax_pointing.pcolormesh(pointing_image.x_axis[::3], pointing_image.y_axis[::3], pointing_image.image[::3, ::3])
    p.set_clim(0, config['plot']['pointing_intensity_max'])

    def plot_spectrum_image(image: ImageWithAxes) -> None:
        if not image.image.size:
            return
        p = ax_spectrum.pcolormesh(image.x_axis[::3], image.y_axis[::3], image.image[::3, ::3])
        p.set_clim(0, config['plot']['spectrum_intensity_max'])

    # plot_spectrum_image(low_energy_image_nonoverlap_region)
    plot_spectrum_image(low_energy_image)
    # plot_spectrum_image(overlap_image)
    plot_spectrum_image(high_energy_image_nonoverlap_region)

    ax_pointing.set(xlabel="horizontal angle [mrad]", ylabel="vertical angle [mrad]")
    ax_spectrum.set(xlabel="energy [MeV]", ylabel="horizontal angle [mrad]")

    ax_spectrum_lineout = ax_spectrum.twinx()
    ax_spectrum_lineout.set(yticks=[])
    ax_spectrum_lineout.plot(spectrum_lineout_energy_axis, spectrum_lineout, color='yellow', alpha=0.7)
    ax_spectrum_lineout.set_ylim(0, config['plot']['spectrum_lineout_max'])

    return fig
