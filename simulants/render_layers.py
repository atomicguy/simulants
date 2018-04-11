import os
import re
import sys
import bpy
import code
import math
import random
import datetime

from argparse import ArgumentParser


def rotate_camera():
    rot_x = math.radians(90)
    rot_y = 0
    rot_z = random.uniform(0, math.radians(360))
    bpy.data.objects['Camera'].rotation_euler = (rot_x, rot_y, rot_z)


def fit_camera():
    for obj in bpy.context.visible_objects:
        if not (obj.hide or obj.hide_render):
            obj.select = True

    bpy.ops.view3d.camera_to_view_selected()


def hdri_lighting(background, intensity):
    """use background image as hdri environment lighting source"""
    nw_world = bpy.data.worlds.new('hdri_tree')
    bpy.context.scene.world = nw_world
    bpy.context.scene.world.use_nodes = True
    nodes = nw_world.node_tree.nodes
    tree = nw_world.node_tree
    img = bpy.data.images.load(background)
    node_env = nodes.new('ShaderNodeTexEnvironment')
    node_env.name = "ENVIRONMENT"
    node_env.image = img
    node_bkgd = tree.nodes['Background']
    node_bkgd.inputs[1].default_value = intensity
    tree.links.new(node_env.outputs['Color'], node_bkgd.inputs['Color'])


def find_base_name():
    blendfile = bpy.path.basename(bpy.data.filepath)

    pattern = '^([\d\w_-]+)(\.blend)$'
    re_match = re.match(pattern, blendfile)
    basename = 'scene'  # Default to avoid empty strings

    if re_match:
        if len(re_match.groups()) > 0:
            basename = re_match.groups()[0]

    return basename


def get_layers_and_passes(context, render_id):
    rl = context.scene.render.layers
    # use_folders = context.scene.folder_props.create_folders

    layers = {}
    pass_attr_str = 'use_pass_'

    for l in rl:
        layers[l.name] = []

        # List all the attributes of the render layer pass with dir
        # then isolate all the render pass attributes
        passes = [p for p in dir(l) if pass_attr_str in p]

        for p in passes:
            # If render pass is active (True) - create output
            if getattr(l, p):
                pass_name = p[len(pass_attr_str):]

                file_path = pass_name + '/' + render_id + '_'

                pass_info = {
                    'filename': file_path,
                    'output': pass_name
                }

                layers[l.name].append(pass_info)

        image_path = 'Image/' + render_id + '_'
        pass_info = {'filename': image_path}
        layers['Image'] = []
        layers['Image'].append(pass_info)

    return layers


def get_output(passout):
    # Renderlayer pass names and renderlayer node output names do not match
    # which is why we're using this dictionary (and regular expressions)
    # to match the two
    output_dict = {
        'ambient_occlusion': 'AO',
        'material_index': 'IndexMA',
        'object_index': 'IndexOB',
        'reflection': 'Reflect',
        'refraction': 'Refract',
        'combined': 'Image',
        'uv': 'UV',
        'z': 'Depth'
    }

    if passout in output_dict.keys():
        output = output_dict[passout]
    elif "_" in passout:
        wl = passout.split("_")  # Split to list of words
        # Capitalize first char in each word and rejoin with spaces
        output = " ".join([s[0].capitalize() + s[1:] for s in wl])
    else:  # If one word, just capitlaize first letter
        output = passout[0].capitalize() + passout[1:]

    return output


def make_image_out_nodes(links, tree, output_node, output, filename):
    """Generate Image output setup of value only"""
    # Break out Value channel
    value_node = tree.nodes.new('CompositorNodeSepHSVA')
    links.new(tree.nodes['Render Layers'].outputs[output], value_node.inputs[0])

    # Copy Value into RGB channels
    combo_node = tree.nodes.new('CompositorNodeCombRGBA')
    links.new(value_node.outputs['V'], combo_node.inputs['R'])
    links.new(value_node.outputs['V'], combo_node.inputs['G'])
    links.new(value_node.outputs['V'], combo_node.inputs['B'])

    # Combine with original alpha
    alpha_node = tree.nodes.new('CompositorNodeSetAlpha')
    links.new(combo_node.outputs['Image'], alpha_node.inputs['Image'])
    links.new(tree.nodes['Render Layers'].outputs['Alpha'], alpha_node.inputs['Alpha'])

    # Send new image to Image
    links.new(alpha_node.outputs['Image'], output_node.inputs['Image'])
    output_node.file_slots['Image'].path = 'image_' + filename


