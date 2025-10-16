import bpy

from ..functions.animation import (
    transfer_animation,
)
from ..functions.mesh import (
    store_active_shape_key,
    set_shape_key_values,
    duplicate_shape_key,
    reposition_shape_key,
)
from ..functions.poll import (
    shape_key_poll,
)


##### ---------------------------------- OPERATORS ---------------------------------- #####

class OBJECT_OT_shape_key_duplicate(bpy.types.Operator):
    bl_idname = "object.shape_key_duplicate"
    bl_label = "Duplicate Shape Key (with Animation)"
    bl_description = "Make a duplicated copy of an active shape key with its animation & drivers"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return shape_key_poll(context)

    def execute(self, context):
        obj = context.object
        shape_keys = obj.data.shape_keys
        active_index = obj.active_shape_key_index
        mode = obj.mode

        if active_index == 0:
            self.report({'INFO'}, "Basis shape key can't be duplicated")
            return {'CANCELLED'}

        # Get the active shape key and its properties
        original_shape_key, sk_properties = store_active_shape_key(obj)

        # Duplicate shape key and transfer properties & animation
        dupe_shape_key = duplicate_shape_key(obj)
        set_shape_key_values(dupe_shape_key, sk_properties)
        transfer_animation(shape_keys, original_shape_key, dupe_shape_key)

        # Move the shape key to the correct position in the UI
        reposition_shape_key(obj, shape_keys, active_index, dupe_shape_key, mode=mode)

        return {'FINISHED'}



##### ---------------------------------- REGISTERING ---------------------------------- #####

classes = [
    OBJECT_OT_shape_key_duplicate,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
