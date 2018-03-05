from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import uuid
import random
import subprocess

from argparse import ArgumentParser


def list_files(path_to_annotations, file_extension):
    """Get list of files in a given directory"""
    file_list = []
    for file in os.listdir(path_to_annotations):
        if file.endswith('.' + file_extension):
            file_list.append(file)
    return file_list


def pick_random_images(background_dir):
    """Return paths to randomly chosen fore/background images"""
    background_list = list_files(background_dir, 'jpg')
    background_image = os.path.join(background_dir, random.choice(background_list))

    return background_image


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--input_dir', '-i', type=str, help='directory of foreground images')
    parser.add_argument('--background_dir', '-b', type=str, help='directory of background images')
    parser.add_argument('--out_dir', '-o', type=str, help='output directory')
    args = parser.parse_args()

    sequence_names = []
    for item in os.listdir(args.input_dir):
        if os.path.isdir(item):
            sequence_names.append(item)

    for sequence in sequence_names:
        input = os.path.join(args.input_dir, sequence)
        background = pick_random_images(args.background_dir)
        output = os.path.join(args.out_dir, sequence)

        cmd = ['python', 'composite_video.py',
               '--input', input,
               '--background', background,
               '--output', output]

        subprocess.check_call(cmd)
