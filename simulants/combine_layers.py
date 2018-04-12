from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import copy
import Imath
import random
import OpenEXR
import colorsys
import datetime
import numpy as np

from PIL import Image, ImageOps, ImageChops
from skimage import color
from scipy import misc, ndimage
from argparse import ArgumentParser


def emoji_skin():
    """Skin colours from the 5 skin tone groups of emoji

    :return: list of 5 RGB tuples
    """
    f1 = (254, 215, 196)
    f2 = (223, 175, 145)
    f3 = (225, 164, 111)
    f4 = (148, 70, 32)
    f5 = (72, 33, 6)
    emoji_skin = [f1, f2, f3, f4, f5]

    return emoji_skin


def randomize_skin(original_skin):
    """Shift the hue of skin tone slightly for more variety

    :param original_skin: RGB tuple of a base skin tone
    :return: new RGB tuple of adjusted skin tone
    """
    r, g, b = original_skin[0]/255.0, original_skin[1]/255.0, original_skin[2]/255.0

    hsv_skin = colorsys.rgb_to_hsv(r, g, b)
    h, s, v = hsv_skin[0], hsv_skin[1], hsv_skin[2]

    h_new = h + random.uniform(-0.1, 0.1)
    rgb_new = colorsys.hsv_to_rgb(h_new, s, v)
    
    new_skin = (int(rgb_new[0]*255), int(rgb_new[1]*255), int(rgb_new[2]*255))
    
    return new_skin


def as_ndarray(image):
    """convert to ndarray if needed"""
    if type(image) == Image.Image:
        image = np.asarray(image)

    assert type(image) == np.ndarray, '{} is wrong type'.format(image)

    return image


def combine_with_color(original_image, item, color_block):
    """multiply image by color

    :param original_image: RGBA image
    :param item: L mask
    :param color_block: RGBA color block
    :return: RGBA combined image
    """
    assert original_image.mode == 'RGBA', 'image mode is {}'.format(original_image.mode)
    assert item.mode == 'L', 'mask mode is {}'.format(item.mode)
    assert color_block.mode == 'RGBA', 'color block mode is {}'.format(color_block.mode)

    colored_item = ImageChops.multiply(original_image, color_block)
    r, g, b, a = colored_item.split()

    masked_result = Image.merge('RGBA', (r, g, b, item))

    return colored_item


def skin_block(original_image, emoji_skin):
    """Return random block of emoji skin tone size of image"""
    original_image = as_ndarray(original_image)
    random_skin = random.choice(emoji_skin)
    random_skin = randomize_skin(random_skin)

    return Image.new('RGBA', original_image.shape[:2], color=random_skin)


def random_hsv_color(min_v, max_v):
    """random hsv color with min and max brightness value"""
    hsv = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(min_v, max_v))
    rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2])
    r = int(rgb[0] * 255)
    g = int(rgb[1] * 255)
    b = int(rgb[2] * 255)
    rgb = (r, g, b)

    return rgb


def color_block(original_image):
    """Return random block of color with uniform random chance HSV"""
    original_image = as_ndarray(original_image)
    rgb = random_hsv_color(0, 1)

    return Image.new('RGBA', original_image.shape[:2], color=rgb)


def convert_to_binary(image):
    """convert imageio Image into PIL L"""
    image = Image.frombytes(mode='L', size=image.shape[:2], data=image)

    return image


def colorize_hair(image, hair_mask):
    image = image.convert(mode='L')
    image = ImageOps.autocontrast(image, ignore=0)
    mid_point = random.uniform(0,1)
    dark = random_hsv_color(0, mid_point)
    light = random_hsv_color(mid_point, 1)
    colorized = ImageOps.colorize(image, dark, light)
    r, g, b = colorized.split()
    just_hair = Image.merge('RGBA', (r, g, b, hair_mask))

    return just_hair


def mask2rgba(alpha_image):
    """Convert 'L' mode image to 'RGBA' as stack"""
    rgba = np.asarray(alpha_image)
    ones = np.ones(rgba.shape)
    rgba = np.stack((ones, ones, ones, rgba), axis=2)

    return Image.fromarray(rgba.astype('uint8'))


