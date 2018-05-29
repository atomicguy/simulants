from __future__ import division
from __future__ import print_function

import bpy
import math
import os
import json
import random
import sys

from argparse import ArgumentParser


def create_metadata(info):
    metadata = {}
    metadata['scene_id'] = info['scene_id']
    metadata['background'] = info['background']
    targets = []

    for obj in info['objects']:
        cls = obj['class_name']
        if cls == 'simulant':
            cls = 'person'
        targets.append({'class_name': cls, 'id': obj['id']})

    metadata['objects'] = targets

    return metadata


def random_position(type='beta'):
    if type == 'beta':
        rho = (1 - random.betavariate(2, 5)) * 10
    else:
        rho = random.uniform(1.5, 10)
    phi = random.uniform(math.radians(-15), math.radians(15))
    x = rho * math.sin(phi)
    y = rho * math.cos(phi) - 2.5
    z = 0

    return (x, y, z)


if __name__ == '__main__':
    argv = sys.argv
    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    parser = ArgumentParser()
    parser.add_argument('--info', '-i', type=str, help='info json describing character', required=True)
    parser.add_argument('--out', '-o', type=str, help='directory to store resultant scene', required=True)
    parser.add_argument('--save', '-s', type=str, help='set true to save scene file', default='False')
    parser.add_argument('--base', '-b', type=str, help='base blend file', default='./data/base_scene.blend')
    args, _ = parser.parse_known_args(argv)

    cwd = os.path.dirname(os.path.abspath(__file__))
    import_dir = cwd.replace('/bin/blender', '', 1)
    sys.path.append(import_dir)

    from simulants import camera, render, simulant

    with open(args.info) as jd:
        info = json.load(jd)

    out_path = os.path.join(args.out, info['scene_id'])

    metadata = create_metadata(info)

    # Generate scene
    bpy.ops.wm.open_mainfile(filepath=args.base)
    render.hdri_lighting(info['background'], info['hdri_intensity'])
    camera.position()
    camera.rotate_env_tex(info['background_rotation'])

    # Import objects
    for obj in info['objects']:
        assert os.path.isfile(obj['path']), 'blend file {} does not exist'.format(obj['path'])
        with bpy.data.libraries.load(obj['path'], link=False) as (source, target):
            target.objects = [name for name in source.objects if name.endswith(obj['id'])]

        # Append to current scene
        for t_obj in target.objects:
            if t_obj is not None:
                bpy.context.scene.objects.link(t_obj)

        # assign simulant body render layers
        sim = bpy.data.objects['body_{}'.format(obj['id'])]
        materials = [mat.name for mat in sim.material_slots]
        for mat in materials:
            if mat.startswith('MBlab_human_skin'):
                render.set_render_layer(mat, obj['skin']['render_layer'])
            else:
                render.set_render_layer(mat, obj['misc']['render_layer'])

        parts = [obj['hair']['id'], obj['pants']['id'], obj['shirt']['id']]
        parts = [bpy.data.objects[part].material_slots[0].name for part in parts]
        layers = [obj['hair']['render_layer'], obj['pants']['render_layer'], obj['shirt']['render_layer']]

        for part, layer in zip(parts, layers):
            render.set_render_layer(part, layer)

        # reposition simulant
        bpy.data.objects[obj['skeleton']].location = random_position(info['distribution'])

    image_size = info['image_size']
    image_percent = int(info['percent_size'])
    tile_size = int(info['tile_size'])

    objects = info['objects']
    simulants = [obj for obj in objects if obj['class_name'] == 'simulant']

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
        render.set_output_nodes(bpy.context, info['scene_id'], os.path.abspath(out_path), info)
        render.set_head_render_settings(image_size, image_percent, tile_size)
        head_mask_path = os.path.join(os.path.abspath(out_path), character['head_id'],
                                      'head_{}.png'.format(character['head_id']))
        bpy.context.scene.render.filepath = head_mask_path
        bpy.context.scene.layers = [i == layer_id for i in range(len(bpy.context.scene.layers))]
        bpy.ops.render.render(animation=False, write_still=True)

        head_info = simulant.head_proxy_properties(character['head_proxy']['id'])
        head_info['class_name'] = 'head'
        head_info['id'] = character['head_id']
        head_info['center'] = [x for x in head_info['center']]
        metadata['objects'].append(head_info)

    # Render UV map
    bpy.data.scenes['Scene'].use_nodes = True
    bpy.context.scene.layers = [i == 0 for i in range(len(bpy.context.scene.layers))]
    render.set_uv_passes(bpy.context)
    render.set_output_nodes(bpy.context, info['scene_id'], os.path.abspath(out_path), info)
    render.set_uv_render_settings(image_size, image_percent, tile_size)
    bpy.ops.render.render(animation=False)

    # Render full image
    bpy.data.scenes['Scene'].use_nodes = True
    bpy.context.scene.layers = [i == 0 for i in range(len(bpy.context.scene.layers))]
    render.set_passes(bpy.context)
    render.set_output_nodes(bpy.context, info['scene_id'], os.path.abspath(out_path), info)
    render.set_render_settings(image_size, image_percent, tile_size)
    bpy.ops.render.render(animation=False)

    # Only save scene file if requested
    if args.save == 'True':
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_path, info['scene_id'] + '.blend'))

    # Save metadata info on depth, etc
    with open(os.path.join(out_path, '{}.json'.format(info['scene_id'])), 'w') as outfile:
        json.dump(metadata, outfile, indent=2)
