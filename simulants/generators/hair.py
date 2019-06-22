from __future__ import absolute_import, division, print_function

import bpy

from simulants import render, retex
from simulants.blend_ops import append_item, get_blend_obj, parent_to_skeleton


class HairGenerator:
    def __init__(self, config):
        self.config = config

    def attach_to(self, geo):
        hair = self.config['hair']
        append_item(hair['model'], 'hair', geo)
        render.set_render_layer('hair', hair['render_layer'])
        hair_color = (
            hair['rgb']['r'], hair['rgb']['g'], hair['rgb']['b'], 1)
        retex.recolor_hair(hair_color)
        get_blend_obj('hair').name = hair['id']
        parent_to_skeleton(bpy.data.objects[hair['id']], bpy.data.objects[self.config['skeleton']])
