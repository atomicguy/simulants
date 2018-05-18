from __future__ import division
from __future__ import print_function

import bpy

import os
import json
import sys

from argparse import ArgumentParser

if __name__ == '__main__':
    argv = sys.argv
    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    parser = ArgumentParser()
    parser.add_argument('--info', '-i', type=str, help='info json describing character', required=True)
    parser.add_argument('--out', '-o', type=str, help='directory to store resultant scene', required=True)
    args, _ = parser.parse_known_args(argv)

    cwd = os.path.dirname(os.path.abspath(__file__))
    import_dir = cwd.replace('/bin/blender', '', 1)
    sys.path.append(import_dir)

    from simulants import render, simulant

    with open(args.info) as jd:
        info = json.load(jd)

    # Open file
    bpy.ops.wm.open_mainfile(filepath=info['scene_path'])

    objects = info['objects']
    simulants = [obj for obj in objects if obj['class'] == 'simulant']

    # Move Head boxes to correct layers
    for simulant in simulants:
        head_proxy = bpy.data.objects[simulant['head_proxy']['id']]
        layer_id = int(simulant['head_proxy']['layer'])
        head_proxy.layers = [i == layer_id for i in range(len(head_proxy.layers))]

    # Render head masks
    bpy.data.scenes['Scene'].use_nodes = True
    for simulant in simulants:
        layer_id = int(simulant['head_proxy']['layer'])
        render.set_head_passes(bpy.context)
        render.set_output_nodes(bpy.context, info['scene_id'], os.path.abspath(args.out), info)
        render.set_head_render_settings(50, 32)
        head_mask_path = os.path.join(os.path.abspath(args.out), simulant['id'], 'head_{}.png'.format(simulant['id']))
        bpy.context.scene.render.filepath = head_mask_path
        bpy.context.scene.layers = [i == layer_id for i in range(len(bpy.context.scene.layers))]
        bpy.ops.render.render(animation=False, write_still=True)

    # Render UV map
    bpy.data.scenes['Scene'].use_nodes = True
    bpy.context.scene.layers = [i == 0 for i in range(len(bpy.context.scene.layers))]
    render.set_uv_passes(bpy.context)
    render.set_output_nodes(bpy.context, info['scene_id'], os.path.abspath(args.out), info)
    render.set_uv_render_settings(50, 32)
    bpy.ops.render.render(animation=False)

    # Render
    bpy.data.scenes['Scene'].use_nodes = True
    bpy.context.scene.layers = [i == 0 for i in range(len(bpy.context.scene.layers))]
    render.set_passes(bpy.context)
    render.set_output_nodes(bpy.context, info['scene_id'], os.path.abspath(args.out), info)
    render.set_render_settings(50, 32)
    bpy.ops.render.render(animation=False)

    # Render each head box
    bpy.data.scenes['Scene'].use_nodes = True
    for obj in objects:
        if obj['class'] == 'simulant':
            bpy.context.scene.layers = [i == int(obj['head_proxy']['layer']) for i in range(len(bpy.context.scene.layers))]
            render.set_passes(bpy.context)
            head_mask_path = os.path.join(args.out, obj['id'])

        # TODO: calculate head distance and save

    # bpy.ops.wm.save_as_mainfile(filepath=os.path.join(args.out, info['scene_id'] + '.blend'))
