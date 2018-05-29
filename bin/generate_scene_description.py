from __future__ import absolute_import, division, print_function

import os
import json
import random
import uuid

from argparse import ArgumentParser
from dataset_toolbox.src.tools.common import find_filepaths, get_list, mkdirp
from simulants.description import update_layers

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--out_dir', type=str, help='where scene json will go', required=True)
    parser.add_argument('--scene_dir', type=str, help='if saved, where scene blend files should end up', required=True)
    parser.add_argument('--sims', type=str, help='directory of simulant json descriptors to use', required=True)
    parser.add_argument('--number', type=int, help='number of simulants in the scene', required=True)
    parser.add_argument('--distribution', type=str, help='distribution function for sim positioning',
                        default='uniform')
    parser.add_argument('--backgrounds', type=str, help='directory of backround hdr images',
                        default='/usr/local/share/datasets/hdris')

    args = parser.parse_args()

    backgrounds = find_filepaths(args.backgrounds, 'hdr')

    # Random scene values
    scene_id = str(uuid.uuid4())
    background = random.choice(backgrounds)
    background_rotation = random.uniform(0, 360)

    scene_info = {'scene_id': scene_id,
                  'scene_path': os.path.join(args.scene_dir, '{}.blend'.format(scene_id)),
                  'background': background,
                  'background_rotation': background_rotation,
                  'hdri_intensity': 1,
                  'image_size': [720, 1280],
                  'percent_size': 100,
                  'tile_size': 32,
                  'distribution': args.distribution}

    simulants = find_filepaths(args.sims, 'json')

    sim_sample = random.sample(simulants, args.number)

    objects = []
    for i, sim in enumerate(sim_sample):
        try:
            with open(sim) as jd:
                simulant = json.load(jd)
        except ValueError:
            print('{} is broken'.format(sim))
            simulants.remove(sim)
            with open(random.choice(simulants)) as jd:
                simulant = json.load(jd)
        info = update_layers(simulant, i)
        objects.append(info)

    scene_info['objects'] = objects

    mkdirp(args.out_dir)
    with open(os.path.join(args.out_dir, '{}.json'.format(scene_id)), 'w') as outfile:
        json.dump(scene_info, outfile, indent=2)
