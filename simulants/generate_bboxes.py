from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import json
import numpy as np

from scipy import misc
from argparse import ArgumentParser


def list_files(path, extension):
    file_list = []
    for file in os.listdir(path):
        if file.endswith('.' + extension):
            file_list.append(file)

    return file_list


def histograms(mask):
    """
    computes histogram of binaries images along y axis
    (vertical downward) and x axis (horizontal forward)

    returns a tuple of np.arrays (histo_y, histo_x)

    """

    histogram_y = np.dot(mask, np.ones((mask.shape[1], 1)))
    histogram_x = np.dot(mask.T, np.ones((mask.shape[0], 1)))

    return (histogram_y, histogram_x)


def min_max(one_dimensional_array):
    """
    computes the coordinate of the first and last non null
    element in a list or one dimmentional array

    returns a tuple (x_min, x_max)

    """

    x_min = 0
    x_max = len(one_dimensional_array) - 1

    done_min = False
    done_max = False

    count = 0
    
    while(True):
        
        if one_dimensional_array[x_min] == 0 and done_min == False and x_min < len(one_dimensional_array) - 1:
            x_min += 1
        else:
            done_min = True
        if one_dimensional_array[x_max] == 0 and done_max == False and x_max > 0:
            x_max -= 1
        else:
            done_max = True
        if done_min == True and done_max == True:
            return (x_min, x_max)

        count += 1

        if count > 10000:
            print("over 10000 null elements in list")
            return (x_min, x_max)

        if x_min > x_max:
            print("only null elements here")
            return (0, 0)


def get_mask(path):
    """read in mask image and make sure it is binary"""
    mask = misc.imread(path)
    assert len(mask.shape) == 2, 'mask {} is not binary'.format(path)

    return mask


def normalize_bbox(bbox, mask_shape):
    """[xmin, xmax, ymin, ymax] bbox and (height, width) shape"""
    xmin, xmax, ymin, ymax = bbox

    im_h, im_w = mask_shape
    # subtract one to match 0 indexed arrays
    im_h = im_h - 1
    im_w = im_w - 1

    # bbox width, height
    width = xmax - xmin
    height = ymax - ymin

    x_norm = xmin / im_w
    y_norm = ymin / im_h
    w_norm = width / im_w
    h_norm = height / im_h

    return {'x': x_norm, 'y': y_norm, 'width': w_norm, 'height': h_norm}


def generate_annotation(path):
    mask = get_mask(path)
    histogram_y, histogram_x = histograms(mask)
    xmin, xmax = min_max(histogram_x)
    ymin, ymax = min_max(histogram_y)
    bbox = (xmin, xmax, ymin, ymax)
    normalized_bbox = normalize_bbox(bbox, mask.shape)

    image_h, image_w = mask.shape
    file_name = os.path.split(path)[1]

    file_info = {'filename': file_name, 'width': image_w, 'height': image_h}

    annotation = {'file_info': file_info, 'annotations': {'person': normalized_bbox}}

    return annotation


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--mask_path', '-m', type=str, help='directory of mask images to process')
    parser.add_argument('--out_path', '-o', type=str, help='directroy for output json files to go')
    args, _ = parser.parse_known_args()

    file_list = list_files(args.mask_path, 'png')
    for mask in file_list:
        file_id = os.path.splitext(mask)[0]
        print('processing {}'.format(file_id))

        annotation = generate_annotation(os.path.join(args.mask_path, mask))

        with open(os.path.join(args.out_path, file_id + '.json'), 'w') as file:
            json.dump(annotation, file, indent=2)

