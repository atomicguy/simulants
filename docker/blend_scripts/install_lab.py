import os
import bpy

bpy.ops.preferences.addon_install(filepath='/tmp/manuelbastionilab.zip')
os.rename('/root/.config/blender/2.80/scripts/addons/MB-Lab-1.7.4b/',
          '/root/.config/blender/2.80/scripts/addons/MB-Lab-174b')
bpy.ops.preferences.addon_enable(module="MB-Lab-174b")
bpy.ops.wm.open_mainfile(filepath='/tmp/blend_scripts/base_scene.blend')
bpy.ops.wm.save_userpref()