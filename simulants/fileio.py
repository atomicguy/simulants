from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os


def image_list(path):
    """Add images of known types to list"""
    file_list = []
    for file in os.listdir(path):
        # print(file)
        extension = os.path.splitext(file)[1]
        # print(extension)
        if extension.lower() == '.tif':
            file_list.append(file)
        elif extension.lower() == '.tiff':
            file_list.append(file)
        elif extension.lower() == '.png':
            file_list.append(file)
        elif extension.lower() == '.jpg':
            file_list.append(file)
        else:
            pass
    print('found {} files in {}'.format(len(file_list), path))

    return file_list


def ensure_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    return dir_path