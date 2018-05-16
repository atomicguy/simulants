import bpy
import math

def set_values(node, values):
    """Set input (defaults) to values from a dictionary

    :param node: node to set input paramaters
    :param values: dictionary of paramaters and values {'paramater': value}
    """
    for input_port, value in values.items():
        node.inputs[input_port].default_value = value


def link(node_group, from_node, out_port, to_node, in_port):
    """Link two nodes together

    :param node_group: group in which both nodes are found (i.e. materials)
    :param from_node: source node
    :param out_port: port on source node
    :param to_node: target node
    :param in_port: port on target node
    """
    links = node_group.node_tree.links
    links.new(from_node.outputs[out_port], to_node.inputs[in_port])


def material(material_name):
    """Return a specified material from a blender scene

    :param material_name: (start of) name of material to return
    :return: the specified material
    """
    materials = bpy.data.materials
    mat_list = [mat for mat in materials if mat.name.startswith(material_name)]
    assert len(mat_list) > 0, 'material {} not found'.format(material_name)

    return mat_list[0]