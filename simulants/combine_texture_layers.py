from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import copy
import random
import colorsys
import datetime
import numpy as np

from PIL import Image
from PIL import ImageChops
from scipy import misc
from scipy import ndimage
from argparse import ArgumentParser


def emoji_skin():
    f1 = (254, 215, 196)
    f2 = (223, 175, 145)
    f3 = (225, 164, 111)
    f4 = (148, 70, 32)
    f5 = (72, 33, 6)
    emoji_skin = [f1, f2, f3, f4, f5]

    return emoji_skin


def randomize_skin(original_skin):
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


def isolate_item(rendered_image, item_mask):
    """use given mask as an alpha for the rendered image
    rendered_image: RGBA ndimage
    item_mask: L ndimage
    masked_image: PIL RGBA image
    """
    rendered_image = as_ndarray(rendered_image)
    masked_image = copy.copy(rendered_image)
    masked_image[:, :, 3] = item_mask
    masked_image = Image.fromarray(masked_image)
    
    return masked_image


def combine_with_color(original_image, item, color_block):
    rendered_item = isolate_item(original_image, item)
    colored_item = ImageChops.multiply(rendered_item, color_block)

    return colored_item


def skin_block(original_image, emoji_skin):
    """Return random block of emoji skin tone size of image"""
    original_image = as_ndarray(original_image)
    random_skin = random.choice(emoji_skin)
    random_skin = randomize_skin(random_skin)

    return Image.new('RGBA', original_image.shape[:2], color=random_skin)


def color_block(original_image):
    """Return random block of color with uniform random chance HSV"""
    original_image = as_ndarray(original_image)
    hsv = (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
    rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], hsv[2])
    r = int(rgb[0] * 255)
    g = int(rgb[1] * 255)
    b = int(rgb[2] * 255)
    rgb = (r, g, b)

    return Image.new('RGBA', original_image.shape[:2], color=rgb)


def convert_to_binary(image):
    """convert imageio Image into PIL L"""
    image = Image.frombytes(mode='L', size=image.shape[:2], data=image)

    return image


def make_clothed_person(image_path, skin_path, shirt_path, pants_path, hair_path, ao_path, p_text, s_text):
    """Generate composited, colorized image from layer paths"""
    image = Image.open(image_path).convert('RGBA')
    skin = Image.open(skin_path).convert('L')
    shirt = Image.open(shirt_path).convert('L')
    pants = Image.open(pants_path).convert('L')
    hair = Image.open(hair_path).convert('L')
    ao = Image.open(ao_path).convert('RGBA')

    new_skin = combine_with_color(image, skin, skin_block(image, emoji_skin()))

    if p_text is not None:
        shirt_texture = Image.open(s_text).convert('RGBA')
        pants_texture = Image.open(p_text).convert('RGBA')
        new_shirt = combine_with_color(image, shirt, shirt_texture)
        new_pants = combine_with_color(image, pants, pants_texture)
    else:
        new_shirt = combine_with_color(image, shirt, color_block(image))
        new_pants = combine_with_color(image, pants, color_block(image))

    new_hair = combine_with_color(image, hair, color_block(image))

    clothes = Image.alpha_composite(new_shirt, new_pants)
    body = Image.alpha_composite(new_skin, new_hair)
    comp = Image.alpha_composite(body, clothes)
    comp = Image.alpha_composite(image, comp)
    comp = ImageChops.multiply(comp, ao)

    return comp, clothes


def image_size(image_path):
    """Return image size from path"""
    im = Image.open(image_path)

    return im.size


def blank_image(image_size):
    """Generate blank RGBA image of a given size"""
    blank = Image.new('RGBA', image_size)

    return blank


def new_person_size(person_size, bg_size):
    """Generate new (random) size for the person image that will fit within the bg"""
    person_w = person_size[0]
    person_h = person_size[1]
    assert person_h == person_w

    bg_w = bg_size[0]
    bg_h = bg_size[1]
    max_side = max(bg_w, bg_h) * 2
    min_size = min(bg_w, bg_h) * 0.15

    new_w = int(random.uniform(min_size, max_side))
    new_size = (new_w, new_w)

    return new_size


def resize_image(image, new_size):
    new_img = image.resize(new_size, resample=Image.BILINEAR)

    return new_img


def rotate_image(image, angle):
    """Randomly rotate input image"""
    rot_image = image.rotate(angle, resample=Image.BILINEAR)

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


def generate_overlay(person, clothes, bg_image_loc, type):
    """generate overlay image with resized person on blank alpha

    :param person: PIL RGBA image
    :param clothes: PIL RGBA image
    :param bg_image_loc: location of image to use for background
    :return: PIL RGBA image
    """
    person_size = person.size
    bg_size = image_size(bg_image_loc)

    new_size = new_person_size(person_size, bg_size)
    new_xy = new_ul_location(new_size, bg_size)
    new_rotation = random.uniform(0, 360)

    if type == 'video':
        new_edge = min(bg_size)
        new_size = (new_edge, new_edge)
        new_xy = center_new_ul(new_size, bg_size)
        new_rotation = 0

    resized_person = resize_image(person, new_size)
    resized_person = rotate_image(resized_person, new_rotation)

    resized_clothes = resize_image(clothes, new_size)
    resized_clothes = rotate_image(resized_clothes, new_rotation)

    overlay = blank_image(bg_size)
    overlay.paste(resized_person, box=new_xy)

    just_clothes = blank_image(bg_size)
    just_clothes.paste(resized_clothes, box=new_xy)

    return overlay, just_clothes


