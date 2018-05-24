from __future__ import absolute_import, division, print_function

import os
import json
import random
import uuid

from argparse import ArgumentParser
from dataset_toolbox.src.tools.common import find_filepaths, get_list
from simulants.description import SimulantDescriptionGenerator

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--out_dir', type=str, help='where scene json will go', required=True)
    parser.add_argument('--scene_dir', type=str, help='where scene blend files should end up', required=True)
    parser.add_argument('--sim_dir', type=str, help='where simulant blends files should go', required=True)
    parser.add_argument('--number', type=int, help='number of simulants in the scene', required=True)
    parser.add_argument('--backgrounds', type=str, help='directory of backround hdr images',
                        default='/usr/local/share/datasets/hdris')
    parser.add_argument('--textures', type=str, help='directory of texture pngs',
                        default='/usr/local/share/datasets/simulants/patterns')
    parser.add_argument('--pose_list', type=str, help='list of poses to use',
                        default='/usr/local/share/datasets/simulants/mocap_pose_list.txt')
    parser.add_argument('--hairs', type=str, help='base directory of hair models',
                        default='/usr/local/share/datasets/simulants/hairs')
    parser.add_argument('--clothes', type=str, help='base directory of clothing models',
                        default='/usr/local/share/datasets/simulants/clothes')
    args = parser.parse_args()

    backgrounds = find_filepaths(args.backgrounds, 'hdr')
    textures = find_filepaths(args.textures, 'png')
    poses = get_list(args.pose_list)

    # Random scene values
    scene_id = str(uuid.uuid4())
    background = random.choice(backgrounds)
    background_rotation = random.uniform(0, 360)

    scene_info = {'scene_id': scene_id,
                  'scene_path': os.path.join(args.scene_dir, '{}.blend'.format(scene_id)),
                  'background': background,
                  'background_rotation': background_rotation,
                  'hdri_intensity': 1,
                  'image_size': 1024,
                  'tile_size': 32}

    sim_info = {'out_path': args.sim_dir,
                'hair_path': args.hairs,
                'clothes_path': args.clothes,
                'textures': textures,
                'poses': poses}

    objects = []
    for i in range(args.number):
        simulant = SimulantDescriptionGenerator(i, scene_id, sim_info)
        info = simulant.desriptor()
        objects.append(info)

    scene_info['objects'] = objects

    with open(os.path.join(args.out_dir, '{}.json'.format(scene_id)), 'w') as outfile:
        json.dump(scene_info, outfile, indent=2)