def map_texture(texture_path, uv_map):
    """Use given UV map to map texture within mask area

    :param texture_path: path to a texture to use
    :param uv_map: OpenEXR image
    :return: PIL mode 'RGB' mapped texture
    """
    texture = misc.imread(texture_path)
    tex_size = texture.shape[0]

    # EXR handling
    pixel_type = Imath.PixelType(Imath.PixelType.FLOAT)
    data_window = uv_map.header()['dataWindow']
    size = (data_window.max.x - data_window.min.x + 1, data_window.max.y - data_window.min.y + 1)
    x_raw = uv_map.channel('R', pixel_type)
    y_raw = uv_map.channel('G', pixel_type)
    x_norm = Image.frombytes('F', size, x_raw)
    y_norm = Image.frombytes('F', size, y_raw)

    x_map = np.asarray(x_norm) * tex_size
    y_map = np.asarray(y_norm) * tex_size

    uv = np.stack([x_map, y_map], axis=2)
    uv = uv.transpose(2, 0, 1)

    mapped_r = ndimage.map_coordinates(texture[:, :, 0], uv, prefilter=False, order=0)
    mapped_g = ndimage.map_coordinates(texture[:, :, 1], uv, prefilter=False, order=0)
    mapped_b = ndimage.map_coordinates(texture[:, :, 2], uv, prefilter=False, order=0)

    mapped_texture = np.stack([mapped_r, mapped_g, mapped_b], axis=2)

    return Image.fromarray(mapped_texture, mode='RGB')


def blend_overlay(base_img, overlay_img, opacity):
    """Overlay blend of image and overlay image by factor of opacity

    :param img_in: PIL 'RGBA' mode image
    :param overlay_img: PIL 'RBBA' mode image
    :param opacity: float [0,1]
    :return: PIL RGBA
    """
    base_img = np.asarray(base_img).astype(np.float)
    overlay_img = np.asarray(overlay_img).astype(np.float)

    # sanity check of inputs
    assert base_img.dtype.kind == 'f', 'Input variable img_in should be of numpy.float type.'
    assert overlay_img.dtype.kind == 'f', 'Input variable overlay_img should be of numpy.float type.'
    assert base_img.shape[2] == 4, 'Input variable img_in should be of shape [:, :,4].'
    assert overlay_img.shape[2] == 4, 'Input variable overlay_img should be of shape [:, :,4].'
    assert 0.0 <= opacity <= 1.0, 'Opacity needs to be between 0.0 and 1.0.'

    base_img /= 255.0
    overlay_img /= 255.0

    comp_alpha = np.minimum(base_img[:, :, 3], overlay_img[:, :, 3]) * opacity
    new_alpha = base_img[:, :, 3] + (1.0 - base_img[:, :, 3]) * comp_alpha
    np.seterr(divide='ignore', invalid='ignore')
    ratio = comp_alpha / new_alpha
    ratio[ratio == np.NAN] = 0.0

    comp = base_img[:,:,:3] * (base_img[:,:,:3] + (2 * overlay_img[:,:,:3]) * (1 - base_img[:,:,:3]))

    ratio_rs = np.reshape(np.repeat(ratio, 3), [comp.shape[0], comp.shape[1], comp.shape[2]])
    img_out = comp * ratio_rs + base_img[:, :, :3] * (1.0 - ratio_rs)
    img_out = np.nan_to_num(np.dstack((img_out, base_img[:, :, 3])))  # add alpha channel and replace nans

    return Image.fromarray((img_out * 255).astype(np.uint8), mode='RGBA')


