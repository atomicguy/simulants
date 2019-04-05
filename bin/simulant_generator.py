import os
import json
import random
import subprocess
import uuid

from argparse import ArgumentParser
from codenamize import codenamize
from dataset_toolbox.src.tools.common import find_filepaths, get_list, mkdirp
from simulants.description import SimulantDescriptionGenerator, update_layers


def make_a_simulant(sim_info, out_dir):
    sim_id = codenamize(str(uuid.uuid4()), 2, 0)
    simulant = SimulantDescriptionGenerator(0, sim_id, sim_info)
    info = simulant.desriptor()

    with open(os.path.join(out_dir, '{}.json'.format(sim_id)), 'w') as outfile:
            json.dump(info, outfile, indent=2)

    return sim_id


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--out_dir', type=str, help='where simulant jsons will go',
                        default='tmp/jsons')
    parser.add_argument('--sim_dir', type=str, help='where simulant blends files should go',
                        default='tmp/simulants')
    parser.add_argument('--textures', type=str, help='directory of texture pngs',
                        default='data/patterns')
    parser.add_argument('--pose_list', type=str, help='list of poses to use',
                        default='data/mocap_pose_list.txt')
    parser.add_argument('--hairs', type=str, help='base directory of hair models',
                        default='data/hairs')
    parser.add_argument('--clothes', type=str, help='base directory of clothing models',
                        default='data/clothes')
    parser.add_argument('--scene_json', type=str, help='where the scene json will go', required=True)
    parser.add_argument('--scene_dir', type=str, help='if saved, where scene blend files should end up', required=True)
    parser.add_argument('--backgrounds', type=str, help='directory of backround hdr images',
                        default='data/backgrounds')
    parser.add_argument('--distribution', type=str, help='distribution function for sim positioning',
                        default='uniform')
    parser.add_argument('--layer_dir', type=str, help='directory for rendered layers', required=True)
    args = parser.parse_args()

    mkdirp(args.out_dir)
    mkdirp(args.sim_dir)

    # Generate Simulant Descriptor
    textures = find_filepaths(args.textures, 'png')
    poses = get_list(args.pose_list)

    sim_info = {'out_path': args.sim_dir,
                'hair_path': args.hairs,
                'clothes_path': args.clothes,
                'textures': textures,
                'poses': poses}

    sim_id = make_a_simulant(sim_info, args.out_dir)

    # Generate Scene Descriptor
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

    with open(os.path.join(args.out_dir, '{}.json'.format(sim_id))) as jd:
        simulant = json.load(jd)
    objects = [update_layers(simulant, 0)]
    scene_info['objects'] = objects

    mkdirp(args.scene_dir)
    scene_json = os.path.join(args.out_dir, '{}.json'.format(scene_id))
    with open(scene_json, 'w') as outfile:
        json.dump(scene_info, outfile, indent=2)

    # Make a Scene
    scene_cmd = ['blender', '-b', '-P',
                 'bin/blender/make_a_scene.py', '--',
                 '--info', scene_json,
                 '--base_scene', 'data/base_scene.blend']
    
    subprocess.check_call(scene_cmd)

    # Render Scene
    command = ['blender', '-b', '-P',
               'bin/blender/build_and_render_scene.py', '--',
               '--info', scene_json,
               '--out', args.layer_dir,
               '--base', 'data/base_scene.blend']

    subprocess.check_call(command)
