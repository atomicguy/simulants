from __future__ import absolute_import, division, print_function

import bpy
import sys

from simulants.output_redirect import OutputRedirect


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