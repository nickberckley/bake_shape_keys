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

class OBJECT_OT_shape_key_merge_all(bpy.types.Operator):
    bl_idname = "object.shape_key_merge_all"
    bl_label = "Merge Shape Keys (All the Way)"
    bl_description = ("Merge active shape key with all other shape keys above or below it.\n"
                    "WARNING: If shape key values are animated, merged shape key will inherit the animation from active shape key.\n"
                    "Rest of the animation will be lost, as well as other properties from merged shape keys\n")
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return shape_key_poll(context)

    def execute(self, context):
        obj = context.object
        mode = context.object.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Store Values
        shape_keys, active_index, values = store_shape_keys(obj)
        (original_shape_key, original_name, original_value, original_min, original_max,
                            original_vertex_group, original_relation, original_mute) = store_active_shape_key(obj)

        if (active_index == 0) or (active_index == 1 and self.direction == "TOP"):
            self.report({'INFO'}, "Basis shape key can't be merged with anything")
            return {'CANCELLED'}

        if active_index == len(shape_keys) - 1 and self.direction == "DOWN":
            self.report({'INFO'}, "Nothing below to merge with")
            return {'CANCELLED'}

        # filter_shape_keys
        shape_keys_above = []
        shape_keys_below = []
        for i, key in enumerate(shape_keys):
            if i == active_index or i == 0:
                continue
            if i < active_index:
                shape_keys_above.append(key)
            else:
                shape_keys_below.append(key)

        if original_shape_key.mute == True:
            original_shape_key.mute = False

        # Merge Up
        if self.direction == "TOP":
            for shape_key in shape_keys_below:
                shape_key.value = 0.0

            merged_shape_key = obj.shape_key_add(from_mix=True)
            set_active_shape_key(obj, merged_shape_key.name)
            bpy.ops.object.shape_key_move(type='TOP')

        # Merge Down
        elif self.direction == "DOWN":
            for shape_key in shape_keys_above:
                shape_key.value = 0.0

            merged_shape_key = obj.shape_key_add(from_mix=True)

        set_shape_key_values(merged_shape_key, original_name + ".merged", original_value, original_min, original_max,
                            original_vertex_group, original_relation, original_mute)

        # Transfer Animation
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            transfer_animation(anim_data, original_name, merged_shape_key)


        # Remove Shape Keys
        filtered_shape_keys = shape_keys_above if self.direction == "TOP" else shape_keys_below
        filtered_shape_keys.append(original_shape_key)
        if anim_data:
            filtered_fcurves = {f'key_blocks["{shape_key.name}"].value' for shape_key in filtered_shape_keys}
            for fcurve in anim_data.action.fcurves[:]:
                if fcurve.data_path in filtered_fcurves:
                    anim_data.action.fcurves.remove(fcurve)

        for shape_key in filtered_shape_keys:
            obj.shape_key_remove(shape_key)

        # Restore Values
        for shape_key in shape_keys:
            shape_key.value = values.get(shape_key.name, 0.0)
        merged_shape_key.value = original_value

        set_active_shape_key(obj, merged_shape_key.name)
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}


class OBJECT_OT_shape_key_merge(bpy.types.Operator):
    bl_idname = "object.shape_key_merge"
    bl_label = "Merge Shape Keys"
    bl_description = ("Merge active shape key with shape key above or below it.\n"
                    "WARNING: If shape key values are animated, merged shape key will inherit the animation from active shape key.\n"
                    "Rest of the animation will be lost, as well as other properties from merged shape keys\n")
    bl_options = {'REGISTER', 'UNDO'}
    
    direction: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return shape_key_poll(context)

    def execute(self, context):
        obj = context.object
        mode = context.object.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Store Values
        shape_keys, active_index, values = store_shape_keys(obj)
        (original_shape_key, original_name, original_value, original_min, original_max,
                            original_vertex_group, original_relation, original_mute) = store_active_shape_key(obj)

        above_shape_key = shape_keys[active_index - 1]
        below_shape_key = shape_keys[active_index + 1]

        if (active_index == 0) or (active_index == 1 and self.direction == "TOP"):
            self.report({'INFO'}, "Basis shape key can't be merged with anything")
            return {'CANCELLED'}

        if active_index == len(shape_keys) - 1 and self.direction == "DOWN":
            self.report({'INFO'}, "Nothing below to merge with")
            return {'CANCELLED'}

        # New Shape Key from Mix
        for shape_key in shape_keys:
            if shape_key == original_shape_key:
                continue
            if ((self.direction == "TOP" and shape_key != above_shape_key) or
                (self.direction == "DOWN" and shape_key != below_shape_key)):
                    shape_key.value = 0.0

        if original_shape_key.mute == True:
            original_shape_key.mute = False

        merged_shape_key = obj.shape_key_add(from_mix=True)
        set_shape_key_values(merged_shape_key, original_name + ".merged", original_value, original_min, original_max,
                            original_vertex_group, original_relation, original_mute)

        # Transfer Animation
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            transfer_animation(anim_data, original_name, merged_shape_key)


        # Remove Shape Keys
        filtered_shape_keys = [original_shape_key, above_shape_key if self.direction=="TOP" else below_shape_key]
        if anim_data:
            filtered_fcurves = {f'key_blocks["{shape_key.name}"].value' for shape_key in filtered_shape_keys}
            for fcurve in anim_data.action.fcurves[:]:
                if fcurve.data_path in filtered_fcurves:
                    anim_data.action.fcurves.remove(fcurve)

        for shape_key in filtered_shape_keys:
            obj.shape_key_remove(shape_key)

        # Restore Values
        for shape_key in shape_keys:
            shape_key.value = values.get(shape_key.name, 0.0)
        merged_shape_key.value = original_value

        # Move Shape Keys to Correct Position in UI
        reposition_shape_key(obj, shape_keys, active_index, mode, merged_shape_key,
                             offset=0 if self.direction=="TOP" else 1)

        return {'FINISHED'}



##### ---------------------------------- REGISTERING ---------------------------------- #####

classes = [
    OBJECT_OT_shape_key_merge_all,
    OBJECT_OT_shape_key_merge,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