def make_clothed_person(image_path, body_path, shirt_path, pants_path, hair_path, ao_path, head_path,
                        pants_tex_path, shirt_tex_path, uv_path):
    """Generate compisited full person image with alpha

    :param image_path: path to base image (RGBA render of simulant)
    :param body_path: path to mask for body skin
    :param shirt_path: path to mask for shirt
    :param pants_path: path to mask for pants
    :param hair_path: path to mask for hair
    :param ao_path: path to RGBA ambient occlusion render
    :param head_path: path to head mask
    :param pants_tex_path: path to texture to use for pants
    :param shirt_tex_path: path to texture to use for shirt
    :param uv_path: path to EXR 32 bit UV render
    :return: tuple of full composite (RGBA), clothes mask (L), head mask (L), and non-head skin mask (L)
    """
    image = Image.open(image_path).convert('RGBA')
    body_alpha = Image.open(body_path).convert('L')
    shirt_alpha = Image.open(shirt_path).convert('L')
    pants_alpha = Image.open(pants_path).convert('L')
    hair_alpha = Image.open(hair_path).convert('L')
    head_alpha = Image.open(head_path).convert('L')
    ao = Image.open(ao_path).convert('RGBA')
    uv = OpenEXR.InputFile(uv_path)

    skin_mask = ImageChops.add(head_alpha, body_alpha)
    colored_skin = combine_with_color(image, skin_mask, skin_block(image, emoji_skin()))

    colored_hair = colorize_hair(image, hair_alpha)

    if pants_tex_path is not '':
        shirt_r, shirt_g, shirt_b = map_texture(shirt_tex_path, uv).split()
        colored_shirt = Image.merge('RGBA', (shirt_r, shirt_g, shirt_b, shirt_alpha))
        pants_r, pants_g, pants_b = map_texture(pants_tex_path, uv).split()
        colored_pants = Image.merge('RGBA', (pants_r, pants_g, pants_b, pants_alpha))

    else:
        colored_shirt = combine_with_color(image, shirt_alpha, color_block(image))
        colored_pants = combine_with_color(image, pants_alpha, color_block(image))

    colored_image = Image.alpha_composite(colored_skin, colored_hair)
    colored_image = Image.alpha_composite(colored_image, colored_shirt)
    colored_image = Image.alpha_composite(colored_image, colored_pants)

    composite = blend_overlay(colored_image, ao, 0.85)
    comp_r, comp_g, comp_b, _ = composite.split()

    whole_head_mask = ImageChops.add(hair_alpha, head_alpha)
    clothes_mask = ImageChops.add(shirt_alpha, pants_alpha)
    simulant_mask = ImageChops.add(whole_head_mask, clothes_mask)
    simulant_mask = ImageChops.add(simulant_mask, body_alpha)

    final_comp = Image.merge('RGBA', (comp_r, comp_g, comp_b, simulant_mask))

    return final_comp, clothes_mask, whole_head_mask, body_alpha


def image_size(image_path):
    """Return image size from path"""
    im = Image.open(image_path)

    return im.size


def blank_image(image_size):
    """Generate blank RGBA image of a given size"""
    blank = Image.new('RGBA', image_size)

    return blank


def new_person_size(person_size, bg_size, min_factor, max_factor):
    """Generate new (random) size for the person image that will fit within the bg"""
    person_w = person_size[0]
    person_h = person_size[1]
    assert person_h == person_w

    bg_w = bg_size[0]
    bg_h = bg_size[1]
    max_side = max(bg_w, bg_h) * max_factor
    min_size = min(bg_w, bg_h) * min_factor

    new_w = int(random.uniform(min_size, max_side))
    new_size = (new_w, new_w)

    return new_size


def resize_image(image, new_size):
    new_img = image.resize(new_size, resample=Image.NEAREST)

    return new_img


def rotate_image(image, angle):
    """Randomly rotate input image"""
    rot_image = image.rotate(angle, resample=Image.NEAREST)

    return rot_image


def new_ul_location(new_person_size, bg_size):
    """Generate new upper left location for person within bg with >50% image visible"""
    min_left = 0 - new_person_size[0] * 0.25
    max_left = bg_size[0] - new_person_size[0] * 0.75
    min_top = 0 - new_person_size[1] * 0.25
    max_top = bg_size[1] - new_person_size[1] * 0.75

    new_x = int(random.uniform(min_left, max_left))
    new_y = int(random.uniform(min_top, max_top))

    return (new_x, new_y)


def center_new_ul(person_size, bg_size):
    p_width, p_height = person_size
    b_width, b_height = bg_size

    w_delta = max((b_width - p_width), 0)
    h_delta = max((b_height - p_height), 0)

    x = int(w_delta / 2)
    y = int(h_delta / 2)

    return (x, y)


