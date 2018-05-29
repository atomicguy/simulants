from __future__ import absolute_import, division, print_function

import ast
import bpy
import math
import mathutils

from simulants import node, render
from simulants.generators.hair import HairGenerator
from simulants.generators.shirt import ShirtGenerator
from simulants.generators.pants import PantsGenerator

from simulants.blend_ops import parent_to_skeleton, deselect_all, get_blend_obj


class SimulantGenerator:
    def __init__(self, config):
        self.config = config
        initialize_base(self.config['base_mesh'])

    def personalize(self):
        set_skin(self.config['base_mesh'], self.config['skin']['hue'], self.config['skin']['saturation'],
                 self.config['skin']['value'], self.config['skin']['age'], self.config['skin']['bump'])
        set_eyes(self.config['base_mesh'], self.config['eye']['hue'], self.config['eye']['saturation'],
                 self.config['eye']['value'])
        set_traits(self.config['base_mesh'], self.config['traits']['age'], self.config['traits']['mass'],
                   self.config['traits']['tone'])
        make_unique(self.config['randomize'])
        finalize()

        # Rename
        get_blend_obj('MBlab_sk').name = self.config['skeleton']
        get_blend_obj('MBlab_bd').name = self.config['geometry']

        # Uncensor
        uncensor(self.config['geometry'])

        # Set render layers
        materials = [mat.name for mat in bpy.data.materials]
        for mat in materials:
            if mat.startswith('MBlab_human_skin'):
                render.set_render_layer(mat, self.config['skin']['render_layer'])
            else:
                render.set_render_layer(mat, self.config['misc']['render_layer'])

        # Generate head proxy and parent to head bone
        head_info = head_properties(self.config['skeleton'])
        head_proxy(self.config['skeleton'], head_info, self.config['head_proxy']['id'])

    def set_position(self):
        rotate(self.config['skeleton'], self.config['rotation']['z'])
        position(self.config['skeleton'], self.config['location'])

    def clothe(self):
        for x in ['hair', 'shirt', 'pants']:
            cfg = clothing_generator(x, self.config)
            cfg.attach_to(self.config['geometry'])

    def set_pose(self):
        pose(self.config['geometry'], self.config['pose'])


def clothing_generator(x, sim_values):
    if x == 'hair':
        return HairGenerator(sim_values)
    if x == 'shirt':
        return ShirtGenerator(sim_values)
    if x == 'pants':
        return PantsGenerator(sim_values)


def get_mat_slot(blend_object, name):
    """Return a specified material slot for a given blender object

    :param blend_object: blender object with material slots
    :param name: name of material slot to return
    :return: specified material slot
    """
    mat_slots = [mat for mat in blend_object.material_slots if mat.name.startswith(name)]
    assert len(mat_slots) > 0, 'slot {} not found on object {}'.format(name, blend_object)

    return mat_slots[0]


def initialize_base(base_type):
    """Initialize base character"""
    bpy.data.scenes['Scene'].mblab_character_name = base_type
    bpy.context.scene.mblab_use_lamps = False
    bpy.ops.mbast.init_character()


def set_skin(mesh_name, hue, sat, value, age, bump):
    """Initialize simulant skin properties

    :param mesh_name: mesh id
    :param hue: hue of skin
    :param sat: saturation of skin
    :param value: value of skin
    :param age: skin age
    :param bump: skin bump
    """
    bpy.data.objects[mesh_name].skin_hue = hue
    bpy.data.objects[mesh_name].skin_saturation = sat
    bpy.data.objects[mesh_name].skin_value = value

    bpy.data.objects[mesh_name].skin_age = age
    bpy.data.objects[mesh_name].skin_bump = bump


def set_eyes(mesh_name, hue, sat, value):
    """Set eye color

    :param mesh_name: simulant mesh id
    :param hue: eye color hue
    :param sat: eye color saturation
    :param value: eye color value
    """
    bpy.data.objects[mesh_name].eyes_hue = hue
    bpy.data.objects[mesh_name].eyes_saturation = sat
    bpy.data.objects[mesh_name].eyes_value = value


def set_traits(mesh_name, age, mass, tone):
    """Set character traits

    :param mesh_name: simulant mesh name
    :param age: simulant apparent age
    :param mass: simulant body mass
    :param tone: simulant muscle tone
    """
    bpy.data.objects[mesh_name].character_age = age
    bpy.data.objects[mesh_name].character_mass = mass
    bpy.data.objects[mesh_name].character_tone = tone


def make_unique(preservations):
    """Use MBLab Randomize function to make a unique simulant"""
    bpy.data.scenes['Scene'].mblab_random_engine = 'RE'  # use realistic random
    for category, choice in preservations.items():
        setattr(bpy.data.scenes['Scene'], category, ast.literal_eval(choice))

    bpy.ops.mbast.character_generator()


def finalize():
    """Bake characteristics into final simulant"""
    bpy.ops.mbast.finalize_character()


def pose(body, pose_path):
    deselect_all()
    human = get_blend_obj(body)
    human.select = True
    bpy.ops.mbast.pose_load(filepath=pose_path)


def uncensor(body):
    """set all skin geometry to skin texture (i.e. remove modesty material)"""
    human = get_blend_obj(body)
    generic_slot = get_mat_slot(human, 'MBlab_generic')
    skin_material = node.material('MBlab_human_skin')

    generic_slot.material = skin_material


def get_bone(skeleton, bone_name):
    """Return bone of given name"""
    skeleton = get_blend_obj(skeleton)
    bone = skeleton.pose.bones[bone_name]

    return bone


def rotate(skeleton, angle):
    root = get_bone(skeleton, 'root')
    # obj = bpy.data.objects[skeleton]
    root.rotation_mode = 'XYZ'
    root.rotation_euler.rotate_axis('Z', math.radians(angle))


def position(skeleton, location):
    # root = get_bone(skeleton, 'root')
    obj = bpy.data.objects[skeleton]
    loc = (location['x'], location['y'], location['z'])
    obj.location = loc


def head_properties(skeleton):
    """Return estimated head data calculated from simulant head bone"""
    head = bpy.data.objects[skeleton].pose.bones['head']
    length = head.length

    head_radius = length * (2 / 3)
    head_center = head.head + (head.vector * (1 / 3))  # world-space

    distance = get_blend_obj('Camera').location - head_center

    return {'radius': head_radius, 'center': head_center, 'distance': distance.length}


def head_proxy(base_skeleton, measurements, proxy_id):
    """Create a head proxy sphere

    :param base_skeleton: skeleton to which head is attached
    :param measurements: radius and location information
    :param proxy_id: unique id for this head proxy
    """
    bpy.ops.mesh.primitive_uv_sphere_add(size=measurements['radius'], location=measurements['center'])
    bpy.context.active_object.name = proxy_id
    head_proxy = bpy.data.objects[proxy_id]

    # Parent to Head Bone
    skeleton = get_blend_obj(base_skeleton)
    parent_to_skeleton(head_proxy, skeleton, bone='head')

    # Fix translation (move -Y two thirds as head bone's tail is now origin)
    center_bone_relative = mathutils.Vector((0, -(2 / 3) * skeleton.pose.bones['head'].length, 0))
    head_proxy.location = center_bone_relative


def head_proxy_properties(head_proxy):
    """Return current head proxy properties"""
    proxy = bpy.data.objects[head_proxy]
    head_center = proxy.matrix_world.to_translation()
    head_radius = proxy.dimensions[0] / 2
    distance = get_blend_obj('Camera').location - head_center

    return {'radius': head_radius, 'center': head_center, 'distance': distance.length}
