from __future__ import division, print_function

import os
import bpy
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
    args, _ = parser.parse_known_args(argv)

    cwd = os.path.dirname(os.path.abspath(__file__))
    import_dir = cwd.replace('/bin/blender', '', 1)
    sys.path.append(import_dir)

    from simulants import simulant
    from dataset_toolbox.src.tools import common

    with open(args.info) as jd:
        info = json.load(jd)

    for obj_properties in info['objects']:
        if obj_properties['class_name'] == 'simulant':
            # ensure Blender is blank slate
            bpy.ops.wm.read_homefile()
            this_simulant = simulant.SimulantGenerator(obj_properties)
            this_simulant.personalize()
            this_simulant.set_pose()
            this_simulant.clothe()
            this_simulant.set_position()

            bpy.ops.file.pack_all()
            common.mkdirp(os.path.split(obj_properties['path'])[0])
            bpy.ops.wm.save_as_mainfile(filepath=obj_properties['path'])
