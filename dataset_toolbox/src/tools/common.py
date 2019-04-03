from __future__ import division, absolute_import, print_function

import json
import os
import glob


def find_filepaths(path, extension):
    return glob.glob('%s/*.%s' % (path, extension))


def find_filenames(path, extension):
    return [os.path.basename(path) for path in find_filepaths(path, extension)]


def mkdirp(path):
    """Checks if a directory exists and if not creates the directory"""
    if not os.path.exists(path):
        os.makedirs(path)

    return path


def get_list(path):
    """Return each line of text file as a list"""
    with open(path) as f:
        list = f.readlines()
    list = [x.strip() for x in list]

    return list


def get_image_crop_target(image_size, target_aspect_ratio):
    """Find best fit crop size for given image and aspect ratio"""
    image_width = image_size[0]
    image_height = image_size[1]
    assert image_width > 0
    assert image_height > 0
    image_aspect_ratio = image_width / image_height
    if image_aspect_ratio > target_aspect_ratio:
        # image wider than target ratio, keep height
        target_height = image_height
        target_width = image_height * target_aspect_ratio
    elif image_aspect_ratio == target_aspect_ratio:
        # image is already target ratio, keep size
        target_height = image_height
        target_width = image_width
    else:
        # image taller than target ratio, keep width
        target_height = image_width * 1 / target_aspect_ratio
        target_width = image_width
    target_size = [target_width, target_height]
    # print('target size:', target_size)
    return target_size


def load_keep_dict(launch_location):
    """Load the correct keep dictionary"""
    if launch_location == 'run':
        base_path = './config/'
    elif launch_location == 'test':
        base_path = './config/'
    else:
        base_path = '../config/'
    try:
        file_path = os.path.join(base_path, 'keep_list.json')
        # print('file path is', os.path.abspath(file_path))
        with open(file_path) as jd:
            keep_dict = json.load(jd)
    except:
        print('no json data for file')
        keep_dict = {}

    return keep_dict


def load_convert_dict(launch_location):
    """Load the correct conversion dictionary"""
    if launch_location == 'run':
        base_path = './config/'
    elif launch_location == 'test':
        base_path = './config/'
    else:
        base_path = '../config/'
    try:
        file_path = os.path.join(base_path, 'convert_dict.json')
        # print('file path is', os.path.abspath(file_path))
        with open(file_path) as jd:
            keep_dict = json.load(jd)
    except:
        print('no json data for file')
        keep_dict = {}

    return keep_dict
