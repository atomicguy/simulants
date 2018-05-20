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

    # Generate objects if needed
    for obj_properties in info['objects']:
        if obj_properties['class'] == 'simulant':
            if not os.path.isfile(obj_properties['path']):
                # reset Blender setup
                bpy.ops.wm.read_homefile()
                this_simulant = simulant.SimulantGenerator(obj_properties)
                this_simulant.personalize()
                this_simulant.set_pose()
                this_simulant.clothe()
                this_simulant.set_position()

                bpy.ops.file.pack_all()
                bpy.ops.wm.save_as_mainfile(filepath=obj_properties['path'])

    # Combine into scene
    bpy.ops.wm.read_homefile()
    render.hdri_lighting(info['background'], info['hdri_intensity'])

    # Import objects
    for obj in info['objects']:
        with bpy.data.libraries.load(obj['path'], link=False) as (source, target):
            target.objects = [name for name in source.objects if name.endswith(obj['id'])]

        # Append to current scene
        for obj in target.objects:
            if obj is not None:
                bpy.context.scene.objects.link(obj)

    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(args.out, info['scene_id'] + '.blend'))
