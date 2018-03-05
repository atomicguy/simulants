import os
import re
import sys
import bpy
import code
import math
import random
import datetime

from argparse import ArgumentParser


def set_hdri(background, intensity):
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

    return (basename)


def set_passes(context):
    nodes = context.scene.node_tree.nodes
    for n in nodes:
        nodes.remove(n)

    rl = context.scene.render.layers['RenderLayer']

    rl.use_pass_combined = True
    rl.use_pass_z = True
    rl.use_pass_mist = False
    rl.use_pass_normal = False
    rl.use_pass_vector = True
    rl.use_pass_uv = True
    rl.use_pass_object_index = False
    rl.use_pass_material_index = True
    rl.use_pass_shadow = False
    rl.use_pass_ambient_occlusion = True


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

    output = ''
    if passout in output_dict.keys():
        output = output_dict[passout]
    elif "_" in passout:
        wl = passout.split("_")  # Split to list of words
        # Capitalize first char in each word and rejoin with spaces
        output = " ".join([s[0].capitalize() + s[1:] for s in wl])
    else:  # If one word, just capitlaize first letter
        output = passout[0].capitalize() + passout[1:]

    return output


def make_file_out_node(context, render_id, image_out):
    bpy.data.scenes['Scene'].use_nodes = True
    tree = context.scene.node_tree
    links = tree.links

    layers = get_layers_and_passes(bpy.context, render_id)

    nodes = tree.nodes
    for n in nodes:
        nodes.remove(n)

    # Add one Render Layers node
    nodes.new('CompositorNodeRLayers')

    output_node = tree.nodes.new('CompositorNodeOutputFile')
    output_node.base_path = image_out

    layer = layers['RenderLayer']

    for rpass in layer:
        output = get_output(rpass['output'])
        filename = rpass['filename']

        # Set skin/clothes/hair indecies correctly
        if output == 'IndexMA':
            # skin now only applies to face
            skin_node = tree.nodes.new('CompositorNodeIDMask')
            skin_node.index = 1
            links.new(tree.nodes['Render Layers'].outputs[output], skin_node.inputs[0])
            output_node.file_slots.new(name='head')
            output_node.file_slots[-1].path = 'head_' + filename
            links.new(skin_node.outputs[0], output_node.inputs[-1])

            shirt_node = tree.nodes.new('CompositorNodeIDMask')
            shirt_node.index = 2
            links.new(tree.nodes['Render Layers'].outputs[output], shirt_node.inputs[0])
            output_node.file_slots.new(name='shirt')
            output_node.file_slots[-1].path = 'shirt_' + filename
            links.new(shirt_node.outputs[0], output_node.inputs[-1])

            pants_node = tree.nodes.new('CompositorNodeIDMask')
            pants_node.index = 3
            links.new(tree.nodes['Render Layers'].outputs[output], pants_node.inputs[0])
            output_node.file_slots.new(name='pants')
            output_node.file_slots[-1].path = 'pants_' + filename
            links.new(pants_node.outputs[0], output_node.inputs[-1])

            hair_node = tree.nodes.new('CompositorNodeIDMask')
            hair_node.index = 4
            links.new(tree.nodes['Render Layers'].outputs[output], hair_node.inputs[0])
            output_node.file_slots.new(name='hair')
            output_node.file_slots[-1].path = 'hair_' + filename
            links.new(hair_node.outputs[0], output_node.inputs[-1])

            body_node = tree.nodes.new('CompositorNodeIDMask')
            body_node.index = 5
            links.new(tree.nodes['Render Layers'].outputs[output], body_node.inputs[0])
            output_node.file_slots.new(name='body')
            output_node.file_slots[-1].path = 'body_' + filename
            links.new(body_node.outputs[0], output_node.inputs[-1])

        elif output == 'Image':
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

        elif output == 'Depth':
            normalize_node = tree.nodes.new('CompositorNodeNormalize')
            links.new(tree.nodes['Render Layers'].outputs['Depth'], normalize_node.inputs[0])
            output_node.file_slots.new(name='depth')
            output_node.file_slots[-1].path = 'depth_' + filename
            links.new(normalize_node.outputs['Value'], output_node.inputs['depth'])

        else:
            output_node.file_slots.new(name=output)
            output_node.file_slots[-1].path = filename
            links.new(tree.nodes['Render Layers'].outputs[output], output_node.inputs[-1])


def get_human_mesh():
    objs = bpy.data.objects
    human_mesh = [obj for obj in objs if obj.name.startswith('MBlab_bd')][0]

    return human_mesh


def make_all_skin():
    human = get_human_mesh()
    try:
        generic_slot = [mat for mat in human.material_slots if mat.name.startswith('MBlab_generic')][0]
        skin_material = [mat for mat in bpy.data.materials if mat.name.startswith('MBlab_human_skin')][0]

        generic_slot.material = skin_material
    except:
        print('already nude')