def generate_mask(foreground):
    """Generate 8bit grayscale mask image"""
    alpha = foreground.split()[-1]
    mask = Image.new('L', bg.size, 0)
    mask.paste(alpha)

    return mask


def make_image_uint8(image):
    """make sure image is 255, uint8 formatted"""
    if image.dtype != 'uint8':
        if np.max(image) <= 1:
            image = image * 255
        image = image.astype('uint8')

    return image


def cdf_norm(array, n_bins):
    """find the normalized cumulative distribution of array"""
    cdf = array.cumsum()
    cdf = (n_bins * cdf / cdf[-1]).astype(np.uint8)

    return cdf


def match_background_rgb(foreground_img, background_img):
    """use histogram matching to match the foreground more closely to background

    :param foreground_img: ndimage 4 channel array
    :param background_img: ndimage
    :return: PIL RGBA image
    """
    foreground_img = as_ndarray(foreground_img)
    background_img = as_ndarray(background_img)

    foreground = make_image_uint8(foreground_img)
    foreground_rgb = foreground[:, :, :3]
    foreground_a = foreground[:, :, 3]

    background = make_image_uint8(background_img)

    n_bins = 255

    matched = foreground.copy()

    for d in range(foreground_rgb.shape[2]):
        f_hist, bins = np.histogram(foreground_rgb[:, :, d].flatten(), bins=n_bins, density=True,
                                    weights=foreground_a.flatten())
        b_hist, bins = np.histogram(background[:, :, d], bins=n_bins, density=True)

        cdf_f = cdf_norm(f_hist, n_bins)
        cdf_b = cdf_norm(b_hist, n_bins)

        im2 = np.interp(foreground_rgb[:, :, d].flatten(), bins[:-1], cdf_f)
        im3 = np.interp(im2, cdf_b, bins[:-1])

        matched[:, :, d] = im3.reshape((foreground.shape[0], foreground.shape[1]))

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

    foreground = make_image_uint8(foreground_img)
    foreground_rgb = foreground[:, :, :3]
    foreground_lab = color.rgb2lab(foreground_rgb)
    foreground_a = foreground[:, :, 3]

    background = make_image_uint8(background_img)
    background_lab = color.rgb2lab(background[:, :, :3])

    n_bins = 255

    matched = foreground.copy()
    matched_lab = foreground_lab.copy()

    for d in range(foreground_rgb.shape[2]):
        f_hist, bins = np.histogram(foreground_lab[:, :, d].flatten(), bins=n_bins, density=True,
                                    weights=foreground_a.flatten())
        b_hist, bins = np.histogram(background_lab[:, :, d], bins=n_bins, density=True)

        cdf_f = cdf_norm(f_hist, n_bins)
        cdf_b = cdf_norm(b_hist, n_bins)

        im2 = np.interp(foreground_lab[:, :, d].flatten(), bins[:-1], cdf_f)
        im3 = np.interp(im2, cdf_b, bins[:-1])

        matched[:, :, d] = im3.reshape((foreground.shape[0], foreground.shape[1]))

    foreground_lab[:, :, :3] = matched_lab[:, :, :3]
    foreground_corrected = color.lab2rgb(matched_lab)
    foreground_corrected = foreground_corrected * 255
    matched[:, :, :3] = foreground_corrected[:, :, :3]

    return Image.fromarray(matched)


def random_crop(imgs, crop_factor=0.99, stddev=0.14):

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
    cropped_imgs = [i.crop([x1,y1,x2,y2]) for i in imgs]
    return cropped_imgs

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
    parser.add_argument('--type', '-y', type=str, help='set to video if using sequence', default='')
    parser.add_argument('--out_name', '-o', type=str, help='if set use this name for output', default='')
    parser.add_argument('--seed', '-d', type=str, help='seed to use for video', default='')
    parser.add_argument('--p_text', '-e', type=str, help='path for clothing textures', default='')
    parser.add_argument('--s_text', '-x', type=str, help='path for clothing textures', default='')
    parser.add_argument('--matching_method', '-z', type=str, help='method for matching fore/background', defalut='RGB')
    args = parser.parse_args()

    if args.type == 'video':
        random.seed(args.seed)

    bg = Image.open(args.background).convert('RGBA')
    person, clothes = make_clothed_person(args.person, args.skin_path, args.shirt_path, args.pants_path, args.hair_path,
                                          args.ao_path, args.p_text, args.s_text)
    foreground, clothes_mask = generate_overlay(person, clothes, args.background, args.type)

    # color match
    if args.matching_method is 'RGB':
        foreground = match_background_rgb(foreground, bg)
    elif args.matching_method is 'LAB':
        foreground = match_background_lab(foreground, bg)
    else:
        print('no matching method specified')

    comp = Image.alpha_composite(bg, foreground)

    # Set to foreground for all person mask, or clothes for clothing mask
    mask = generate_mask(foreground)

    # Randomly crop both mask and image to simulate handshake jitter
    # cropped = random_crop([comp, mask])
    cropped = [comp, mask]

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    comp_id = 'simulant_{}'.format(timestamp)
    if args.out_name is not '':
        comp_id = args.out_name

    # Save composite image, mask, and annotation
    cropped[0].save(os.path.join(args.composite, comp_id + '.png'))
    cropped[1].save(os.path.join(args.mask, comp_id + '.png'))
