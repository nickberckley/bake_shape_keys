import bpy
from ..functions.animation import (
    transfer_animation,
)
from ..functions.mesh import (
    set_active_shape_key,
    store_shape_keys,
    store_active_shape_key,
    set_shape_key_values,
)


##### ---------------------------------- OPERATORS ---------------------------------- #####

class MESH_OT_shape_key_merge_all(bpy.types.Operator):
    bl_idname = "mesh.shape_key_merge_all"
    bl_label = "Merge Shape Keys (All the Way)"
    bl_description = ("Merge active shape key with all other shape keys above or below it.\n"
                    "WARNING: If shape key values are animated, merged shape key will inherit the animation from active shape key.\n"
                    "Rest of the animation will be lost, as well as other properties from merged shape keys\n")
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.active_object.data.shape_keys is not None

    def execute(self, context):
        obj = context.object

        # Store Values
        shape_keys, active_index, values = store_shape_keys(obj)
        (original_shape_key, original_name, original_value, original_min, original_max,
                                original_vertex_group, original_relation) = store_active_shape_key(obj)

        if active_index == 0:
            self.report({'INFO'}, "Basis shape key can't be merged with anything")
            return {'CANCELLED'}

        if active_index == len(shape_keys) - 1 and self.direction == "DOWN":
            self.report({'INFO'}, "Nothing below to merge with")
            return {'CANCELLED'}


        if active_index != -1:
            # select_shape_keys_above
            shape_keys_above = []
            for i in range(active_index + 1, len(shape_keys)):
                if shape_keys[i].name != shape_keys[0].name:
                    shape_keys_above.append(shape_keys[i])

            # select_shape_keys_below
            shape_keys_below = []
            for i in range(active_index - 1, -1, -1):
                if shape_keys[i].name != shape_keys[0].name:
                    shape_keys_below.append(shape_keys[i])

        # Merge Up
        if self.direction == "TOP":
            for shape_key in shape_keys_above:
                shape_key.value = 0.0
            for shape_key in shape_keys_below:
                shape_key.mute = False
                shape_key.value = 1.0
            merged_shape_key = obj.shape_key_add(from_mix=True)
            set_active_shape_key(merged_shape_key.name)
            bpy.ops.object.shape_key_move(type='TOP')

        # Merge Down
        elif self.direction == "DOWN":
            for shape_key in shape_keys_below:
                shape_key.value = 0.0
            for shape_key in shape_keys_above:
                shape_key.mute = False
                shape_key.value = 1.0
            merged_shape_key = obj.shape_key_add(from_mix=True)

        set_shape_key_values(merged_shape_key, original_name + ".merged", original_value, original_min, original_max,
                            original_vertex_group, original_relation)

        # Transfer Animation
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            transfer_animation(anim_data, original_name, merged_shape_key)


        # Remove Shape Keys
        filtered_shape_keys = shape_keys_below if self.direction == "TOP" else shape_keys_above
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

        set_active_shape_key(merged_shape_key.name)
        return {'FINISHED'}


class MESH_OT_shape_key_merge(bpy.types.Operator):
    bl_idname = "mesh.shape_key_merge"
    bl_label = "Merge Shape Keys"
    bl_description = ("Merge active shape key with shape key above or below it.\n"
                    "WARNING: If shape key values are animated, merged shape key will inherit the animation from active shape key.\n"
                    "Rest of the animation will be lost, as well as other properties from merged shape keys\n")
    bl_options = {'REGISTER', 'UNDO'}
    
    direction: bpy.props.StringProperty(
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.active_object.data.shape_keys is not None

    def execute(self, context):
        obj = context.object
        mode = context.object.mode

        # Store Values
        shape_keys, active_index, values = store_shape_keys(obj)
        (original_shape_key, original_name, original_value, original_min, original_max,
                                original_vertex_group, original_relation) = store_active_shape_key(obj)

        if active_index == 0:
            self.report({'INFO'}, "Basis shape key can't be merged with anything")
            return {'CANCELLED'}

        if active_index == len(shape_keys) - 1 and self.direction == "DOWN":
            self.report({'INFO'}, "Nothing below to merge with")
            return {'CANCELLED'}


        # Select Shape Keys
        above_index = active_index - 1
        above_shape_key = shape_keys[above_index]
        below_index = active_index + 1
        below_shape_key = shape_keys[below_index] if not active_index == len(shape_keys) - 1 else None

        filtered_shape_keys = []
        for i, shape_key in enumerate(shape_keys):
            if self.direction == "TOP":
                if i != active_index and i != above_index:
                    filtered_shape_keys.append(shape_key)
            elif self.direction == "DOWN":
                if i != active_index and i != below_index:
                    filtered_shape_keys.append(shape_key)
    
        # Merge Up
        if self.direction == "TOP":
            original_shape_key.value = 1.0
            above_shape_key.value = 1.0
            original_shape_key.mute = False
            above_shape_key.mute = False

        # Merge Down
        elif self.direction == "DOWN":
            original_shape_key.value = 1.0
            below_shape_key.value = 1.0
            original_shape_key.mute = False
            below_shape_key.mute = False
        for shape_key in filtered_shape_keys:
            shape_key.value = 0.0

        merged_shape_key = obj.shape_key_add(from_mix=True)
        set_shape_key_values(merged_shape_key, original_name + ".merged", original_value, original_min, original_max,
                            original_vertex_group, original_relation)

        # Transfer Animation
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            transfer_animation(anim_data, original_name, merged_shape_key)


        # Remove Shape Keys
        obj.shape_key_remove(original_shape_key)
        if self.direction == "TOP":
            if anim_data:
                for fcurve in anim_data.action.fcurves:
                    if fcurve.data_path in [f'key_blocks["{original_name}"].value', f'key_blocks["{above_shape_key.name}"].value']:
                        anim_data.action.fcurves.remove(fcurve)
            obj.shape_key_remove(above_shape_key)

        elif self.direction == "DOWN":
            if anim_data:
                for fcurve in anim_data.action.fcurves:
                    if fcurve.data_path in [f'key_blocks["{original_name}"].value', f'key_blocks["{below_shape_key.name}"].value']:
                        anim_data.action.fcurves.remove(fcurve)
            obj.shape_key_remove(below_shape_key)

        # Restore Values
        for shape_key in shape_keys:
            shape_key.value = values.get(shape_key.name, 0.0)
        merged_shape_key.value = original_value
        set_active_shape_key(merged_shape_key.name)

        # Move Shape Keys to Correct Position in UI
        bpy.ops.object.mode_set(mode='OBJECT')
        if self.direction == "TOP":
            new_index = (len(obj.data.shape_keys.key_blocks) - active_index)
            for _ in range(new_index):
                bpy.ops.object.shape_key_move(type='UP')
        elif self.direction == "DOWN":
            new_index = (len(obj.data.shape_keys.key_blocks) - active_index) - 1
            for _ in range(new_index):
                bpy.ops.object.shape_key_move(type='UP')

        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}



##### ---------------------------------- REGISTERING ---------------------------------- #####

classes = [
    MESH_OT_shape_key_merge_all,
    MESH_OT_shape_key_merge,
]

def register():
    for cls in classes :
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes) :
        bpy.utils.unregister_class(cls)
