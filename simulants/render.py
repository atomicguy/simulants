import os
import bpy


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
    bpy.data.scenes['Scene'].layers[1] = False
    bpy.data.scenes['Scene'].layers[0] = True

    bpy.data.scenes['Scene'].cycles.film_transparent = False
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


def set_head_render_settings(percent_size, tile_size):
    """Set Cycles to known good render settings"""
    bpy.data.scenes['Scene'].layers[1] = True
    bpy.data.scenes['Scene'].layers[0] = False
    bpy.data.scenes['Scene'].cycles.film_transparent = True
    bpy.data.scenes['Scene'].render.resolution_percentage = percent_size
    bpy.context.scene.render.tile_x = tile_size
    bpy.context.scene.render.tile_y = tile_size

    bpy.context.scene.render.layers[0].cycles.use_denoising = False
    bpy.context.scene.render.layers[0].cycles.denoising_radius = 4
    bpy.context.scene.cycles.sampling_pattern = 'CORRELATED_MUTI_JITTER'

    bpy.context.scene.cycles.aa_samples = 1