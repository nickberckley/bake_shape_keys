import bpy
from ..functions.mesh import (
    set_active_shape_key,
    store_shape_keys,
    store_active_shape_key,
    set_shape_key_values,
)


##### ---------------------------------- OPERATORS ---------------------------------- #####

class MESH_OT_shape_key_duplicate(bpy.types.Operator):
    bl_idname = "mesh.shape_key_uplicate"
    bl_label = "Duplicate Shape Key"
    bl_description = "Make a duplicated copy of an active shape key"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.active_object.data.shape_keys is not None

    def execute(self, context):
        obj = context.object
        mode = context.object.mode

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)

        # Store Values
        shape_keys, active_index, values = store_shape_keys(obj)
        (__, original_name, original_value, original_min, original_max,
                                original_vertex_group, original_relation) = store_active_shape_key(obj)

        if active_index == 0:
            self.report({'INFO'}, "This operation can't be performed on basis shape key")
            return {'CANCELLED'}

        # New Shape Key from Mix
        for shape_key in shape_keys:
            shape_key.value = 0.0
        obj.active_shape_key.value = 1.0

        bpy.ops.object.shape_key_add(from_mix=True)
        dupe_shape_key = obj.active_shape_key
        set_shape_key_values(dupe_shape_key, original_name, original_value, original_min, original_max,
                            original_vertex_group, original_relation)

        # Paste Keyframes from Original Shape Key
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{original_name}"].value':
                    original_fcurve = fcurve
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        value = keyframe.co[1]
                        
                        dupe_shape_key.value = value
                        dupe_shape_key.keyframe_insert(data_path="value", frame=frame)

            # Paste Interpolation from Original Keyframes
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{dupe_shape_key.name}"].value':
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        for orig_keyframe in original_fcurve.keyframe_points:
                            if int(orig_keyframe.co[0]) == frame:
                                keyframe.interpolation = orig_keyframe.interpolation
                                keyframe.easing = orig_keyframe.easing
                                keyframe.handle_left_type = orig_keyframe.handle_left_type
                                keyframe.handle_right_type = orig_keyframe.handle_right_type
                                keyframe.handle_left = orig_keyframe.handle_left
                                keyframe.handle_right = orig_keyframe.handle_right
                                break

        # Restore Values
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key.value = values.get(shape_key.name, 0.0)

        # Move Shape Keys to Correct Position in UI
        new_index = (len(obj.data.shape_keys.key_blocks) - active_index) - 2
        bpy.ops.object.mode_set(mode='OBJECT')
        for _ in range(new_index):
            set_active_shape_key(dupe_shape_key.name)
            bpy.ops.object.shape_key_move(type='UP')

        bpy.ops.object.mode_set(mode=mode)
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
