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

class MESH_OT_shape_key_split(bpy.types.Operator):
    bl_idname = "mesh.shape_key_split"
    bl_label = "Split Shape Key"
    bl_description = "Split active shape key into two parts based on edit mode selection"
    bl_options = {'REGISTER', 'UNDO'}

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
            self.report({'INFO'}, "Basis shape key can't be split")
            return {'CANCELLED'}

        if not any(v.select for v in obj.data.vertices):
            self.report({'INFO'}, "Nothing is selected in edit mode")
            return {'CANCELLED'}

        # Create Vertex Groups
        bpy.ops.object.mode_set(mode='OBJECT')

        vertices_left = [v.index for v in obj.data.vertices if v.select == True]
        group_left = obj.vertex_groups.new(name="shape_key_split_left")
        group_left.add(vertices_left, weight=1, type='ADD')

        vertices_right = [v.index for v in obj.data.vertices if v.select == False]
        group_right = obj.vertex_groups.new(name="shape_key_split_right")
        group_right.add(vertices_right, weight=1, type='ADD')

        # create_left_key
        for shape_key in shape_keys:
            shape_key.value = 0.0
        original_shape_key.vertex_group = 'shape_key_split_left'
        original_shape_key.value = 1.0

        left_shape_key = obj.shape_key_add(from_mix=True)
        set_shape_key_values(left_shape_key, original_name + ".split_001", original_value, original_min, original_max,
                            original_vertex_group, original_relation)

        # create_right_key
        left_shape_key.value = 0.0
        original_shape_key.vertex_group = 'shape_key_split_right'
        original_shape_key.value = 1.0

        right_shape_key = obj.shape_key_add(from_mix=True)
        set_shape_key_values(right_shape_key, original_name + ".split_002", original_value, original_min, original_max,
                            original_vertex_group, original_relation)

        # Transfer Animation
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            transfer_animation(anim_data, original_name, left_shape_key, right_shape_key)


        # Remove Original Shape Key
        obj.shape_key_remove(original_shape_key)
        if anim_data:
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{original_name}"].value':
                    anim_data.action.fcurves.remove(fcurve)
                    break

        # Remove Vertex Groups
        obj.vertex_groups.remove(group_left)
        obj.vertex_groups.remove(group_right)

        # Restore Values
        for shape_key in shape_keys:
            shape_key.value = values.get(shape_key.name, 0.0)
        left_shape_key.value = original_value
        right_shape_key.value = original_value

        # Move Shape Keys to Correct Position in UI
        new_index = (len(shape_keys) - active_index) - 2
        for _ in range(new_index):
            set_active_shape_key(left_shape_key.name)
            bpy.ops.object.shape_key_move(type='UP')
            set_active_shape_key(right_shape_key.name)
            bpy.ops.object.shape_key_move(type='UP')

        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}



##### ---------------------------------- REGISTERING ---------------------------------- #####

classes = [
    MESH_OT_shape_key_split,
]

def register():
    for cls in classes :
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes) :
        bpy.utils.unregister_class(cls)
