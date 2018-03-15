from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import math
import random
import numpy as np

from PIL import Image
from argparse import ArgumentParser


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--input', '-i', type=str, help='input image', required=True)
    parser.add_argument('--output', '-o', type=str, help='output directory', required=True)
    parser.add_argument('--number_frames', '-n', type=str, help='number of frames to generate', required=True)
    args = parser.parse_args()

    number_frames = int(args.number_frames)

    image_name = os.path.splitext(os.path.split(args.input)[1])[0]

    background = Image.open(args.input)
    width, height = background.size

    short_side = min(width, height)
    long_side = max(width, height)

    width_new = int(short_side * 0.9)
    height_new = width_new
    size_new = np.array([height_new, width_new])

    width_delta = width - width_new
    height_delta = height - height_new

    direction = random.choice(['horiz', 'vert', 'diag'])

    if direction is 'horiz':
        distance = [0, width_delta]
    elif direction is 'vert':
        distance = [height_delta, 0]
    elif direction is 'diag':
        distance = [height_delta, width_delta]
    else:
        print('something has gone wrong and a random direction was not chosen')

    step_size = np.array(distance) / number_frames

    motion = random.choice(['forward', 'backward'])

    # print('moving {} in {} direction at step size of {}'.format(motion, direction, step_size))

    for frame in range(number_frames):
        tl = np.round(step_size * frame).astype(np.int)
        br = tl + size_new
        image_cropped = background.crop(box=(tl[1], tl[0], br[1], br[0]))
        image_resized = image_cropped.resize((1024, 1024), Image.BICUBIC)
        if motion is 'backward':
            frame = number_frames - frame - 1
        image_resized.save(os.path.join(args.output, '{}_{}.png'.format(image_name, str(frame).zfill(4))))
