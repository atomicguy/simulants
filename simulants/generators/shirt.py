from __future__ import absolute_import, division, print_function

import bpy

from simulants import node, render, retex
from simulants.blend_ops import append_item, get_blend_obj, parent_to_skeleton

class ShirtGenerator:
    def __init__(self, config):
        self.config = config

    def attach_to(self, geo):
        shirt = self.config['shirt']
        append_item(shirt['model'], 'tshirt', geo)
        render.set_render_layer('tshirt', shirt['render_layer'])
        shirt_mat = node.material('tshirt')
        texture_file = shirt['texture']
        retexture_shirt = getattr(retex, shirt['retexture_type'])
        retexture_shirt(shirt_mat, texture_file)
        get_blend_obj('tshirt').name = shirt['id']
        retex.customize_clothes(shirt['id'], shirt['style'])
        parent_to_skeleton(bpy.data.objects[shirt['id']], bpy.data.objects[self.config['skeleton']])