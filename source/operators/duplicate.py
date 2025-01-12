import bpy
from ..functions.animation import (
    transfer_animation,
)
from ..functions.mesh import (
    store_active_shape_key,
    set_shape_key_values,
    reposition_shape_key,
)
from ..functions.poll import (
    shape_key_poll,
)


##### ---------------------------------- OPERATORS ---------------------------------- #####

class OBJECT_OT_shape_key_duplicate(bpy.types.Operator):
    bl_idname = "object.shape_key_duplicate"
    bl_label = "Duplicate Shape Key"
    bl_description = "Make a duplicated copy of an active shape key"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return shape_key_poll(context)

    def execute(self, context):
        obj = context.object
        shape_keys = obj.data.shape_keys.key_blocks
        active_sk = obj.active_shape_key_index
        mode = context.object.mode

        if active_sk == 0:
            self.report({'INFO'}, "Basis shape key can't be duplicated")
            return {'CANCELLED'}

        # store_values
        original_shape_key, sk_properties = store_active_shape_key(obj)


        # New Shape Key from Mix
        obj.show_only_shape_key = True
        dupe_shape_key = obj.shape_key_add(from_mix=True)
        set_shape_key_values(dupe_shape_key, sk_properties)

        # Transfer Animation
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            transfer_animation(anim_data, sk_properties["name"], dupe_shape_key)

        # Move Shape Key to the Correct Position
        reposition_shape_key(obj, shape_keys, active_sk, mode, dupe_shape_key)


        # restore_properties
        obj.show_only_shape_key = False

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
