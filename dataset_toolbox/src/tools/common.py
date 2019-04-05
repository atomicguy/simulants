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
