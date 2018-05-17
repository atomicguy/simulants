from __future__ import division, print_function

import os
import bpy
import json
import sys

from argparse import ArgumentParser


class HairGenerator:
    def __init__(self, config):
        self.config = config

    def attach_to(self, geo):
        simulant.append_item(self.config['model'], 'hair', geo)
        render.set_render_layer('hair', self.config['render_layer'])
        hair_color = (
            self.config['rgb']['r'], self.config['rgb']['g'], self.config['rgb']['b'], 1)
        retex.recolor_hair(hair_color)
        simulant.get_blend_obj('hair').name = self.config['id']


class ShirtGenerator:
    def __init__(self, config):
        self.config = config

    def attach_to(self, geo):
        simulant.append_item(self.config['model'], 'tshirt', geo)
        render.set_render_layer('tshirt', self.config['render_layer'])
        shirt_mat = node.material('tshirt')
        texture_file = self.config['texture']
        retexture_shirt = getattr(retex, self.config['retexture_type'])
        retexture_shirt(shirt_mat, texture_file)
        simulant.get_blend_obj('tshirt').name = self.config['id']


class PantsGenerator:
    def __init__(self, config):
        self.config = config

    def attach_to(self, geo):
        simulant.append_item(self.config['model'], 'pants', geo)
        render.set_render_layer('pants', self.config['render_layer'])
        pants_mat = node.material('pants')
        texture_file = self.config['texture']
        retexture_shirt = getattr(retex, self.config['retexture_type'])
        retexture_shirt(pants_mat, texture_file)
        simulant.get_blend_obj('pants').name = self.config['id']


def build_generator(x, sim_values):
    if x == 'hair':
        return HairGenerator(sim_values['hair'])
    if x == 'shirt':
        return ShirtGenerator(sim_values['shirt'])
    if x == 'pants':
        return PantsGenerator(sim_values['pants'])


class SimulantGenerator:
    def __init__(self, config):
        self.config = config
        simulant.initialize_base(self.config['base_mesh'])

    def personalize(self):
        simulant.set_skin(self.config['base_mesh'], self.config['skin']['hue'], self.config['skin']['saturation'],
                          self.config['skin']['value'], self.config['skin']['age'], self.config['skin']['bump'])
        simulant.set_eyes(self.config['base_mesh'], self.config['eye']['hue'], self.config['eye']['saturation'],
                          self.config['eye']['value'])
        simulant.set_traits(self.config['base_mesh'], self.config['traits']['age'], self.config['traits']['mass'],
                            self.config['traits']['tone'])
        simulant.make_unique(self.config['randomize'])
        simulant.finalize()

        # Rename
        simulant.get_blend_obj('MBlab_sk').name = self.config['skeleton']
        simulant.get_blend_obj('MBlab_bd').name = self.config['geometry']

        # Uncensor
        simulant.uncensor(self.config['geometry'])

        # Set render layers
        materials = [mat.name for mat in bpy.data.materials]
        for mat in materials:
            if mat.startswith('MBlab_human_skin'):
                render.set_render_layer(mat, self.config['skin']['render_layer'])
            else:
                render.set_render_layer(mat, self.config['misc']['render_layer'])

        # Generate head proxy and parent to head bone
        head_info = simulant.head_properties(self.config['skeleton'])
        simulant.head_proxy(self.config['skeleton'], head_info, self.config['head_proxy'])

    def set_position(self):
        simulant.rotate(self.config['skeleton'], self.config['rotation']['z'])
        simulant.position(self.config['skeleton'], self.config['location'])

    def set_pose(self):
        simulant.pose(self.config['geometry'], self.config['pose'])

    def clothe(self):
        for x in ['hair', 'shirt', 'pants']:
            cfg = build_generator(x, self.config)
            cfg.attach_to(self.config['geometry'])


if __name__ == '__main__':
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    parser = ArgumentParser()
    parser.add_argument('--info', '-i', type=str, help='info json describing character', required=True)
    args, _ = parser.parse_known_args(argv)

    cwd = os.path.dirname(os.path.abspath(__file__))
    import_dir = cwd.replace('/bin/blender', '', 1)
    sys.path.append(import_dir)

    from simulants import node, render, retex, simulant

    with open(args.info) as jd:
        info = json.load(jd)

    for obj_properties in info['objects']:
        if obj_properties['class'] == 'simulant':
            # ensure Blender is blank slate
            bpy.ops.wm.read_homefile()
            this_simulant = SimulantGenerator(obj_properties)
            this_simulant.personalize()
            this_simulant.set_pose()
            this_simulant.clothe()
            this_simulant.set_position()

            bpy.ops.file.pack_all()
            bpy.ops.wm.save_as_mainfile(filepath=obj_properties['path'])
