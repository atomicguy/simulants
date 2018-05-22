from __future__ import absolute_import, division, print_function

import os
import json
import random
import uuid

from argparse import ArgumentParser
from dataset_toolbox.src.tools import common


def get_list(path):
    with open(path) as f:
        list = f.readlines()
    list = [x.strip() for x in list]

    return list


def which_sex(base_mesh):
    sex = ''
    if base_mesh[0] == 'f':
        sex = 'female'
    if base_mesh[0] == 'm':
        sex = 'male'
    assert len(sex) > 3, 'simulant must have assigned sex. It is: {}'.format(sex)

    return sex


class Simulant:
    def __init__(self, instance_id, scene_id, sim_info):
        """Generate the characteristics of a simulant

        :param instance_id: int enumerating the object in the scene
        :param scene_id: unique scene id
        :param sim_info: dict containing out_path, hair_path, clothing_path, textures, and poses
        """
        layer_base = instance_id * 10
        base_meshes = ['f_ca01', 'f_as01', 'f_af01', 'm_ca01', 'm_as01', 'm_af01']
        hairs = ['01', '02', '03', '04', '06', '07']
        retexture_types = ['noise_wrinkle', 'wave_wrinkle', 'magic_wrinkle', 'new_texture']
        pants_masks = ['', 'shorts_1', 'shorts_2', 'shorts_3']
        shirt_masks = ['shirt_neck', 'shirt_sleeveless', 'shirt_croptop', 'shirt_open_front',
                       'shirt_short_1', 'shirt_short_2']

        self.instance_id = str(instance_id).zfill(2)
        self.cls = 'simulant'
        self.id = '{}_01_{}'.format(scene_id, self.instance_id)
        self.head_id = '{}_91_{}'.format(scene_id, self.instance_id)
        self.skeleton = 'skeleton_{}'.format(self.id)
        self.geometry = 'body_{}'.format(self.id)
        self.path = os.path.join(sim_info['out_path'], '{}.blend'.format(self.id))
        self.base = random.choice(base_meshes)
        self.sex = which_sex(self.base)
        self.head_proxy = {'id': 'head_proxy_{}'.format(self.id),
                           'layer': instance_id + 1}
        self.randomize = {'mblab_preserve_fantasy': 'True',
                          'mblab_preserve_mass': 'True',
                          'mblab_preserve_tone': 'True',
                          'mblab_preserve_height': 'False',
                          'mblab_preserve_body': 'False',
                          'mblab_preserve_face': 'False',
                          'mblab_preserve_phenotype': 'False'}
        self.skin = {'hue': random.gauss(0.5, 0.2),
                     'saturation': random.uniform(0.6, 1),
                     'value': random.uniform(0.1, 1),
                     'age': random.uniform(0, 1),
                     'bump': random.uniform(0, 1),
                     'render_layer': layer_base + 1}
        self.misc = {'render_layer': layer_base + 6}
        self.eye = {'hue': random.uniform(0, 1),
                    'saturation': random.uniform(0, 1),
                    'value': random.uniform(0, 1)}
        self.traits = {'age': random.uniform(0, 1),
                       'mass': random.uniform(0, 1),
                       'tone': random.uniform(0, 1)}
        self.hair = {'model': os.path.join(sim_info['hair_path'],
                                           '{}_hair_{}.blend'.format(self.sex, random.choice(hairs))),
                     'id': 'hair_{}'.format(self.id),
                     'rgb': {'r': random.uniform(0, 1), 'g': random.uniform(0, 1), 'b': random.uniform(0, 1)},
                     'render_layer': layer_base + 4}
        self.shirt = {'id': 'tshirt_{}'.format(self.id),
                      'model': os.path.join(sim_info['clothes_path'], 'human_{}_clothes.blend'.format(self.sex)),
                      'retexture_type': random.choice(retexture_types),
                      'texture': random.choice(sim_info['textures']),
                      'style': random.choice(shirt_masks),
                      'render_layer': layer_base + 2}
        self.pants = {'id': 'pants_{}'.format(self.id),
                      'model': os.path.join(sim_info['clothes_path'], 'human_{}_clothes.blend'.format(self.sex)),
                      'retexture_type': random.choice(retexture_types),
                      'texture': random.choice(sim_info['textures']),
                      'style': random.choice(pants_masks),
                      'render_layer': layer_base + 3}
        self.pose = random.choice(sim_info['poses'])
        self.location = {'x': random.uniform(-2, 2),
                         'y': random.uniform(-8, 1.5),
                         'z': 0.0}
        self.rotation = {'x': 0.0, 'y': 0.0, 'z': random.uniform(-180, 180)}

    def desriptor(self):
        return {'id': self.id,
                'class': self.cls,
                'head_id': self.head_id,
                'skeleton': self.skeleton,
                'geometry': self.geometry,
                'path': self.path,
                'sex': self.sex,
                'head_proxy': self.head_proxy,
                'base_mesh': self.base,
                'skin': self.skin,
                'misc': self.misc,
                'eye': self.eye,
                'traits': self.traits,
                'randomize': self.randomize,
                'hair': self.hair,
                'shirt': self.shirt,
                'pants': self.pants,
                'pose': self.pose,
                'location': self.location,
                'rotation': self.rotation}


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--out_dir', type=str, help='where scene json will go', required=True)
    parser.add_argument('--scene_dir', type=str, help='where scene blend files should end up', required=True)
    parser.add_argument('--sim_dir', type=str, help='where simulant blends files should go', required=True)
    parser.add_argument('--backgrounds', type=str, help='directory of backround hdr images', required=True)
    parser.add_argument('--textures', type=str, help='directory of texture pngs', required=True)
    parser.add_argument('--pose_list', type=str, help='list of poses to use', required=True)
    parser.add_argument('--number', type=int, help='number of simulants in the scene', required=True)
    parser.add_argument('--hairs', type=str, help='base directory of hair models',
                        default='/usr/local/share/datasets/simulants/hairs')
    parser.add_argument('--clothes', type=str, help='base directory of clothing models',
                        default='/usr/local/share/datasets/simulants/clothes')
    args = parser.parse_args()

    backgrounds = common.find_filepaths(args.backgrounds, 'hdr')
    textures = common.find_filepaths(args.textures, 'png')
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
        simulant = Simulant(i, scene_id, sim_info)
        info = simulant.desriptor()
        objects.append(info)

    scene_info['objects'] = objects

    with open(os.path.join(args.out_dir, '{}.json'.format(scene_id)), 'w') as outfile:
        json.dump(scene_info, outfile, indent=2)
