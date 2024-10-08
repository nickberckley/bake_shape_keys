bl_info = {
    "name": "Bake Shape Keys",
    "description": "Feature-set for shape keys and shape key animations",
    "author": "Nika Kutsniashvili (nickberckley)",
    "version": (1, 3),
    "blender": (4, 2, 0),
    "doc_url": "https://extensions.blender.org/add-ons/bake-shape-keys/", 
    "tracker_url": "https://github.com/nickberckley/bake_shape_keys/issues/new",
    "location": "Object > Animation menu in Object Mode",
    "category": "Animation",
}

import bpy

from . import ui
from .operators import register as operators_register, unregister as operators_unregister


##### ---------------------------------- REGISTERING ---------------------------------- #####

modules = [
    ui,
]

def register():
    for module in modules:
        module.register()

    operators_register()


def unregister():
    for module in reversed(modules):
        module.unregister()

    operators_unregister()