def new_mat_index_nodes(index, name, tree, links, output, output_node, filename):
    """Generate material index layer and link to output"""
    new_node = tree.nodes.new('CompositorNodeIDMask')
    new_node.index = index
    links.new(tree.nodes['Render Layers'].outputs[output], new_node.inputs[0])
    output_node.file_slots.new(name=name)
    output_node.file_slots[-1].path = '{}_{}'.format(name, filename)
    links.new(new_node.outputs[0], output_node.inputs[-1])


def make_mat_index_layers(tree, links, output, output_node, filename):
    """Break material indices out into individual outputs"""
    new_mat_index_nodes(1, 'head', tree, links, output, output_node, filename)
    new_mat_index_nodes(2, 'shirt', tree, links, output, output_node, filename)
    new_mat_index_nodes(3, 'pants', tree, links, output, output_node, filename)
    new_mat_index_nodes(4, 'hair', tree, links, output, output_node, filename)
    new_mat_index_nodes(5, 'body', tree, links, output, output_node, filename)


def output_exr(tree, links, output_node, filename, render_name, out_name):
    """Export layer as EXR"""
    output_node.file_slots.new(name=out_name)
    output_node.file_slots[-1].path = filename
    output_node.file_slots[-1].use_node_format = False
    output_node.file_slots[-1].format.file_format = 'OPEN_EXR'
    links.new(tree.nodes['Render Layers'].outputs[render_name], output_node.inputs[out_name])


def make_file_out_node(context, layers, image_out):
    """"""
    bpy.data.scenes['Scene'].use_nodes = True
    tree = context.scene.node_tree
    links = tree.links

    # Remove old composite node
    nodes = tree.nodes
    for n in nodes:
        nodes.remove(n)

    # Add one Render Layers node
    nodes.new('CompositorNodeRLayers')

    output_node = tree.nodes.new('CompositorNodeOutputFile')
    output_node.base_path = image_out

    layer = layers['RenderLayer']

    for render_pass in layer:
        output = get_output(render_pass['output'])
        filename = render_pass['filename']

        if output == 'IndexMA':
            make_mat_index_layers(tree, links, output, output_node, filename)

        elif output == 'Image':
            make_image_out_nodes(links, tree, output_node, output, filename)

        elif output == 'Depth':
            output_exr(tree, links, output_node, filename, 'Depth', 'depth')

        elif output == 'UV':
            output_exr(tree, links, output_node, filename, 'UV', 'uv')

        elif output == 'Normal':
            output_exr(tree, links, output_node, filename, 'Normal', 'normal')

        else:
            output_node.file_slots.new(name=output)
            output_node.file_slots[-1].path = filename
            links.new(tree.nodes['Render Layers'].outputs[output], output_node.inputs[-1])


def get_blend_obj(object_name):
    """Return a specified blender object

    :param object_name: name (or start of name) of object to be returned
    :return: the specified blender object
    """
    objs = bpy.data.objects
    obj_list = [obj for obj in objs if obj.name.startswith(object_name)]
    assert len(obj_list) > 0, 'object {} not found'.format(object_name)

    return obj_list[0]


def get_blend_mat(material_name):
    """Return a specified material from a blender scene

    :param material_name: (start of) name of material to return
    :return: the specified material
    """
    materials = bpy.data.materials
    mat_list = [mat for mat in materials if mat.name.startswith(material_name)]
    assert len(mat_list) > 0, 'material {} not found'.format(material_name)

    return mat_list[0]


def get_mat_slot(blend_object, name):
    """Return a specified material slot for a given blender object

    :param blend_object: blender object with material slots
    :param name: name of material slot to return
    :return: specified material slot
    """
    mat_slots = [mat for mat in blend_object.material_slots if mat.name.startswith(name)]
    assert len(mat_slots) > 0, 'slot {} not found on object {}'.format(name, blend_object)

    return mat_slots[0]


def get_human_mesh():
    """Get the mesh human object from a blend scene"""

    return get_blend_obj('MBlab_bd')


def make_all_skin():
    """set all skin geometry to skin texture (i.e. remove modesty material)"""
    human = get_human_mesh()
    generic_slot = get_mat_slot(human, 'MBlab_generic')
    skin_material = get_blend_mat('MBlab_human_skin')

    generic_slot.material = skin_material


def set_material_diffuse_color(material, color):
    """Set Diffuse BSDF color chanel to specified color

    :param material: material
    :param color: (R, G, B, A) float color
    """
    mat_nodes = material.node_tree.nodes
    shirt_diffuse = mat_nodes.get('Diffuse BSDF')
    shirt_diffuse.inputs['Color'].default_value = color


