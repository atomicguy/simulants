from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import numpy as np

from PIL import Image
from skimage import color


def as_ndarray(image):
    """convert to ndarray if needed"""
    if type(image) == Image.Image:
        image = np.asarray(image)

    assert type(image) == np.ndarray, '{} is wrong type'.format(image)

    return image


def cdf_norm(array, bins):
    """find the normalized cumulative distribution of array"""
    cdf = array.cumsum()
    cdf = (bins * cdf / cdf[-1]).astype(np.uint8)

    return cdf


def match_channels(foreground, background, n_bins):
    """Use Histogram Matching to match foreground and background images by channel

    :param foreground: 4 channel ndarray image (i.e. RGBA, LABA, etc)
    :param background: background in same format as foreground
    :param n_bins: number of bins to match (usually 255)
    :return: histogram matched image in same format as original (RGBA etc)
    """

    # Ensure correct data types
    assert foreground.dtype == background.dtype, 'foreground and background cannot be different dtypes'

    matched = foreground.copy()
    foreground_3 = foreground[:, :, :3]
    foreground_alpha = foreground[:, :, 3]

    for d in range(foreground_3.shape[2]):
        f_hist, bins = np.histogram(foreground_3[:, :, d].flatten(), bins=n_bins, density=True,
                                    weights=foreground_alpha.flatten())
        b_hist, bins = np.histogram(background[:, :, d], bins=n_bins, density=True)

        cdf_f = cdf_norm(f_hist, n_bins)
        cdf_b = cdf_norm(b_hist, n_bins)

        im2 = np.interp(foreground_3[:, :, d].flatten(), bins[:-1], cdf_f)
        im3 = np.interp(im2, cdf_b, bins[:-1])

        matched[:, :, d] = im3.reshape((foreground.shape[0], foreground.shape[1]))

    return matched


def match_background_rgb(foreground_img, background_img):
    """use histogram matching to match the foreground more closely to background

    :param foreground_img: ndimage 4 channel array
    :param background_img: ndimage
    :return: PIL RGBA image
    """

    foreground_img = as_ndarray(foreground_img)
    background_img = as_ndarray(background_img)
    n_bins = 255

    matched = match_channels(foreground_img, background_img, n_bins)
    matched = Image.fromarray(matched)

    return matched


def match_background_lab(foreground_img, background_img):
    """use lab histogram matching to match the foreground contrast more closely to background

    :param foreground_img: ndimage 4 channel array
    :param background_img: ndimage
    :return: PIL RGBA image
    """

    foreground_img = as_ndarray(foreground_img)
    background_img = as_ndarray(background_img)
    n_bins = 255

    foreground_img_lab = color.rgb2lab(foreground_img[:, :, :3])
    background_img_lab = color.rgb2lab(background_img[:, :, :3])
    foreground_alpha = np.expand_dims(foreground_img[:, :, 3], 2)
    foreground_img_laba = np.concatenate((foreground_img_lab, foreground_alpha), axis=2)

    matched = match_channels(foreground_img_laba, background_img_lab, n_bins)
    matched_rgb = color.lab2rgb(matched[:, :, :3]) * 255
    matched[:, :, :3] = matched_rgb[:, :, :3]
    matched = Image.fromarray(matched.astype('uint8'))

    return matched


def match_background_hsv(foreground_img, background_img):
    """use hsv histogram matching to match the foreground contrast more closely to background

    :param foreground_img: ndimage 4 channel array
    :param background_img: ndimage
    :return: PIL RGBA image
    """

    foreground_img = as_ndarray(foreground_img)
    background_img = as_ndarray(background_img)
    n_bins = 255

    foreground_img_hsv = color.rgb2hsv(foreground_img[:, :, :3])
    background_img_hsv = color.rgb2hsv(background_img[:, :, :3])
    foreground_alpha = np.expand_dims(foreground_img[:, :, 3], 2)
    foreground_img_hsva = np.concatenate((foreground_img_hsv, foreground_alpha), axis=2)

    matched = match_channels(foreground_img_hsva, background_img_hsv, n_bins)
    matched_rgb = color.hsv2rgb(matched[:, :, :3]) * 255
    matched[:, :, :3] = matched_rgb[:, :, :3]
    matched = Image.fromarray(matched.astype('uint8'))

    return matched


def match_background_sat(foreground_img, background_img):
    """histogram match just saturation

    :param foreground_img: ndimage 4 channel array
    :param background_img: ndimage
    :return: PIL RGBA image
    """

    foreground_img = as_ndarray(foreground_img)
    background_img = as_ndarray(background_img)
    n_bins = 255

    foreground_img_hsv = color.rgb2hsv(foreground_img[:, :, :3])
    background_img_hsv = color.rgb2hsv(background_img[:, :, :3])
    foreground_alpha = np.expand_dims(foreground_img[:, :, 3], 2)
    foreground_img_hsva = np.concatenate((foreground_img_hsv, foreground_alpha), axis=2)

    matched = match_channels(foreground_img_hsva, background_img_hsv, n_bins)
    matched[:, :, 0] = foreground_img_hsv[:, :, 0]
    matched[:, :, 2] = foreground_img_hsv[:, :, 2]
    matched_rgb = color.hsv2rgb(matched[:, :, :3]) * 255
    matched[:, :, :3] = matched_rgb[:, :, :3]
    matched = Image.fromarray(matched.astype('uint8'))

    return matched


def match_background_sat_val(foreground_img, background_img):
    """histogram match just saturation

    :param foreground_img: ndimage 4 channel array
    :param background_img: ndimage
    :return: PIL RGBA image
    """

    foreground_img = as_ndarray(foreground_img)
    background_img = as_ndarray(background_img)
    n_bins = 255

    foreground_img_hsv = color.rgb2hsv(foreground_img[:, :, :3])
    background_img_hsv = color.rgb2hsv(background_img[:, :, :3])
    foreground_alpha = np.expand_dims(foreground_img[:, :, 3], 2)
    foreground_img_hsva = np.concatenate((foreground_img_hsv, foreground_alpha), axis=2)

    matched = match_channels(foreground_img_hsva, background_img_hsv, n_bins)
    matched[:, :, 0] = foreground_img_hsv[:, :, 0]
    matched_rgb = color.hsv2rgb(matched[:, :, :3]) * 255
    matched[:, :, :3] = matched_rgb[:, :, :3]
    matched = Image.fromarray(matched.astype('uint8'))

    return matched