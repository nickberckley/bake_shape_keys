bl_info = {
    "name": "Bake Shape Keys",
    "description": "Shape Key Operations for Stop-Motion Animation",
    "author": "Nika Kutsniashvili (nickberckley)",
    "version": (1, 1),
    "blender": (3, 5, 0),
    "doc_url": "https://blendermarket.com/products/bake-shape-keys", 
    "tracker_url": "https://blenderartists.org/t/bake-shape-keys-stop-motion-and-3d-printing-add-on/1458920",
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
