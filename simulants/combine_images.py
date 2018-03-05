from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import json
import random
import datetime
import numpy as np

from PIL import Image
from scipy import misc
from scipy import ndimage
from argparse import ArgumentParser


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
    max_side = max(bg_w, bg_h)
    min_size = min(bg_w, bg_h) * 0.10

    new_w = int(random.uniform(min_size, max_side))
    new_size = (new_w, new_w)

    return new_size


def resize_image(image, new_size):
    new_img = image.resize(new_size, resample=Image.BILINEAR)

    return new_img


def rotate_image(image):
    """Randomly rotate input image"""
    rot_angle = random.uniform(0, 360)
    rot_image = image.rotate(rot_angle, resample=Image.BILINEAR)

    return rot_image


def new_ul_location(new_person_size, bg_size):
    """Generate new upper left location for person within bg with >50% image visible"""
    min_left = 0 - new_person_size[0] / 2
    max_left = bg_size[0] - new_person_size[0] / 2
    min_top = 0 - new_person_size[1] / 2
    max_top = bg_size[1] - new_person_size[1] / 2

    new_x = int(random.uniform(min_left, max_left))
    new_y = int(random.uniform(min_top, max_top))

    return (new_x, new_y)


def generate_overlay(person_image_loc, bg_image_loc):
    """Generate overlay image with resized person on blank alpha"""
    person = Image.open(person_image_loc)
    person_size = person.size
    bg_size = image_size(bg_image_loc)

    new_size = new_person_size(person_size, bg_size)
    new_xy = new_ul_location(new_size, bg_size)

    resized_person = resize_image(person, new_size)
    resized_person = rotate_image(resized_person)

    overlay = blank_image(bg_size)
    overlay.paste(resized_person, box=new_xy)

    return overlay


def generate_mask(foreground):
    """Generate 8bit grayscale mask image"""
    alpha = foreground.split()[-1]
    mask = Image.new('L', bg.size, 0)
    mask.paste(alpha)

    return mask


def find_bbox(mask):
    mask_np = np.array(mask)
    slice_x, slice_y = ndimage.find_objects(mask_np == 1)[0]
    bbox = {'xmin': slice_x.start, 'xmax': slice_x.stop,
            'ymin': slice_y.start, 'ymax': slice_y.stop}

    return bbox


def generate_annotation(comp_id, mask):
    annotation = []
    annotation.append({'filename': comp_id + '.png'})
    bbox = find_bbox(mask)
    annotation.append({'annotations': [{'person': bbox}]})

    return annotation


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--person', '-p', type=str, help='foreground person image', required=True)
    parser.add_argument('--background', '-b', type=str, help='background image', required=True)
    parser.add_argument('--composite', '-c', type=str, help='dir for composite output', required=True)
    parser.add_argument('--mask', '-m', type=str, help='dir for mask output', required=True)
    parser.add_argument('--anno', '-a', type=str, help='dir for annotation output', required=True)
    args = parser.parse_args()

    bg = Image.open(args.background).convert('RGBA')
    foreground = generate_overlay(args.person, args.background)

    comp = Image.alpha_composite(bg, foreground)
    mask = generate_mask(foreground)

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    comp_id = 'simulant_{}'.format(timestamp)
    annotation = generate_annotation(comp_id, mask)

    # Save composite image, mask, and annotation
    comp.save(os.path.join(args.composite, comp_id + '.png'))
    mask.save(os.path.join(args.mask, comp_id + '.png'))
    with open(os.path.join(args.anno, comp_id + '.json'), 'w') as outfile:
        json.dump(annotation, outfile, indent=2)