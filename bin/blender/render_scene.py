from __future__ import division
from __future__ import print_function

import bpy

import os
import json
import sys

from argparse import ArgumentParser


def create_metadata(info):
    metadata = {}
    metadata['scene_id'] = info['scene_id']
    metadata['background'] = info['background']
    targets = []

    for obj in info['objects']:
        cls = obj['class']
        if cls == 'simulant':
            cls = 'person'
        targets.append({'class': cls, 'id': obj['id']})

    metadata['objects'] = targets

    return metadata

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

    metadata = create_metadata(info)

    # Load scene
    bpy.ops.wm.open_mainfile(filepath=info['scene_path'])

    image_percent = int(info['image_size'] / 2048 * 100)
    tile_size = int(info['tile_size'])

    objects = info['objects']
    simulants = [obj for obj in objects if obj['class'] == 'simulant']

    # Move Head boxes to correct layers
    for character in simulants:
        head_proxy = bpy.data.objects[character['head_proxy']['id']]
        layer_id = int(character['head_proxy']['layer'])
        head_proxy.layers = [i == layer_id for i in range(len(head_proxy.layers))]

    # Render head masks
    bpy.data.scenes['Scene'].use_nodes = True
    for character in simulants:
        layer_id = int(character['head_proxy']['layer'])
        render.set_head_passes(bpy.context)
        render.set_output_nodes(bpy.context, info['scene_id'], os.path.abspath(args.out), info)
        render.set_head_render_settings(image_percent, tile_size)
        head_mask_path = os.path.join(os.path.abspath(args.out), character['head_id'], 'mask_{}.png'.format(character['id']))
        bpy.context.scene.render.filepath = head_mask_path
        bpy.context.scene.layers = [i == layer_id for i in range(len(bpy.context.scene.layers))]
        bpy.ops.render.render(animation=False, write_still=True)

        head_info = simulant.head_properties('skeleton_{}'.format(character['id']))
        head_info['class'] = 'head'
        head_info['id'] = character['head_id']
        head_info['center'] = [x for x in head_info['center']]
        metadata['objects'].append(head_info)

    # Render UV map
    bpy.data.scenes['Scene'].use_nodes = True
    bpy.context.scene.layers = [i == 0 for i in range(len(bpy.context.scene.layers))]
    render.set_uv_passes(bpy.context)
    render.set_output_nodes(bpy.context, info['scene_id'], os.path.abspath(args.out), info)
    render.set_uv_render_settings(image_percent, tile_size)
    bpy.ops.render.render(animation=False)

    # Render full image
    bpy.data.scenes['Scene'].use_nodes = True
    bpy.context.scene.layers = [i == 0 for i in range(len(bpy.context.scene.layers))]
    render.set_passes(bpy.context)
    render.set_output_nodes(bpy.context, info['scene_id'], os.path.abspath(args.out), info)
    render.set_render_settings(image_percent, tile_size)
    bpy.ops.render.render(animation=False)

    # bpy.ops.wm.save_as_mainfile(filepath=os.path.join(args.out, info['scene_id'] + '.blend'))
    with open(os.path.join(args.out, '{}.json'.format(info['scene_id'])), 'w') as outfile:
        json.dump(metadata, outfile, indent=2)
