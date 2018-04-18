from __future__ import division
from __future__ import print_function

import os
import bpy
import sys
import random
import datetime

from argparse import ArgumentParser

character_list = ['f_ca01', 'f_as01', 'f_af01', 'm_ca01', 'm_as01', 'm_af01']

pose_list = ['captured01.json', 'evil_beast.json', 'evil_explains.json',
             'evil_waiting_orders01.json', 'evil_waiting_orders02.json',
             'flying01.json', 'flying02.json', 'glamour01.json',
             'glamour02.json', 'glamour03.json', 'glamour04.json',
             'glamour05.json', 'glamour06.json', 'glamour07.json',
             'glamour08.json', 'gym01.json', 'gym02.json', 'pinup01.json',
             'shojo_classic01.json', 'shojo_classic02.json',
             'shojo_classic03.json', 'shojo_classic04.json', 'sit_basic.json',
             'sit_meditation.json', 'sit_sexy.json', 'sorceress.json',
             'standing_basic.json', 'standing_fitness_competition.json',
             'standing_fitness_competition02.json', 'standing_hero01.json',
             'standing_hero02.json', 'standing_in_lab.json',
             'standing_old_people.json', 'standing_symmetric.json',
             'standing01.json', 'standing02.json', 'standing03.json',
             'standing04.json', 'standing05.json', 'standing06.json']


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


def generate_id(base_type, pose_id, hair_id):
    date_stamp = datetime.datetime.now().strftime('%Y%m%d')
    character_id = '{}_{}_{}_{}'.format(date_stamp, base_type, hair_id, pose_id)

    return character_id


def initialize_base(base_type):
    """Initialize base character"""
    bpy.data.scenes['Scene'].mblab_character_name = base_type
    bpy.context.scene.mblab_use_lamps = False
    bpy.ops.mbast.init_character()


def set_skin(base_type):
    """Randomize skin age and set to grayscale"""
    bpy.data.objects[base_type].skin_value = 1.0
    bpy.data.objects[base_type].skin_saturation = 0
    bpy.data.objects[base_type].skin_hue = 0.5

    skin_age = random.uniform(0, 1)
    bpy.data.objects[base_type].skin_age = skin_age
    skin_bump = random.uniform(0, 1)
    bpy.data.objects[base_type].skin_bump = skin_bump


def randomize_eyes(base_type):
    """Randomize eye properties"""
    eye_hue = random.uniform(0, 1)
    bpy.data.objects[base_type].eyes_hue = eye_hue
    eye_sat = random.uniform(0, 1)
    bpy.data.objects[base_type].eyes_saturation = eye_sat
    eye_val = random.uniform(0, 1)
    bpy.data.objects[base_type].eyes_value = eye_val


def randomize_character(base_type):
    """Randomize character age, mass, tone"""
    age = random.uniform(-1, 1)
    bpy.data.objects[base_type].character_age = age
    mass = random.betavariate(2, 2) * 2 - 1
    bpy.data.objects[base_type].character_mass = mass
    tone = random.betavariate(2, 2) * 2 - 1
    bpy.data.objects[base_type].character_tone = tone
    set_skin(base_type)
    randomize_eyes(base_type)


def randomize_attributes():
    """Randomize character attributes"""
    bpy.data.scenes['Scene'].mblab_preserve_fantasy = True
    bpy.data.scenes['Scene'].mblab_preserve_mass = True
    bpy.data.scenes['Scene'].mblab_preserve_tone = True
    bpy.data.scenes['Scene'].mblab_random_engine = 'RE'  # use realistic random
    bpy.ops.mbast.character_generator()


def get_sex(base_type):
    """Return sex of base model"""
    if base_type.startswith('f'):
        sex = 'female'
    elif base_type.startswith('m'):
        sex = 'male'
    else:
        print('Your character cannot be clothed')
        return

    return sex


def deselect_all():
    for obj in bpy.context.scene.objects:
        obj.select = False


def get_human_mesh():
    objs = bpy.data.objects
    human_mesh = [obj for obj in objs if obj.name.startswith('MBlab_bd')][0]

    return human_mesh


