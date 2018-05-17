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
    parser.add_argument('--out', '-o', type=str, help='directory to save result', required=True)
    args, _ = parser.parse_known_args(argv)

    cwd = os.path.dirname(os.path.abspath(__file__))
    import_dir = cwd.replace('/bin/blender', '', 1)
    sys.path.append(import_dir)

    from simulants import render, simulant

    with open(args.info) as jd:
        info = json.load(jd)

    sim_values = info['objects'][0]
    skin_values = sim_values['skin_values']
    eye_values = sim_values['eye_values']
    trait_values = sim_values['traits']

    # Add Simulant to project
    simulant.initialize_base(sim_values['base_mesh'])

    # Set skin, eye, body traits, etc and finalize
    simulant.set_skin(sim_values['base_mesh'], skin_values['hue'], skin_values['saturation'], skin_values['value'],
                      skin_values['age'], skin_values['bump'])
    simulant.set_eyes(sim_values['base_mesh'], eye_values['hue'], eye_values['saturation'], eye_values['value'])
    simulant.set_traits(sim_values['base_mesh'], trait_values['age'], trait_values['mass'], trait_values['tone'])

    simulant.make_unique(sim_values['randomize'])
    simulant.finalize()

    # Clothe, Pose, Set render layers
    simulant.uncensor()
    render.set_render_layer('MBlab_human_skin', skin_values['render_layer'])
    render.set_render_layer('MBlab_human_eyes', eye_values['render_layer'])
    render.set_render_layer('MBlab_pupil', eye_values['render_layer'])
    render.set_render_layer('MBlab_cornea', eye_values['render_layer'])
    # lump in teeth, fur with eyes to become 'etc'
    render.set_render_layer('MBlab_human_teeth', eye_values['render_layer'])
    render.set_render_layer('MBlab_fur', eye_values['render_layer'])

    simulant.pose(sim_values['pose'])

    simulant.append_item(sim_values['hair']['model'], 'hair')
    render.set_render_layer('hair', sim_values['hair']['render_layer'])
    simulant.append_item(sim_values['shirt']['model'], 'tshirt')
    render.set_render_layer('tshirt', sim_values['shirt']['render_layer'])
    simulant.append_item(sim_values['pants']['model'], 'pants')
    render.set_render_layer('pants', sim_values['pants']['render_layer'])

    simulant.rotate(sim_values['rotation']['z'])
    simulant.position(sim_values['location'])

    # TODO: get head proxy to rotate/translate with simulant
    # head_info = simulant.get_head_properties()
    head_info = simulant.head_properties()
    simulant.head_proxy(head_info, sim_values['head_proxy'])

    bpy.ops.file.pack_all()
    blend_result_path = os.path.join(args.out, info['scene_id'] + '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=blend_result_path)