def new_part(image, new_size, new_rotation, new_xy, background_size):
    """Resize, rotate, and position image in a given background size"""
    resized_part = resize_image(image, new_size)
    rotated_part = rotate_image(resized_part, new_rotation)
    full_size = blank_image(background_size)
    full_size.paste(rotated_part, box=new_xy)

    return full_size


def mask_layer(mask, new_size, new_rotation, new_xy, background_size):
    """Create rotated, resized, positioned mask image"""
    resized_mask = resize_image(mask, new_size)
    rotated_mask = rotate_image(resized_mask, new_rotation)
    frame = Image.new('L', background_size)
    frame.paste(rotated_mask, box=new_xy)

    return frame


def generate_overlay(person, clothes_mask, head_mask, body_mask, bg_image_loc, type, scale_min=0.15, scale_max=2,
                     rotate_min=-180, rotate_max=180):
    """Generate randomly rotated, scaled overlay of simulant sized to composite on top of background image

    :param person: RGBA PIL of composited simulant
    :param clothes_mask: L PIL of clothes
    :param head_mask: RGBA L of head
    :param body_mask: RGBA L of body
    :param bg_image_loc: path to background image
    :param type: flag for video
    :param scale_min: minimum scale of overlaid simulant
    :param scale_max: maximum scale of overlaid simulant
    :param rotate_min: minimum rotation of overlaid simulant
    :param rotate_max: maximum rotation of overlaid simulant
    :return: tuple of fully clothed simulant (RGBA), clothes mask (L), head mask (L), and non-body skin mask (L)
    """
    person_size = person.size
    bg_size = image_size(bg_image_loc)

    new_size = new_person_size(person_size, bg_size, scale_min, scale_max)
    new_xy = new_ul_location(new_size, bg_size)
    new_rotation = random.uniform(rotate_min, rotate_max)

    if type == 'video':
        new_edge = min(bg_size)
        new_size = (new_edge, new_edge)
        new_xy = center_new_ul(new_size, bg_size)
        new_rotation = 0

    overlay = new_part(person, new_size, new_rotation, new_xy, bg_size)
    clothes_overlay_mask = mask_layer(clothes_mask, new_size, new_rotation, new_xy, bg_size)
    head_overlay_mask = mask_layer(head_mask, new_size, new_rotation, new_xy, bg_size)
    body_overlay_mask = mask_layer(body_mask, new_size, new_rotation, new_xy, bg_size)

    return overlay, clothes_overlay_mask, head_overlay_mask, body_overlay_mask


def generate_mask(foreground):
    """Generate 8bit grayscale mask image"""
    alpha = foreground.split()[-1]
    mask = Image.new('L', foreground.size, 0)
    mask.paste(alpha)

    return mask


def make_image_uint8(image):
    """make sure image is 255, uint8 formatted"""
    print('making uint8 from {}'.format(image.dtype))
    if image.dtype != 'uint8':
        print('image.dtype is not uint8')
        if np.max(image) <= 1:
            image = image * 255
        image = image.astype('uint8')

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


def random_crop(imgs, crop_factor=0.99, stddev=0.14):
    # Randomly crop image to simulate handshake jitter

    # make sure all images have the same size
    img_arrays = map(np.array, imgs)
    sizes = [i.shape[0:2] for i in img_arrays]
    assert len(set(sizes)) == 1
    image_size = np.array(sizes[0])

    # calculate cropped image size and a random offset from tl of the image
    crop_size = (crop_factor * image_size).astype(np.int)
    max_offset = image_size - crop_size
    random_offset = np.round(np.clip(np.random.normal(0.5, stddev, 2), 0, 1) * max_offset).astype(np.int)

    # convert into PIL's box format
    x1 = random_offset[1]
    y1 = random_offset[0]
    x2 = x1 + crop_size[1]
    y2 = y1 + crop_size[0]
    assert x1 >= 0
    assert y1 >= 0
    assert x2 <= image_size[1]
    assert y2 <= image_size[0]

    # crop the images
    cropped_imgs = [i.crop([x1, y1, x2, y2]) for i in imgs]
    return cropped_imgs


def mult_by_noise(image):
    np_image = np.asarray(image)
    new_image = np_image.copy()
    np_image_rgb = np_image[:, :, :3]
    noise = np.random.normal(loc=0.9, scale=0.1, size=np_image_rgb.shape)
    noisy_image = np_image_rgb * noise
    new_image[:, :, :3] = noisy_image[:, :, :3]

    return Image.fromarray(new_image, mode='RGBA')