def set_render_layer(name, index, color=None):
    """Set material of name to specified index"""
    mat = get_blend_mat(name)
    mat.pass_index = index
    if color:
        set_material_diffuse_color(mat, color)


def set_render_layers():
    """Set indices of render layers"""
    set_render_layer('MBlab_human_skin', 1)
    ten_percent_gray = (0.9, 0.9, 0.9, 1)
    set_render_layer('tshirt', 2, ten_percent_gray)
    set_render_layer('pants', 3, ten_percent_gray)
    set_render_layer('hair', 4)


def set_output_nodes(context, render_id, image_name):
    """Generate output nodes as needed"""
    full_rgb_path = os.path.join(image_name, 'rgba_comp', render_id + '_')
    print('full rgb: {}'.format(full_rgb_path))
    bpy.context.scene.render.filepath = full_rgb_path
    # bpy.data.scenes['Scene'].render.filepath = full_rgb_path
    layers = get_layers_and_passes(context, render_id)
    make_file_out_node(context, layers, image_name)


def set_passes(context):
    """Enable/disable known render passes"""
    nodes = context.scene.node_tree.nodes
    for n in nodes:
        nodes.remove(n)

    rl = context.scene.render.layers['RenderLayer']

    rl.use_pass_combined = True
    rl.use_pass_z = True
    rl.use_pass_mist = False
    rl.use_pass_normal = True
    rl.use_pass_vector = True
    rl.use_pass_uv = False
    rl.use_pass_object_index = False
    rl.use_pass_material_index = True
    rl.use_pass_shadow = False
    rl.use_pass_ambient_occlusion = True


def set_render_settings(percent_size, tile_size):
    """Set Cycles to known good render settings"""
    bpy.data.scenes['Scene'].cycles.film_transparent = True
    bpy.data.scenes['Scene'].render.resolution_percentage = percent_size
    bpy.context.scene.render.tile_x = tile_size
    bpy.context.scene.render.tile_y = tile_size

    bpy.context.scene.render.layers[0].cycles.use_denoising = False
    bpy.context.scene.render.layers[0].cycles.denoising_radius = 4
    bpy.context.scene.cycles.sampling_pattern = 'CORRELATED_MUTI_JITTER'

    bpy.context.scene.cycles.max_bounces = 8
    bpy.context.scene.cycles.min_bounces = 2

    bpy.context.scene.cycles.aa_samples = 4
    bpy.context.scene.cycles.diffuse_samples = 2
    bpy.context.scene.cycles.glossy_samples = 1
    bpy.context.scene.cycles.transmission_samples = 1
    bpy.context.scene.cycles.ao_samples = 2
    bpy.context.scene.cycles.mesh_light_samples = 1
    bpy.context.scene.cycles.subsurface_samples = 1
    bpy.context.scene.cycles.volume_samples = 1

    bpy.context.scene.cycles.transparent_min_bounces = 2
    bpy.context.scene.cycles.transparent_max_bounces = 4
    bpy.context.scene.cycles.transmission_bounces = 2
    bpy.context.scene.cycles.glossy_bounces = 2
    bpy.context.scene.cycles.max_bounces = 8


def set_uv_passes(context):
    """Enable/disable known render passes"""
    nodes = context.scene.node_tree.nodes
    for n in nodes:
        nodes.remove(n)

    rl = context.scene.render.layers['RenderLayer']

    rl.use_pass_combined = False
    rl.use_pass_z = False
    rl.use_pass_mist = False
    rl.use_pass_normal = False
    rl.use_pass_vector = False
    rl.use_pass_uv = True
    rl.use_pass_object_index = False
    rl.use_pass_material_index = False
    rl.use_pass_shadow = False
    rl.use_pass_ambient_occlusion = False


def set_uv_render_settings(percent_size, tile_size):
    """Set Cycles to known good render settings"""
    bpy.data.scenes['Scene'].cycles.film_transparent = True
    bpy.data.scenes['Scene'].render.resolution_percentage = percent_size
    bpy.context.scene.render.tile_x = tile_size
    bpy.context.scene.render.tile_y = tile_size

    bpy.context.scene.render.layers[0].cycles.use_denoising = False
    bpy.context.scene.render.layers[0].cycles.denoising_radius = 4
    bpy.context.scene.cycles.sampling_pattern = 'CORRELATED_MUTI_JITTER'

    bpy.context.scene.cycles.aa_samples = 1


def randomize_shirt():
    """shirt_sleeveless is only male and shirt_croptop is only female so defaults to full shirt on other sex"""
    shirt_masks = ['shirt_neck', 'shirt_sleeveless', 'shirt_croptop', 'shirt_open_front',
                   'shirt_short_1', 'shirt_short_2']
    shirt = get_blend_obj('tshirt')
    mask = shirt.modifiers.new(name='smask', type='MASK')
    mask.vertex_group = random.choice(shirt_masks)


