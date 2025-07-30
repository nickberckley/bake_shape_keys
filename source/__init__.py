if "bpy" in locals():
    import importlib
    for mod in [operators,
                ui,
                ]:
        importlib.reload(mod)
    print("Add-on Reloaded: Bake Shape Keys")
else:
    import bpy
    from . import (
        operators,
        ui,
    )


##### ---------------------------------- REGISTERING ---------------------------------- #####

modules = [
    operators,
    ui,
]

def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
