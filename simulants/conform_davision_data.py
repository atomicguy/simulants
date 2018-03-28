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


def split_masks(rgb_mask_path, out_path):
    file_list = sorted(image_list(rgb_mask_path))
    print('reading: {}'.format(rgb_mask_path))
    print('writing to: {}'.format(out_path))

    for i, mask in enumerate(file_list):
        progress_bar((i+1)/len(file_list))
        mask_path = os.path.join(rgb_mask_path, mask)
        mask_img = Image.open(mask_path)
        mask_np = np.asarray(mask_img)

        mask_r = mask_np[:, :, 0]
        mask_g = mask_np[:, :, 1]
        mask_b = mask_np[:, :, 2]

        mask_hair = Image.fromarray(mask_r, mode='L')
        mask_skin = Image.fromarray(mask_g, mode='L')
        mask_face = Image.fromarray(mask_b, mode='L')

        hair_dir = ensure_dir(os.path.join(out_path, 'hair'))
        skin_dir = ensure_dir(os.path.join(out_path, 'skin'))
        face_dir = ensure_dir(os.path.join(out_path, 'face'))

        mask_hair.save(os.path.join(hair_dir, '{}.png'.format(str(i).zfill(5))))
        mask_skin.save(os.path.join(skin_dir, '{}.png'.format(str(i).zfill(5))))
        mask_face.save(os.path.join(face_dir, '{}.png'.format(str(i).zfill(5))))


def conform_cloth(cloth_masks_path, out_path):
    file_list = sorted(image_list(cloth_masks_path))

    cloth_out_path = ensure_dir(os.path.join(out_path, 'cloth'))
    print('writing cloth: {}'.format(cloth_out_path))

    for i, cloth in enumerate(file_list):
        cloth_path = os.path.join(cloth_masks_path, cloth)
        cloth_img = Image.open(cloth_path).convert('L')
        cloth_img.save(os.path.join(cloth_out_path, '{}.png'.format(str(i).zfill(5))))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--sequences_path', '-m', type=str, help='directory of mask images to process')
    parser.add_argument('--out_path', '-o', type=str, help='output path')
    args, _ = parser.parse_known_args()

    sequences = sorted(os.listdir(args.sequences_path))
    for sequence in sequences:
        instances = os.listdir(os.path.join(args.sequences_path, sequence))
        for instance in instances:
            rgb_masks_source = os.path.join(args.sequences_path, sequence, instance, 'rgb')
            out_masks_target = os.path.join(args.out_path, sequence, instance)
            split_masks(rgb_masks_source, out_masks_target)
            cloth_path_source = os.path.join(args.sequences_path, sequence, instance, 'cloth')
            conform_cloth(cloth_path_source, out_masks_target)