def randomize_pants():
    """Randomize pants length"""
    pants_masks = ['', 'shorts_1', 'shorts_2', 'shorts_3']
    pants = get_blend_obj('pants')
    mask = pants.modifiers.new(name='pmask', type='MASK')
    mask.vertex_group = random.choice(pants_masks)


def randomize_clothing():
    randomize_shirt()
    randomize_pants()


def setup_head_mask():
    # Deselect all objects
    for obj in bpy.data.objects:
        obj.select = False

    # Select just the human
    human_mesh = get_human_mesh()
    bpy.context.scene.objects.active = human_mesh

    # Copy skin material into new material slot on body mesh
    skin_mat = get_blend_mat('MBlab_human_skin')
    body_mat = skin_mat.copy()
    body_mat.name = 'body'
    human_mesh.data.materials.append(body_mat)
    body_mat.pass_index = 5

    # Select the vertecies in the body only
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_set_active(group='head')
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.select_all(action='INVERT')

    # Assign body material to body vertices
    human_mesh.active_material_index = human_mesh.material_slots.find('body')
    bpy.ops.object.material_slot_assign()

    bpy.ops.object.mode_set(mode='OBJECT')


def import_character(blend_file):
    """Open character file and standardize skin, clothes, and head"""
    bpy.ops.wm.open_mainfile(filepath=blend_file)
    make_all_skin()
    randomize_clothing()
    setup_head_mask()


def load_animation(animation_path):
    for obj in bpy.data.objects:
        obj.select = False
    human = get_blend_obj('MBlab_sk')
    human.select = True
    bpy.ops.mbast.pose_reset()
    bpy.ops.mbast.load_animation(filepath=animation_path)


def set_mocap_camera():
    bpy.data.objects['Camera'].location = (0, -5, 1.5)
    bpy.data.objects['Camera'].rotation_euler = (math.radians(90), 0, 0)


def render_multi_pass(render_id, image_out, percent_size, tile_size, animation):
    # Set up material render layers for masks
    set_render_layers()

    # UV layer render
    set_uv_passes(bpy.context)
    set_output_nodes(bpy.context, render_id, image_out)
    set_uv_render_settings(percent_size, tile_size)
    bpy.ops.render.render(animation=animation)

    # Anti-Aliased Normal Render
    set_passes(bpy.context)
    set_output_nodes(bpy.context, render_id, image_out)
    set_render_settings(percent_size, tile_size)
    bpy.ops.render.render(animation=animation)


def render_character(blend_in, background, image_out, percent_size, render_id, blend_save, animation, steps):
    """Import character, set up rendering, and render layers"""
    import_character(blend_in)

    hdri_lighting(background, 4)
    # set_render_layers()
    # set_passes(bpy.context)
    # set_output_nodes(bpy.context, render_id, image_out)
    # set_render_settings(percent_size, 32)

    if animation is '':
        rotate_camera()
        fit_camera()
        # bpy.ops.render.render()
        render_multi_pass(render_id, image_out, percent_size, 32, False)
    else:
        set_mocap_camera()
        load_animation(animation)
        bpy.context.scene.frame_step = steps
        # bpy.ops.render.render(animation=True)
        render_multi_pass(render_id, image_out, percent_size, 32, True)

    if blend_save is not '':
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(blend_save, render_id + '.blend'))


if __name__ == '__main__':
    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    parser = ArgumentParser()
    parser.add_argument('--blend_in', '-f', type=str, help='character input blender file', required=True)
    parser.add_argument('--background', '-i', type=str, help='background image to use for hdri lighting',
                        required=True)
    parser.add_argument('--img_out', '-o', type=str, help='render image output', required=True)
    parser.add_argument('--percent_size', '-p', type=int, help='image size percent of 2048', required=True)
    parser.add_argument('--render_id', '-r', type=str, help='unique id for render generated if set to time',
                        required=True)
    parser.add_argument('--blend_save', '-b', type=str, help='if set, directory to save blend files', default='')
    parser.add_argument('--animation', '-a', type=str, help='if set, directory to mocap animation file', default='')
    parser.add_argument('--stride', '-s', type=int, help='frame steps; 1 is all frames', default=5)
    args, _ = parser.parse_known_args(argv)

    if args.render_id is 'time':
        file_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    else:
        file_id = args.render_id

    render_character(args.blend_in, args.background, args.img_out, args.percent_size, file_id, args.blend_save,
                     args.animation, args.stride)
