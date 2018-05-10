import bpy
import math


def link_nodes(node_group, from_node, out_port, to_node, in_port):
    """Link two nodes together

    :param node_group: group in which both nodes are found (i.e. materials)
    :param from_node: source node
    :param out_port: port on source node
    :param to_node: target node
    :param in_port: port on target node
    """
    links = node_group.node_tree.links
    links.new(from_node.outputs[out_port], to_node.inputs[in_port])


def rotate_env_tex(angle):
    world = [world for world in bpy.data.worlds][0]
    node_tree = world.node_tree
    tex_coord = node_tree.nodes.new(type='ShaderNodeTexCoord')
    mapping = node_tree.nodes.new(type='ShaderNodeMapping')
    mapping.vector_type = 'POINT'
    link_nodes(world, tex_coord, 'Generated', mapping, 'Vector')
    mapping.rotation[2] = math.radians(angle)
    env_tex = node_tree.nodes.get('ENVIRONMENT')
    link_nodes(world, mapping, 'Vector', env_tex, 'Vector')
