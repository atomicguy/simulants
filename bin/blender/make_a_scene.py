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
    parser.add_argument('--base_scene', type=str, help='blender base file',
                        default='/usr/local/share/datasets/simulants/base_scene.blend')
    args, _ = parser.parse_known_args(argv)

    cwd = os.path.dirname(os.path.abspath(__file__))
    import_dir = cwd.replace('/bin/blender', '', 1)
    sys.path.append(import_dir)

    from simulants import camera, render, simulant
    from dataset_toolbox.src.tools import common

    with open(args.info) as jd:
        info = json.load(jd)

    # Generate objects if needed
    for obj_properties in info['objects']:
        if obj_properties['class_name'] == 'simulant':
            if not os.path.isfile(obj_properties['path']):
                # reset Blender setup
                bpy.ops.wm.open_mainfile(filepath=args.base_scene)

                # Load simulant and set properties
                this_simulant = simulant.SimulantGenerator(obj_properties)
                this_simulant.personalize()
                this_simulant.clothe()
                this_simulant.set_pose()
                this_simulant.set_position()
                this_simulant.proxy_fit()
    
                # Pack and save blendfile
                bpy.ops.file.pack_all()
                common.mkdirp(os.path.split(obj_properties['path'])[0])
                bpy.ops.wm.save_as_mainfile(filepath=obj_properties['path'])

    # Combine into scene
    bpy.ops.wm.open_mainfile(filepath=args.base_scene)
    render.hdri_lighting(info['background'], info['hdri_intensity'])
    camera.position()
    camera.rotate_env_tex(info['background_rotation'])

    # Import any additional objects
    for obj in info['objects']:
        with bpy.data.libraries.load(obj['path'], link=False) as (source, target):
            target.objects = [name for name in source.objects if name.endswith(obj['id'])]

        # Append to current scene
        for obj in target.objects:
            if obj is not None:
                bpy.context.scene.objects.link(obj)

    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=info['scene_path'])
