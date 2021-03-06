from __future__ import absolute_import, division, print_function

import math
import os
import random


class SimulantDescriptionGenerator:
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
        location = random_position()

        self.instance_id = str(instance_id).zfill(4)
        self.class_name = 'simulant'
        self.id = '{}_01_{}'.format(scene_id, self.instance_id)
        self.head_id = '{}_91_{}'.format(scene_id, self.instance_id)
        self.skeleton = 'skeleton_{}'.format(self.id)
        self.geometry = 'body_{}'.format(self.id)
        self.path = os.path.join(sim_info['out_path'], '{}.blend'.format(self.id))
        self.base_mesh = random.choice(base_meshes)
        self.sex = which_sex(self.base_mesh)
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
        self.location = {'x': location[0],
                         'y': location[1],
                         'z': location[2]}
        self.rotation = {'x': 0.0, 'y': 0.0, 'z': random.uniform(-180, 180)}

    def desriptor(self):
        return {'id': self.id,
                'class_name': self.class_name,
                'head_id': self.head_id,
                'skeleton': self.skeleton,
                'geometry': self.geometry,
                'path': self.path,
                'sex': self.sex,
                'head_proxy': self.head_proxy,
                'base_mesh': self.base_mesh,
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


def which_sex(base_mesh):
    """From base mesh name, return simulant's sex"""
    sex = ''
    if base_mesh[0] == 'f':
        sex = 'female'
    if base_mesh[0] == 'm':
        sex = 'male'
    assert len(sex) > 3, 'simulant must have assigned sex. It is: {}'.format(sex)

    return sex


def random_position(fov=30, min=2, max=10, camera=-2.5, type='beta'):
    """Generate an x,y,z position within a given frustum

    :param fov: camera field of view
    :param min: min distance from camera
    :param max: max distance from camera
    :param camera: camera position on y axis
    :return: (x, y, z) coordinates
    """
    if type == 'beta':
        rho = (1 - random.betavariate(min, max)) * 10
    else:
        rho = random.uniform(1.5, 10)
    phi = random.uniform(math.radians(-1*fov/2), math.radians(fov/2))
    x = rho * math.sin(phi)
    y = rho * math.cos(phi) + camera
    z = 0

    return (x, y, z)


def update_layers(simulant, instance_id):
    """Update the layers & render layers of a simulant

    :param simulant: the dictionary for a simulant
    :return: updated object dictionary
    """
    layer_base = instance_id * 10
    simulant['head_proxy']['layer'] = instance_id + 1
    simulant['skin']['render_layer'] = layer_base + 1
    simulant['misc']['render_layer'] = layer_base + 6
    simulant['hair']['render_layer'] = layer_base + 4
    simulant['shirt']['render_layer'] = layer_base + 2
    simulant['pants']['render_layer'] = layer_base + 3

    return simulant
