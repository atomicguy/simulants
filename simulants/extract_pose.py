from __future__ import division
from __future__ import print_function

import os
import bpy
import sys
import random
import datetime

from argparse import ArgumentParser

character_list = ['f_ca01', 'f_as01', 'f_af01', 'm_ca01', 'm_as01', 'm_af01']


class OutputRedirect:
    def __init__(self, output, redirected_path):
        self.output = output
        self.redirected_path = redirected_path

    def __enter__(self):
        self.output_fd_backup = os.dup(self.output.fileno())
        self.output.flush()
        os.close(self.output.fileno())
        os.open(self.redirected_path, os.O_WRONLY)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.close(self.output.fileno())
        os.dup(self.output_fd_backup)
        os.close(self.output_fd_backup)


def generate_base_type():
    """Set up random base character and out path"""
    base_type = random.choice(character_list)
    print('generating character {}'.format(base_type))

    return base_type


def generate_id(base_type):
    date_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    character_id = '{}_{}'.format(date_stamp, base_type)

    return character_id


def initialize_base(base_type):
    """Initialize base character"""
    bpy.data.scenes['Scene'].mblab_character_name = base_type
    bpy.context.scene.mblab_use_lamps = False
    bpy.ops.mbast.init_character()


def deselect_all():
    for obj in bpy.context.scene.objects:
        obj.select = False


def get_human_mesh():
    objs = bpy.data.objects
    human_mesh = [obj for obj in objs if obj.name.startswith('MBlab_bd')][0]

    return human_mesh


def get_blend_obj(object_name):
    """Return a specified blender object

    :param object_name: name (or start of name) of object to be returned
    :return: the specified blender object
    """
    objs = bpy.data.objects
    obj_list = [obj for obj in objs if obj.name.startswith(object_name)]
    assert len(obj_list) > 0, 'object {} not found'.format(object_name)

    return obj_list[0]


def load_animation(animation_path):
    for obj in bpy.data.objects:
        obj.select = False
    human = get_blend_obj('MBlab_sk')
    human.select = True
    bpy.ops.mbast.pose_reset()
    bpy.ops.mbast.load_animation(filepath=animation_path)


def save_pose_sequence(mocap_path, out_path):
    mocap_name = os.path.splitext(os.path.basename(mocap_path))[0]

    out_dir = os.path.join(out_path, mocap_name)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    for f in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
        bpy.context.scene.frame_set(f)
        pose_name = os.path.join(out_dir, '{}_{}.json'.format(mocap_name, str(f).zfill(4)))
        bpy.ops.mbast.pose_save(filepath=pose_name)


def export_poses(out_dir, base_file, mocap_path):
    bpy.ops.wm.open_mainfile(filepath=base_file)
    base_type = generate_base_type()
    initialize_base(base_type)
    bpy.ops.mbast.finalize_character()

    load_animation(mocap_path)

    save_pose_sequence(mocap_path, out_dir)

    # Reset blender scene
    bpy.ops.wm.read_homefile()


if __name__ == '__main__':
    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    parser = ArgumentParser()
    parser.add_argument('--base_file', '-f', type=str, help='base blender file containing setup',
                        default='data/base_scene.blend')
    parser.add_argument('--out_dir', '-o', type=str, help='output directory for simulants', required=True)
    parser.add_argument('--mocap_path', '-m', type=str, help='mocap file path')

    args, _ = parser.parse_known_args(argv)

    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)

    export_poses(args.out_dir, args.base_file, args.mocap_path)