def append_item(filepath, item_name, human_mesh):
    """Append clothing item to current scene"""
    scn = bpy.context.scene
    item = item_name
    link = False

    # Get item from external file
    with bpy.data.libraries.load(filepath, link=link) as (source, target):
        target.objects = [name for name in source.objects if name.startswith(item)]

    # Append to current scene
    for obj in target.objects:
        if obj is not None:
            scn.objects.link(obj)

    # Proxy fit
    deselect_all()
    human_mesh.select = True
    objs = bpy.data.objects
    item = [obj for obj in objs if obj.name.startswith(item_name)][0]
    item.select = True
    print('fitting item {}'.format(item))
    bpy.ops.mbast.proxy_removefit()
    bpy.context.scene.mblab_overwrite_proxy_weights = True
    bpy.context.scene.mblab_proxy_offset = 5
    # proxy fit spams stdout with Vertex Group error messages
    with OutputRedirect(sys.stdout, '/dev/null'):
        bpy.ops.mbast.proxy_fit()


def get_clothing_path(clothes_path, sex):
    if sex is 'male':
        filepath = os.path.join(clothes_path, 'human_male_clothes.blend')
    elif sex is 'female':
        filepath = os.path.join(clothes_path, 'human_female_clothes.blend')
    else:
        print('No clothes found')
        return

    return filepath


def get_hair_path(hair_path, sex):
    hair_list = ['01', '02', '03', '04', '05', '06', '07']
    hair_type = random.choice(hair_list)

    if sex is 'male':
        filepath = os.path.join(hair_path, 'male_hair_{}.blend'.format(hair_type))
    elif sex is 'female':
        filepath = os.path.join(hair_path, 'female_hair_{}.blend'.format(hair_type))
    else:
        print('No hair found')
        return

    return filepath


def add_clothes(base_type, clothes_path, hair_path):
    """Attach clothes to base model"""
    sex = get_sex(base_type)
    filepath = get_clothing_path(clothes_path, sex)
    human_mesh = get_human_mesh()

    # Append shirt
    append_item(filepath, 'tshirt', human_mesh)

    # Append pants
    append_item(filepath, 'pants', human_mesh)

    # Append hair
    hair_path = get_hair_path(hair_path, sex)
    append_item(hair_path, 'hair', human_mesh)

    hair_id = os.path.splitext(os.path.basename(hair_path))[0]

    return hair_id


def pose(pose_path):
    # choose random default pose if not specified
    if pose_path == '':
        pose = random.choice(pose_list)
        pose_path = os.path.join('data', 'poses', pose)

    print('using pose {}'.format(pose_path))
    human = get_human_mesh()
    human.select = True
    bpy.ops.mbast.pose_load(filepath=pose_path)

    pose_id = os.path.splitext(os.path.basename(pose_path))[0]

    return pose_id


def generate_character(out_dir, base_file, clothes_path, hair_path, pose_path):
    bpy.ops.wm.open_mainfile(filepath=base_file)
    base_type = generate_base_type()
    initialize_base(base_type)
    randomize_character(base_type)
    randomize_attributes()
    bpy.ops.mbast.finalize_character()

    hair_id = add_clothes(base_type, clothes_path, hair_path)

    # Set Pose
    pose_id = pose(pose_path)

    character_id = generate_id(base_type, pose_id, hair_id)

    # Save blender file
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, character_id + '.blend'))

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
    parser.add_argument('--clothing', '-c', type=str, help='path to clothing blends',
                        default='data/clothes')
    parser.add_argument('--hair', '-a', type=str, help='path to hair blends', default='data/hairs')
    parser.add_argument('--out_dir', '-o', type=str, help='output directory for simulants', required=True)
    parser.add_argument('--pose_path', '-p', type=str, help='if included, use a specified pose', default='')

    args, _ = parser.parse_known_args(argv)

    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)

    generate_character(args.out_dir, args.base_file, args.clothing, args.hair, args.pose_path)
