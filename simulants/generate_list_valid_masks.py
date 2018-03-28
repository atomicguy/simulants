from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import numpy as np

from PIL import Image
from argparse import ArgumentParser


def list_files(path, extension):
    file_list = []
    for file in os.listdir(path):
        if file.endswith('.' + extension):
            file_list.append(file)

    return file_list


def progress_bar(progress, bar_length=30):
    """Displays or updates a console progress bar

    :param progress: a float percentage between 0 and 1 (i.e. halt to 100%).
    :param bar_length: characters wide the progress bar should be
    """
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(bar_length*progress))
    text = "\rPercent: [{0}] {1}% {2}".format("="*block + " "*(bar_length-block), round(progress*100, 4), status)
    sys.stdout.write(text)
    sys.stdout.flush()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--mask_path', '-m', type=str, help='directory of mask images to process')
    parser.add_argument('--out_path', '-o', type=str, help='directroy for output json files to go')
    args, _ = parser.parse_known_args()

    file_list = list_files(args.mask_path, 'png')
    valid_list = []

    for i, mask in enumerate(file_list):
        progress_bar((i+1)/len(file_list))
        mask_path = os.path.join(args.mask_path, mask)
        mask_img = Image.open(mask_path).convert('L')
        mask_np = np.asarray(mask_img)
        if np.max(mask_np) > 0:
            valid_list.append(os.path.splitext(mask)[0])

    with open(os.path.join(args.out_path, 'trainlist.txt'), 'w') as file_handler:
        for item in valid_list:
            file_handler.write('{}\n'.format(item))
