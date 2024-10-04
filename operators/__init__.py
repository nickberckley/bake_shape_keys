import bpy

from . import(
    bake,
    copy,
    duplicate,
    merge,
    objects,
    split,
)

#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    bake,
    copy,
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
