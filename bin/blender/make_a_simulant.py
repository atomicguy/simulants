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
        sim = json.load(jd)

    # ensure Blender is blank slate
    bpy.ops.wm.open_mainfile(filepath='/tmp/blend_scripts/base_scene.blend')
    this_simulant = simulant.SimulantGenerator(sim)
    this_simulant.personalize()
    this_simulant.set_pose()
    this_simulant.clothe()
    this_simulant.set_position()

    bpy.ops.file.pack_all()
    common.mkdirp(os.path.split(sim['path'])[0])
    bpy.ops.wm.save_as_mainfile(filepath=sim['path'])
