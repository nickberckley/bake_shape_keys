if "bpy" in locals():
    import importlib
    for mod in [bake,
                copy,
                duplicate,
                merge,
                objects,
                split,
                ]:
        importlib.reload(mod)
else:
    import bpy
    from . import (
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
