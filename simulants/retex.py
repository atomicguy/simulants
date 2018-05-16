from __future__ import absolute_import

import bpy
import math
import os
import random
import sys

cwd = os.path.dirname(os.path.abspath(__file__))
sys.path.append(cwd)

import node

def use_texture(material, texture):
    mat_nodes = material.node_tree.nodes
    output = mat_nodes.get('Material Output')
    shader = mat_nodes.new(type='ShaderNodeBsdfDiffuse')

    if texture is None:
        ten_percent_gray = (0.9, 0.9, 0.9, 1)
        shader.inputs['Color'].default_value = ten_percent_gray
    else:
        image = bpy.data.images.load(texture)
        image_tex = mat_nodes.new(type='ShaderNodeTexImage')
        image_tex.image = image
        node.link(material, image_tex, 'Color', shader, 'Color')

    node.link(material, shader, 'BSDF', output, 'Surface')


def noise_wrinkle(material, texture):
    # Make noise wrinkles
    mat_nodes = material.node_tree.nodes
    output = mat_nodes.get('Material Output')

    noise_tex = mat_nodes.new(type='ShaderNodeTexNoise')
    noise_values = {'Scale': 5.0, 'Detail': 2, 'Distortion': 3.6}
    node.set_values(noise_tex, noise_values)

    # Link wrinkles to displacement
    node.link(material, noise_tex, 'Fac', output, 'Displacement')

    # Add texture
    use_texture(material, texture)


def wave_wrinkle(material, texture):
    # Wrinkles based on a wave pattern
    mat_nodes = material.node_tree.nodes
    output = mat_nodes.get('Material Output')

    # Enable control of wave rotation on surface
    tex_coord = mat_nodes.new(type='ShaderNodeTexCoord')
    mapping = mat_nodes.new(type='ShaderNodeMapping')
    mapping.vector_type = 'TEXTURE'
    node.link(material, tex_coord, 'UV', mapping, 'Vector')

    # Randomize rotation
    rotation = math.radians(random.uniform(0, 180))
    mapping.rotation[1] = rotation

    wave_tex = mat_nodes.new(type='ShaderNodeTexWave')
    wave_vals = {'Scale': 30, 'Distortion': 1.1, 'Detail': 2, 'Detail Scale': 1}
    node.set_values(wave_tex, wave_vals)
    node.link(material, mapping, 'Vector', wave_tex, 'Vector')

    noise_tex = mat_nodes.new(type='ShaderNodeTexNoise')

    # Randomize wave supression scale
    scale = random.uniform(2.0, 10.0)

    noise_vals = {'Scale': scale, 'Detail': 2, 'Distortion': 1.5}
    node.set_values(noise_tex, noise_vals)
    node.link(material, noise_tex, 'Fac', wave_tex, 'Scale')

    node.link(material, wave_tex, 'Fac', output, 'Displacement')

    # Use texture
    use_texture(material, texture)


def magic_wrinkle(material, texture):
    # Wrinkles based on Magic Texture
    mat_nodes = material.node_tree.nodes
    output = mat_nodes.get('Material Output')

    noise_tex = mat_nodes.new(type='ShaderNodeTexNoise')
    noise_vals = {'Scale': 5, 'Detail': 2, 'Distortion': 0}
    node.set_values(noise_tex, noise_vals)

    voronoi_tex = mat_nodes.new(type='ShaderNodeTexVoronoi')
    node.link(material, noise_tex, 'Fac', voronoi_tex, 'Scale')

    mult_node = mat_nodes.new(type='ShaderNodeMath')
    mult_node.operation = 'MULTIPLY'
    node.link(material, voronoi_tex, 'Fac', mult_node, 0)
    node.link(material, noise_tex, 'Fac', mult_node, 1)

    magic_tex = mat_nodes.new(type='ShaderNodeTexMagic')
    magic_tex.turbulence_depth = random.choice([1, 2, 3])
    magic_vals = {'Distortion': 13}
    node.set_values(magic_tex, magic_vals)
    node.link(material, mult_node, 'Value', magic_tex, 'Scale')

    musgrave_tex = mat_nodes.new(type='ShaderNodeTexMusgrave')
    musgrave_vals = {'Scale': 10.9, 'Detail': 2, 'Dimension': 2, 'Lacunarity': 1, 'Offset': 0, 'Gain': 1}
    node.set_values(musgrave_tex, musgrave_vals)

    mult_2_node = mat_nodes.new(type='ShaderNodeMath')
    mult_2_node.operation = 'MULTIPLY'
    node.link(material, magic_tex, 'Fac', mult_2_node, 0)
    node.link(material, musgrave_tex, 'Fac', mult_2_node, 1)

    node.link(material, mult_2_node, 'Value', output, 'Displacement')

    # Add texture
    use_texture(material, texture)


def new_texture(material, texture):
    "adds no wrinkles; placeholder"
    use_texture(material, texture)


def recolor_simulant(hue, saturation, value):
    skin = node.material('MBlab_human_skin')
    skin_sat = skin.node_tree.nodes.get('skin_saturation')
    skin_hue = skin.node_tree.nodes.get('skin_hue')
    skin_val = skin.node_tree.nodes.get('skin_value')

    skin_sat.outputs[0].default_value = saturation
    skin_hue.outputs[0].default_value = hue
    skin_val.outputs[0].default_value = value


def recolor_hair(new_color):
    hair = node.material('hair')
    image_tex = hair.node_tree.nodes.get('Image Texture')
    shader = hair.node_tree.nodes.get('Diffuse BSDF')

    mix = hair.node_tree.nodes.new(type='ShaderNodeMixRGB')
    mix.blend_type = 'SCREEN'
    mix.inputs['Color2'].default_value = new_color

    node.link(hair, image_tex, 'Color', mix, 'Color1')
    node.link(hair, mix, 'Color', shader, 'Color')