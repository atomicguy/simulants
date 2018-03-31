from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import numpy as np

from PIL import Image
from argparse import ArgumentParser


def image_list(path):
    file_list = []
    for file in os.listdir(path):
        # print(file)
        extension = os.path.splitext(file)[1]
        # print(extension)
        if extension.lower() == '.jpg':
            file_list.append(file)
        elif extension.lower() == '.tiff':
            file_list.append(file)
        elif extension.lower() == '.png':
            file_list.append(file)
        else:
            pass
    print('found {} files in {}'.format(len(file_list), path))

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


def ensure_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    return dir_path


def copy_frames(source_path, out_path):
    frames = sorted(image_list(source_path))
    print('writing to {}'.format(out_path))

    for i, frame in enumerate(frames):
        progress_bar((i+1)/len(frames))
        frame_path = os.path.join(source_path, frame)
        frame_image = Image.open(frame_path).convert('RGB')
        frame_image.save(os.path.join(out_path, '{}.png'.format(str(i).zfill(5))))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--sequences_path', '-m', type=str, help='directory of mask images to process')
    args, _ = parser.parse_known_args()

    sequences = sorted(os.listdir(args.sequences_path))
    for sequence in sequences:
        sequence_path = os.path.join(args.sequences_path, sequence, 'frames')
        out_path = os.path.join(args.sequences_path, sequence)
        copy_frames(sequence_path, out_path)

