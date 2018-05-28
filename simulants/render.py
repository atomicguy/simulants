import os
import bpy


class MaterialNodeGenerator:
    def __init__(self, config):
        self.config = config

    def connect(self, material_name, tree, output_node):
        links = tree.links
        object_id = self.config['id']
        layer = self.config[material_name]['render_layer']
        path = object_id + '/' + material_name
        new_mat_index_nodes(layer, path, tree, links, 'IndexMA', output_node, object_id)


def get_blend_mat(material_name):
    """Return a specified material from a blender scene

    :param material_name: (start of) name of material to return
    :return: the specified material
    """
    materials = bpy.data.materials
    mat_list = [mat for mat in materials if mat.name.startswith(material_name)]
    assert len(mat_list) > 0, 'material {} not found'.format(material_name)

    return mat_list[0]


def set_render_layer(name, index):
    """Set material of name to specified index"""
    mat = get_blend_mat(name)
    mat.pass_index = index


def set_render_layers():
    """Set indices of render layers"""
    set_render_layer('MBlab_human_skin', 1)
    set_render_layer('tshirt', 2)
    set_render_layer('pants', 3)
    set_render_layer('hair', 4)
    set_render_layer('MBlab_pupil', 6)
    set_render_layer('MBlab_human_teeth', 6)
    set_render_layer('MBlab_fur', 6)
    set_render_layer('MBlab_human_eyes', 6)
    set_render_layer('MBlab_cornea', 6)


def set_image_size(image_size, percent_size):
    """Set image properties

    :param image_size: [w, h] in pixels
    :param percent_size: percent size (usually 100)
    """
    bpy.data.scenes['Scene'].render.resolution_percentage = percent_size
    bpy.data.scenes['Scene'].render.resolution_x = image_size[0]
    bpy.data.scenes['Scene'].render.resolution_y = image_size[1]


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


def set_render_settings(image_size, percent_size, tile_size):
    """Set Cycles to known good render settings"""
    bpy.data.scenes['Scene'].layers[1] = False
    bpy.data.scenes['Scene'].layers[0] = True

    set_image_size(image_size, percent_size)
    bpy.data.scenes['Scene'].cycles.film_transparent = False
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


def set_uv_render_settings(image_size, percent_size, tile_size):
    """Set Cycles to known good render settings"""
    set_image_size(image_size, percent_size)
    bpy.data.scenes['Scene'].cycles.film_transparent = True
    bpy.context.scene.render.tile_x = tile_size
    bpy.context.scene.render.tile_y = tile_size

    bpy.context.scene.render.layers[0].cycles.use_denoising = False
    bpy.context.scene.render.layers[0].cycles.denoising_radius = 4
    bpy.context.scene.cycles.sampling_pattern = 'CORRELATED_MUTI_JITTER'

    bpy.context.scene.cycles.aa_samples = 1


def set_head_passes(context):
    """Enable/disable known render passes"""
    nodes = context.scene.node_tree.nodes
    for n in nodes:
        nodes.remove(n)

    rl = context.scene.render.layers['RenderLayer']

    rl.use_pass_combined = True
    rl.use_pass_z = False
    rl.use_pass_mist = False
    rl.use_pass_normal = False
    rl.use_pass_vector = False
    rl.use_pass_uv = False
    rl.use_pass_object_index = False
    rl.use_pass_material_index = False
    rl.use_pass_shadow = False
    rl.use_pass_ambient_occlusion = False


def set_head_render_settings(image_size, percent_size, tile_size):
    """Set Cycles to known good render settings"""
    bpy.data.scenes['Scene'].layers[1] = True
    bpy.data.scenes['Scene'].layers[0] = False

    set_image_size(image_size, percent_size)
    bpy.data.scenes['Scene'].cycles.film_transparent = True
    bpy.context.scene.render.tile_x = tile_size
    bpy.context.scene.render.tile_y = tile_size

    bpy.context.scene.render.layers[0].cycles.use_denoising = False
    bpy.context.scene.render.layers[0].cycles.denoising_radius = 4
    bpy.context.scene.cycles.sampling_pattern = 'CORRELATED_MUTI_JITTER'

    bpy.context.scene.cycles.max_bounces = 2
    bpy.context.scene.cycles.min_bounces = 1

    bpy.context.scene.cycles.aa_samples = 1
    bpy.context.scene.cycles.diffuse_samples = 1
    bpy.context.scene.cycles.glossy_samples = 1
    bpy.context.scene.cycles.transmission_samples = 1
    bpy.context.scene.cycles.ao_samples = 1
    bpy.context.scene.cycles.mesh_light_samples = 1
    bpy.context.scene.cycles.subsurface_samples = 1
    bpy.context.scene.cycles.volume_samples = 1

    bpy.context.scene.cycles.transparent_min_bounces = 1
    bpy.context.scene.cycles.transparent_max_bounces = 1
    bpy.context.scene.cycles.transmission_bounces = 1
    bpy.context.scene.cycles.glossy_bounces = 1
    bpy.context.scene.cycles.max_bounces = 2


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


def set_output_nodes(context, render_id, image_name, config):
    """Generate output nodes as needed"""
    full_rgb_path = os.path.join(image_name, 'rgba_comp', render_id + '_')
    bpy.context.scene.render.filepath = full_rgb_path
    layers = get_layers_and_passes(render_id)
    make_file_out_node(context, layers, image_name, config)


def get_layers_and_passes(render_id):
    layers = {}
    pass_attr_str = 'use_pass_'

    # choosing only base layer for simplicity
    l = bpy.context.scene.render.layers[0]

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

    return layers


def get_output(passout):
    # Renderlayer pass names and renderlayer node output names do not match
    # which is why we're using this dictionary to match the two
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


def new_mat_index_nodes(index, name, tree, links, output, output_node, filename):
    """Generate material index layer and link to output"""
    new_node = tree.nodes.new('CompositorNodeIDMask')
    new_node.index = index
    links.new(tree.nodes['Render Layers'].outputs[output], new_node.inputs[0])
    output_node.file_slots.new(name=name)
    output_node.file_slots[-1].path = '{}_{}'.format(name, filename)
    links.new(new_node.outputs[0], output_node.inputs[-1])


def make_mat_index_layers(config, tree, output_node):
    """Break material indices out into individual outputs"""
    for obj in config['objects']:
        new_layers = MaterialNodeGenerator(obj)
        materials = [name for name, value in obj.items() if 'render_layer' in value]
        for mat in materials:
            new_layers.connect(mat, tree, output_node)


def output_exr(tree, links, output_node, filename, render_name, out_name):
    """Export layer as EXR"""
    output_node.file_slots.new(name=out_name)
    output_node.file_slots[-1].path = filename
    output_node.file_slots[-1].use_node_format = False
    output_node.file_slots[-1].format.file_format = 'OPEN_EXR'
    links.new(tree.nodes['Render Layers'].outputs[render_name], output_node.inputs[out_name])


def make_file_out_node(context, layers, image_out, config):
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
            make_mat_index_layers(config, tree, output_node)

        # elif output == 'Image':
        #     make_image_out_nodes(links, tree, output_node, output, filename)

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
