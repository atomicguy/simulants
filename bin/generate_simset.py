from __future__ import absolute_import, division, print_function

import os
import json
import uuid

from argparse import ArgumentParser
from codenamize import codenamize
from dataset_toolbox.src.tools.common import find_filepaths, get_list
from simulants.description import SimulantDescriptionGenerator

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--out_dir', type=str, help='where scene json will go', required=True)
    parser.add_argument('--sim_dir', type=str, help='where simulant blends files should go', required=True)
    parser.add_argument('--number', type=int, help='number of simulants in the scene', required=True)
    parser.add_argument('--textures', type=str, help='directory of texture pngs',
                        default='/usr/local/share/datasets/simulants/patterns')
    parser.add_argument('--pose_list', type=str, help='list of poses to use',
                        default='/usr/local/share/datasets/simulants/mocap_pose_list.txt')
    parser.add_argument('--hairs', type=str, help='base directory of hair models',
                        default='/usr/local/share/datasets/simulants/hairs')
    parser.add_argument('--clothes', type=str, help='base directory of clothing models',
                        default='/usr/local/share/datasets/simulants/clothes')
    args = parser.parse_args()

    textures = find_filepaths(args.textures, 'png')
    poses = get_list(args.pose_list)

    sim_info = {'out_path': args.sim_dir,
                'hair_path': args.hairs,
                'clothes_path': args.clothes,
                'textures': textures,
                'poses': poses}

    objects = []
    for i in range(args.number):
        sim_id = codenamize(str(uuid.uuid4()), 2, 0)
        simulant = SimulantDescriptionGenerator(i, sim_id, sim_info)
        info = simulant.desriptor()
        objects.append(info)

    scene_info = {'objects': objects}

    with open(os.path.join(args.out_dir, 'simulant_set.json'), 'w') as outfile:
        json.dump(scene_info, outfile, indent=2)
