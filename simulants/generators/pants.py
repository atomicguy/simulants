from __future__ import absolute_import, division, print_function

import bpy

from simulants import node, render, retex
from simulants.blend_ops import append_item, get_blend_obj, parent_to_skeleton


class PantsGenerator:
    def __init__(self, config):
        self.config = config

    def attach_to(self, geo):
        pants = self.config['pants']
        append_item(pants['model'], 'pants', geo)
        render.set_render_layer('pants', pants['render_layer'])
        pants_mat = node.material('pants')
        texture_file = pants['texture']
        retexture_shirt = getattr(retex, pants['retexture_type'])
        retexture_shirt(pants_mat, texture_file)
        get_blend_obj('pants').name = pants['id']
        retex.customize_clothes(pants['id'], pants['style'])
        parent_to_skeleton(bpy.data.objects[pants['id']], bpy.data.objects[self.config['skeleton']])