def matching_method(foreground, background, method_setting):
    if method_setting == 'RGB':
        foreground = match_background_rgb(foreground, background)
    elif method_setting == 'LAB':
        foreground = match_background_lab(foreground, background)
    elif method_setting == 'HSV':
        foreground = match_background_hsv(foreground, background)
    elif method_setting == 'SAT':
        foreground = match_background_sat(foreground, background)
    elif method_setting == 'SATVAL':
        foreground = match_background_sat_val(foreground, background)
    else:
        pass

    return foreground


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--person', '-p', type=str, help='foreground person image', required=True)
    parser.add_argument('--skin_path', '-s', type=str, help='path to skin masks', required=True)
    parser.add_argument('--shirt_path', '-t', type=str, help='path to shirt masks', required=True)
    parser.add_argument('--pants_path', '-n', type=str, help='path to pants masks', required=True)
    parser.add_argument('--hair_path', '-r', type=str, help='path to hair masks', required=True)
    parser.add_argument('--ao_path', '-a', type=str, help='path to ambient occlusion', required=True)
    parser.add_argument('--background', '-b', type=str, help='background image', required=True)
    parser.add_argument('--composite', '-c', type=str, help='dir for composite output', required=True)
    parser.add_argument('--mask', '-m', type=str, help='dir for mask output', required=True)
    parser.add_argument('--uv', '-v', type=str, help='path to exr uv map', required=True)
    parser.add_argument('--type', '-y', type=str, help='set to video if using sequence', default='')
    parser.add_argument('--out_name', '-o', type=str, help='if set use this name for output', default='')
    parser.add_argument('--seed', '-d', type=str, help='seed to use for video', default='')
    parser.add_argument('--head', '-z', type=str, help='if set, save head mask', default='')
    parser.add_argument('--parts_out', '-w', type=str, help='output head, body, and cloth mask', default='')
    parser.add_argument('--p_tex', '-e', type=str, help='path for pants textures if set', default='')
    parser.add_argument('--s_tex', '-x', type=str, help='path for shirt textures if set', default='')
    parser.add_argument('--matching_method', '-u', type=str, help='method for matching fore/background', default='RGB')
    parser.add_argument('--noise_type', '-q', type=str, help='noise type to use', default='')
    args = parser.parse_args()

    if args.type == 'video':
        random.seed(args.seed)

    bg = Image.open(args.background).convert('RGBA')
    person, clothes, head, body = make_clothed_person(args.person, args.skin_path, args.shirt_path, args.pants_path,
                                                args.hair_path, args.ao_path, args.head, args.p_tex, args.s_tex, args.uv)
    foreground, clothes_mask, head_mask, body_mask = generate_overlay(person, clothes, head, body, args.background, args.type)

    foreground = matching_method(foreground, bg, args.matching_method)

    if args.noise_type == 'foreground':
        foreground = mult_by_noise(foreground)

    comp = Image.alpha_composite(bg, foreground)

    if args.noise_type == 'all':
        comp = mult_by_noise(comp)

    # Mask for entire foreground
    mask = generate_mask(foreground)

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    comp_id = 'simulant_{}'.format(timestamp)

    if args.out_name is not '':
        comp_id = args.out_name

    if args.parts_out is not '':
        head_mask = generate_mask(head_mask)
        cloth_mask = generate_mask(clothes_mask)
        body_mask = generate_mask(body_mask)
        cropped = random_crop([comp, mask, head_mask, cloth_mask, body_mask])
        cropped[2].save(os.path.join(args.parts_out, 'heads', comp_id + '.png'))
        cropped[3].save(os.path.join(args.parts_out, 'cloth', comp_id + '.png'))
        cropped[4].save(os.path.join(args.parts_out, 'body', comp_id + '.png'))
    else:
        cropped = random_crop([comp, mask])

    # Save composite image, mask, and annotation
    cropped[0].save(os.path.join(args.composite, comp_id + '.png'))
    cropped[1].save(os.path.join(args.mask, comp_id + '.png'))
