bl_info = {
    "name": "Bake Shape Keys",
    "description": "Feature-set for shape keys and shape key animations",
    "author": "Nika Kutsniashvili (nickberckley)",
    "version": (1, 1),
    "blender": (3, 5, 0),
    "doc_url": "https://extensions.blender.org/add-ons/bake-shape-keys/", 
    "tracker_url": "https://github.com/nickberckley/bake_shape_keys/issues/new",
    "location": "Object > Animation menu in Object Mode",
    "category": "Animation",
}

import bpy

from . import ui
from .operators import (
    bake,
    duplicate,
    merge,
    objects,
    split,
)


##### ---------------------------------- REGISTERING ---------------------------------- #####

modules = [
    ui,
    bake,
    duplicate,
    merge,
    objects,
    split,
]

def register():
    for module in modules:
        module.register()

def unregister():
    for module in reversed(modules):
        module.unregister()
