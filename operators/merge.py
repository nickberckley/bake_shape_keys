import bpy
from ..functions.mesh import (
    set_active_shape_key,
    remember_shape_key_values,
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
        obj = bpy.context.object

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)

        # Store Values
        shape_keys = obj.data.shape_keys.key_blocks
        values = remember_shape_key_values(self, context, obj)
        active_index = shape_keys.find(obj.active_shape_key.name)
        saved_shape_key = shape_keys[active_index]
        original_name = saved_shape_key.name
        original_value = saved_shape_key.value
        min_value = saved_shape_key.slider_min
        max_value = saved_shape_key.slider_max
        original_vertex_group = saved_shape_key.vertex_group
        original_relation = saved_shape_key.relative_key

        # Restrictions
        if active_index == 0:
            self.report({'INFO'}, "Basis shape key can't be merged with anything")
            return {'CANCELLED'}

        if active_index == len(shape_keys) - 1 and self.direction == "DOWN":
            self.report({'INFO'}, "Nothing below to merge with")
            return {'CANCELLED'}

        if active_index != -1:
            # Select Top Shape Keys
            shape_keys_above = []
            for i in range(active_index + 1, len(shape_keys)):
                if shape_keys[i].name != shape_keys[0].name:
                    shape_keys_above.append(shape_keys[i])
            
            # Select Bottom Shape keys
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
            bpy.ops.object.shape_key_add(from_mix=True)
            bpy.context.object.active_shape_key.name = original_name + ".merged"
            merged_shape_key = bpy.context.object.active_shape_key
            bpy.ops.object.shape_key_move(type='TOP')

        # Merge Down
        elif self.direction == "DOWN":
            for shape_key in shape_keys_below:
                shape_key.value = 0.0
            for shape_key in shape_keys_above:
                shape_key.mute = False
                shape_key.value = 1.0
            bpy.ops.object.shape_key_add(from_mix=True)
            bpy.context.object.active_shape_key.name = original_name + ".merged"
            merged_shape_key = bpy.context.object.active_shape_key

        merged_shape_key.slider_min = min_value
        merged_shape_key.slider_max = max_value
        merged_shape_key.vertex_group = original_vertex_group
        merged_shape_key.relative_key = original_relation

        # Paste Keyframes from Original Shape Key
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{original_name}"].value':
                    original_fcurve = fcurve
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        value = keyframe.co[1]
                        
                        merged_shape_key.value = value
                        merged_shape_key.keyframe_insert(data_path="value", frame=frame)

            # Paste Interpolation from Original Keyframes
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{merged_shape_key.name}"].value':
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
    
        # Remove Shape Keys
        filtered_shape_keys = shape_keys_below if self.direction == "TOP" else shape_keys_above
        for shape_key in filtered_shape_keys:
            set_active_shape_key(shape_key.name)
            bpy.ops.object.shape_key_remove(all=False)
        set_active_shape_key(original_name)
        bpy.ops.object.shape_key_remove(all=False)

        for item in filtered_shape_keys:
            name = item.name
            if anim_data:
                for fcurve in anim_data.action.fcurves:
                    if fcurve.data_path == f'key_blocks["{name}"].value':
                        anim_data.action.fcurves.remove(fcurve)

        # Restore Values
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key.value = values.get(shape_key.name, 0.0)
        set_active_shape_key(merged_shape_key.name)
        bpy.context.object.active_shape_key.value = original_value

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
        obj = bpy.context.object
        mode = bpy.context.object.mode
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)

        # Store Values
        shape_keys = obj.data.shape_keys.key_blocks
        values = remember_shape_key_values(self, context, obj)
        active_index = shape_keys.find(obj.active_shape_key.name)
        saved_shape_key = shape_keys[active_index]
        original_name = saved_shape_key.name
        original_value = saved_shape_key.value
        min_value = saved_shape_key.slider_min
        max_value = saved_shape_key.slider_max
        original_vertex_group = saved_shape_key.vertex_group
        original_relation = saved_shape_key.relative_key

        # Restrictions
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
            saved_shape_key.value = 1.0
            above_shape_key.value = 1.0
            saved_shape_key.mute = False
            above_shape_key.mute = False

        # Merge Down
        elif self.direction == "DOWN":
            saved_shape_key.value = 1.0
            below_shape_key.value = 1.0
            saved_shape_key.mute = False
            below_shape_key.mute = False
        for shape_key in filtered_shape_keys:
            shape_key.value = 0.0

        bpy.ops.object.shape_key_add(from_mix=True)
        bpy.context.object.active_shape_key.name = original_name + ".merged"
        merged_shape_key = bpy.context.object.active_shape_key
        merged_shape_key.slider_min = min_value
        merged_shape_key.slider_max = max_value
        merged_shape_key.vertex_group = original_vertex_group
        merged_shape_key.relative_key = original_relation

        # Paste Keyframes from Original Shape Key
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{original_name}"].value':
                    original_fcurve = fcurve
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        value = keyframe.co[1]
                        
                        merged_shape_key.value = value
                        merged_shape_key.keyframe_insert(data_path="value", frame=frame)

            # Paste Interpolation from Original Keyframes
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{merged_shape_key.name}"].value':
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

        # Remove Shape Keys
        set_active_shape_key(original_name)
        bpy.ops.object.shape_key_remove(all=False)
        if self.direction == "TOP":
            set_active_shape_key(above_shape_key.name)
            bpy.ops.object.shape_key_remove(all=False)
            if anim_data:
                for fcurve in anim_data.action.fcurves:
                    if fcurve.data_path in [f'key_blocks["{original_name}"].value', f'key_blocks["{above_shape_key.name}"].value']:
                        anim_data.action.fcurves.remove(fcurve)

        elif self.direction == "DOWN":
            set_active_shape_key(below_shape_key.name)
            bpy.ops.object.shape_key_remove(all=False)
            if anim_data:
                for fcurve in anim_data.action.fcurves:
                    if fcurve.data_path in [f'key_blocks["{original_name}"].value', f'key_blocks["{below_shape_key.name}"].value']:
                        anim_data.action.fcurves.remove(fcurve)

        # Restore Values
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key.value = values.get(shape_key.name, 0.0)
        set_active_shape_key(merged_shape_key.name)
        bpy.context.object.active_shape_key.value = original_value

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
