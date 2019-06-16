import os
import bpy

bpy.ops.wm.addon_install(filepath='/tmp/manuelbastionilab.zip')
bpy.ops.wm.addon_enable(module="manuelbastionilab")
bpy.ops.wm.open_mainfile(filepath='/tmp/blend_scripts/base_scene.blend')
bpy.ops.wm.save_userpref()