from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import numpy as np

from PIL import Image, ImageChops
from argparse import ArgumentParser


def image_list(path):
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


def test_masks(masks, frame_id):
    sum_mask = np.asarray(masks[0])
    sum_mask = np.zeros_like(sum_mask)
    for mask in masks:
        this_mask = np.asarray(mask)
        sum_mask = sum_mask + this_mask

    assert np.max(sum_mask) <= 255, 'max of {} on {}'.format(np.max(sum_mask), frame_id)


def save_frames(original_path, out_path):
    frames = sorted(image_list(os.path.join(original_path, 'cloth')))

    for i, frame in enumerate(frames):
        progress_bar((i+1)/len(frames))

        cloth = Image.open(os.path.join(original_path, 'cloth', frame)).convert('L')
        skin = Image.open(os.path.join(original_path, 'skin', frame)).convert('L')
        face = Image.open(os.path.join(original_path, 'face', frame)).convert('L')
        hair = Image.open(os.path.join(original_path, 'hair', frame)).convert('L')

        new_cloth = ImageChops.multiply(cloth, ImageChops.invert(skin))
        body = ImageChops.add(new_cloth, skin)

        new_face = ImageChops.multiply(face, ImageChops.invert(body))
        person = ImageChops.add(new_face, body)

        new_hair = ImageChops.multiply(hair, ImageChops.invert(person))

        skin_out = ensure_dir(os.path.join(out_path, 'skin'))
        cloth_out = ensure_dir(os.path.join(out_path, 'cloth'))
        face_out = ensure_dir(os.path.join(out_path, 'face'))
        hair_out = ensure_dir(os.path.join(out_path, 'hair'))

        masks = [skin, new_hair, new_cloth, new_face]
        test_masks(masks, frame)

        skin.save(os.path.join(skin_out, frame))
        new_cloth.save(os.path.join(cloth_out, frame))
        new_face.save(os.path.join(face_out, frame))
        new_hair.save(os.path.join(hair_out, frame))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--original_sequences', type=str, help='directory of original masks images to process')
    parser.add_argument('--out_path', type=str, help='output path')
    args, _ = parser.parse_known_args()

    sequences = os.listdir(args.original_sequences)

    for sequence in sequences:
        print(sequence)
        instances = os.listdir(os.path.join(args.original_sequences, sequence))

        for instance in instances:
            frames_path = os.path.join(args.original_sequences, sequence, instance)
            out_path = ensure_dir(os.path.join(args.out_path, sequence, instance))

            save_frames(frames_path, out_path)
