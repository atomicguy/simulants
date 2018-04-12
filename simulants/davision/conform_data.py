from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import numpy as np

from PIL import Image
from argparse import ArgumentParser

sys.path.append('../')
import fileio
import cli


def split_masks(rgb_mask_path, out_path):
    file_list = sorted(fileio.image_list(rgb_mask_path))
    print('reading: {}'.format(rgb_mask_path))
    print('writing to: {}'.format(out_path))

    for i, mask in enumerate(file_list):
        cli.progress_bar((i+1)/len(file_list))
        mask_path = os.path.join(rgb_mask_path, mask)
        mask_img = Image.open(mask_path)
        mask_np = np.asarray(mask_img)

        mask_r = mask_np[:, :, 0]
        mask_g = mask_np[:, :, 1]
        mask_b = mask_np[:, :, 2]

        mask_hair = Image.fromarray(mask_r, mode='L')
        mask_skin = Image.fromarray(mask_g, mode='L')
        mask_face = Image.fromarray(mask_b, mode='L')

        hair_dir = fileio.ensure_dir(os.path.join(out_path, 'hair'))
        skin_dir = fileio.ensure_dir(os.path.join(out_path, 'skin'))
        face_dir = fileio.ensure_dir(os.path.join(out_path, 'face'))

        mask_hair.save(os.path.join(hair_dir, '{}.png'.format(str(i).zfill(5))))
        mask_skin.save(os.path.join(skin_dir, '{}.png'.format(str(i).zfill(5))))
        mask_face.save(os.path.join(face_dir, '{}.png'.format(str(i).zfill(5))))


def conform_cloth(cloth_masks_path, out_path):
    file_list = sorted(fileio.image_list(cloth_masks_path))

    cloth_out_path = fileio.ensure_dir(os.path.join(out_path, 'cloth'))
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

