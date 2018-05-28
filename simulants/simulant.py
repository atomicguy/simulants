import ast
import bpy
import bpy_extras
import math
import mathutils
import os
import sys

from simulants import node, render, retex


class HairGenerator:
    def __init__(self, config):
        self.config = config

    def attach_to(self, geo):
        hair = self.config['hair']
        append_item(hair['model'], 'hair', geo)
        render.set_render_layer('hair', hair['render_layer'])
        hair_color = (
            hair['rgb']['r'], hair['rgb']['g'], hair['rgb']['b'], 1)
        retex.recolor_hair(hair_color)
        get_blend_obj('hair').name = hair['id']
        parent_to_skeleton(bpy.data.objects[hair['id']], bpy.data.objects[self.config['skeleton']])


class ShirtGenerator:
    def __init__(self, config):
        self.config = config

    def attach_to(self, geo):
        shirt = self.config['shirt']
        append_item(shirt['model'], 'tshirt', geo)
        render.set_render_layer('tshirt', shirt['render_layer'])
        shirt_mat = node.material('tshirt')
        texture_file = shirt['texture']
        retexture_shirt = getattr(retex, shirt['retexture_type'])
        retexture_shirt(shirt_mat, texture_file)
        get_blend_obj('tshirt').name = shirt['id']
        customize_clothes(shirt['id'], shirt['style'])
        parent_to_skeleton(bpy.data.objects[shirt['id']], bpy.data.objects[self.config['skeleton']])


class PantsGenerator:
    def __init__(self, config):
        self.config = config

    def attach_to(self, geo):
        pants = self.config['pants']
        append_item(pants['model'], 'pants', geo)
        render.set_render_layer('pants', pants['render_layer'])
        pants_mat = node.material('pants')
        texture_file = pants['texture']
        retexture_shirt = getattr(retex, pants['retexture_type'])
        retexture_shirt(pants_mat, texture_file)
        get_blend_obj('pants').name = pants['id']
        customize_clothes(pants['id'], pants['style'])
        parent_to_skeleton(bpy.data.objects[pants['id']], bpy.data.objects[self.config['skeleton']])


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


def clothing_generator(x, sim_values):
    if x == 'hair':
        return HairGenerator(sim_values)
    if x == 'shirt':
        return ShirtGenerator(sim_values)
    if x == 'pants':
        return PantsGenerator(sim_values)


def parent_to_skeleton(obj, skeleton, bone=''):
    """Parent specified object to specified skeleton

    :param obj: mesh to parent to skeleton
    :param skeleton: Simulant skeleton
    :param bone: optional specific bone as target
    """
    obj.parent = skeleton
    if not bone == '':
        obj.parent_type = 'BONE'
        obj.parent_bone = bone


def deselect_all():
    for obj in bpy.context.scene.objects:
        obj.select = False


def get_blend_obj(object_name):
    """Return a specified blender object

    :param object_name: name (or start of name) of object to be returned
    :return: the specified blender object
    """
    objs = bpy.data.objects
    obj_list = [obj for obj in objs if obj.name.startswith(object_name)]
    assert len(obj_list) > 0, 'object {} not found'.format(object_name)

    return obj_list[0]


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


def append_item(filepath, item_name, body):
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
    get_blend_obj(body).select = True
    item = get_blend_obj(item)
    item.select = True
    print('fitting item {}'.format(item))
    bpy.ops.mbast.proxy_removefit()
    bpy.context.scene.mblab_overwrite_proxy_weights = True
    bpy.context.scene.mblab_proxy_offset = 5
    with OutputRedirect(sys.stdout, '/dev/null'):
        bpy.ops.mbast.proxy_fit()


def customize_clothes(clothing_item, mask_name):
    """Use specified mask to customize clothing item

    :param clothing_item: clothing item to customize
    :param mask_name: name of customization mask
    """
    obj = bpy.data.objects[clothing_item]
    mask = obj.modifiers.new(name='pmask', type='MASK')
    mask.vertex_group = mask_name


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
    center_bone_relative = mathutils.Vector((0, -(2/3) * skeleton.pose.bones['head'].length, 0))
    head_proxy.location = center_bone_relative
