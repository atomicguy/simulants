from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import json
import Imath
import OpenEXR
import numpy as np

from PIL import Image, ImageChops, ImageStat
from argparse import ArgumentParser


def depth_array(file_path):
    exr = OpenEXR.InputFile(file_path)
    pixel_type = Imath.PixelType(Imath.PixelType.FLOAT)
    dw = exr.header()['dataWindow']
    size = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)

    z = exr.channel('R', pixel_type)
    z = Image.frombytes('F', size, z)
    z = np.asarray(z)

    return z


def depth_values(depth_array, z_max=10000000000.0):
    """array of depth values less than maximum"""
    values = depth_array[np.where(depth_array < z_max)]

    return values


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('--info', '-i', type=str, help='scene metadata json', required=True)
    args, _ = parser.parse_known_args()

    with open(args.info) as jd:
        info = json.load(jd)

    base_path = os.path.split(args.info)[0]

    for obj in info['objects']:
        if obj['class'] == 'head':
            head_mask = Image.open(os.path.join(base_path, obj['id'], 'head_{}.png'.format(obj['id']))).convert('L')
            head_mask.save(os.path.join(base_path, obj['id'], 'mask_{}.png'.format(obj['id'])))
            if ImageStat.Stat(head_mask).extrema[0][0] == ImageStat.Stat(head_mask).extrema[0][1]:
                obj['distance'] = float('nan')
        if obj['class'] == 'person':
            mask_parts = ['hair', 'misc', 'pants', 'shirt', 'skin']
            hair = Image.open(os.path.join(base_path, obj['id'],
                                           'hair_{}0001.png').format(obj['id'])).convert('L')
            mask = Image.new('L', hair.size, color=0)
            for part in mask_parts:
                part = Image.open(os.path.join(base_path, obj['id'],
                                               '{}_{}0001.png'.format(part, obj['id']))).convert('L')
                mask = ImageChops.add(mask, part)

            mask.save(os.path.join(base_path, obj['id'], 'mask_{}.png'.format(obj['id'])))
            depth = depth_array(os.path.join(base_path, 'z', '{}_0001.exr'.format(info['scene_id'])))
            mask_np = np.asarray(mask)
            mask_np = mask_np / 255.0

            np.putmask(depth, mask_np < 1, 10000000001.0)
            distance = np.mean(depth_values(depth))
            obj['distance'] = float(distance)

    with open(os.path.join(base_path, 'metadata_{}.json'.format(info['scene_id'])), 'w') as outfile:
        json.dump(info, outfile, indent=2)