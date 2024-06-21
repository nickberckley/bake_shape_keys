import bpy
from ..functions.animation import (
    transfer_animation,
)
from ..functions.mesh import (
    set_active_shape_key,
    store_shape_keys,
    store_active_shape_key,
    set_shape_key_values,
    reposition_shape_key,
)
from ..functions.poll import (
    shape_key_poll,
)


##### ---------------------------------- OPERATORS ---------------------------------- #####

class MESH_OT_shape_key_duplicate(bpy.types.Operator):
    bl_idname = "mesh.shape_key_uplicate"
    bl_label = "Duplicate Shape Key"
    bl_description = "Make a duplicated copy of an active shape key"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return shape_key_poll(context)

    def execute(self, context):
        obj = context.object
        mode = context.object.mode

        # Store Values
        shape_keys, active_index, values = store_shape_keys(obj)
        (__, original_name, original_value, original_min, original_max,
                                original_vertex_group, original_relation) = store_active_shape_key(obj)

        if active_index == 0:
            self.report({'INFO'}, "Basis shape key can't be duplicated")
            return {'CANCELLED'}

        # New Shape Key from Mix
        for shape_key in shape_keys:
            shape_key.value = 0.0
        obj.active_shape_key.value = 1.0

        dupe_shape_key = obj.shape_key_add(from_mix=True)
        set_shape_key_values(dupe_shape_key, original_name, original_value, original_min, original_max,
                            original_vertex_group, original_relation)

        # Copy Animation
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            transfer_animation(anim_data, original_name, dupe_shape_key)

        # Restore Values
        for shape_key in shape_keys:
            shape_key.value = values.get(shape_key.name, 0.0)

        # Move Shape Keys to Correct Position in UI
        reposition_shape_key(shape_keys, active_index, mode, dupe_shape_key)

        return {'FINISHED'}



##### ---------------------------------- REGISTERING ---------------------------------- #####

classes = [
    MESH_OT_shape_key_duplicate,
]

def register():
    for cls in classes :
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes) :
        bpy.utils.unregister_class(cls)