def set_render_layer():
    """Set Skin, Shirt, Pants render layers to 1, 2, 3"""
    materials = bpy.data.materials

    templist = [mat for mat in materials if mat.name.startswith('MBlab_human_skin')]
    assert len(templist) > 0, 'no skin material found'
    skin_mat = [mat for mat in materials if mat.name.startswith('MBlab_human_skin')][0]
    skin_mat.pass_index = 1

    # Shirt Material Settings
    shirt_mat = [mat for mat in materials if mat.name.startswith('tshirt')][0]
    shirt_mat.pass_index = 2
    # set material diffuse to 0.9 grey
    shirt_nodes = shirt_mat.node_tree.nodes
    shirt_diffuse = shirt_nodes.get('Diffuse BSDF')
    shirt_diffuse.inputs['Color'].default_value = (0.9, 0.9, 0.9, 1)

    # Pants Material Settings
    pants_mat = [mat for mat in materials if mat.name.startswith('pants')][0]
    pants_mat.pass_index = 3
    # set material diffuse to 0.9 grey
    pants_nodes = pants_mat.node_tree.nodes
    pants_diffuse = pants_nodes.get('Diffuse BSDF')
    pants_diffuse.inputs['Color'].default_value = (0.9, 0.9, 0.9, 1)

    # Hair Material Settings
    hair_mat = [mat for mat in materials if mat.name.startswith('hair')][0]
    hair_mat.pass_index = 4


def randomize_shirt():
    """shirt_sleeveless is only male and shirt_croptop is only female so defaults to full shirt on other sex"""
    shirt_masks = ['shirt_neck', 'shirt_sleeveless', 'shirt_croptop', 'shirt_open_front',
                   'shirt_short_1', 'shirt_short_2']
    shirt = [obj for obj in bpy.data.objects if obj.name.startswith('tshirt')][0]
    mask = shirt.modifiers.new(name='smask', type='MASK')
    mask.vertex_group = random.choice(shirt_masks)


def randomize_pants():
    pants_masks = ['', 'shorts_1', 'shorts_2', 'shorts_3']
    pants = [obj for obj in bpy.data.objects if obj.name.startswith('pants')][0]
    mask = pants.modifiers.new(name='pmask', type='MASK')
    mask.vertex_group = random.choice(pants_masks)


def randomize_clothing():
    randomize_shirt()
    randomize_pants()


def load_animation(animation_path):
    for obj in bpy.data.objects:
        obj.select = False
    human = [obj for obj in bpy.data.objects if obj.name.startswith('MBlab_sk')][0]
    human.select = True
    bpy.ops.mbast.pose_reset()
    bpy.ops.mbast.load_animation(filepath=animation_path)


def setup_head_mask():
    # Deselect all objects
    for obj in bpy.data.objects:
        obj.select = False

    # Select just the human
    human_mesh = [obj for obj in bpy.data.objects if obj.name.startswith('MBlab_bd')][0]
    bpy.context.scene.objects.active = human_mesh

    # Copy skin material into new material slot on body mesh
    skin_mat = [mat for mat in bpy.data.materials if mat.name.startswith('MBlab_human_skin')][0]
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

    # Assign body material to body vertecies
    human_mesh.active_material_index = human_mesh.material_slots.find('body')
    bpy.ops.object.material_slot_assign()

    bpy.ops.object.mode_set(mode='OBJECT')


def set_render_settings():
    bpy.data.scenes['Scene'].cycles.film_transparent = True
    # bpy.context.scene.render.layers[0].cycles.use_denoising = True
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


def generate_character(blend_in, background, image_out, percent_size, render_id, blend_save, animation_path):
    bpy.ops.wm.open_mainfile(filepath=blend_in)
    randomize_clothing()

    # Move camera to static position for mocap sequence
    bpy.data.objects['Camera'].location = (0, -5, 1.5)
    bpy.data.objects['Camera'].rotation_euler = (math.radians(90), 0, 0)

    set_hdri(background, 4)
    set_render_layer()

    set_passes(bpy.context)
    setup_head_mask()

    make_file_out_node(bpy.context, render_id, image_out)
    make_all_skin()

    # Render Scene
    set_render_settings()
    full_rgb_path = os.path.join(image_out, 'rgba_comp', render_id + '_')
    bpy.data.scenes['Scene'].render.filepath = full_rgb_path
    bpy.data.scenes['Scene'].render.resolution_percentage = percent_size
    bpy.context.scene.render.tile_x = 32
    bpy.context.scene.render.tile_y = 32

    load_animation(animation_path)
    bpy.context.scene.frame_step = 5

    bpy.ops.render.render(animation=True)
    # bpy.ops.render.render()

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
    parser.add_argument('--blend_in', '-f', type=str, help='path to input blender file', required=True)
    parser.add_argument('--background', '-i', type=str, help='background image to use for hdri lighting',
                        required=True)
    parser.add_argument('--img_out', '-o', type=str, help='render image output', required=True)
    parser.add_argument('--percent_size', '-p', type=int, help='image size percent of 2048', required=True)
    parser.add_argument('--render_id', '-r', type=str, help='unique id for render generated if set to time',
                        required=True)
    parser.add_argument('--blend_save', '-b', type=str, help='if set, directory to save blend files', default='')
    parser.add_argument('--animation_path', '-a', type=str, help='path to animation bvh file')
    args, _ = parser.parse_known_args(argv)

    if args.render_id is 'time':
        file_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    else:
        file_id = args.render_id

    generate_character(args.blend_in, args.background, args.img_out, args.percent_size, file_id, args.blend_save, args.animation_path)
