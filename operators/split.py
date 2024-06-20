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
        obj = bpy.context.object
        if not any(v.select for v in obj.data.vertices):
            self.report({'INFO'}, "Nothing is selected in edit mode")
            return {'CANCELLED'}

        if obj.data.shape_keys.key_blocks.find(obj.active_shape_key.name) == 0:
            self.report({'INFO'}, "Basis shape key can't be split")
            return {'CANCELLED'}

        mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.active_object.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')

        # Create Vertex Groups 
        vertex_group_l = obj.vertex_groups.new(name="split_shape_key_left")
        selected_vertices = [v.index for v in obj.data.vertices if v.select]
        for vertex in selected_vertices:
            bpy.ops.object.vertex_group_assign()

        bpy.ops.mesh.select_all(action='INVERT')
        vertex_group_r = obj.vertex_groups.new(name="split_shape_key_right")
        selected_vertices = [v.index for v in obj.data.vertices if v.select]
        for vertex in selected_vertices:
            bpy.ops.object.vertex_group_assign()

        # Store Values
        shape_keys, active_index, values = store_shape_keys(obj)
        (original_shape_key, original_name, original_value, original_min, original_max,
                                original_vertex_group, original_relation) = store_active_shape_key(obj)

        bpy.ops.object.mode_set(mode='OBJECT')

        # Create Left Version
        bpy.ops.object.shape_key_clear()
        original_shape_key.vertex_group = 'split_shape_key_left'
        original_shape_key.value = 1.0

        bpy.ops.object.shape_key_add(from_mix=True)
        left_shape_key = bpy.context.object.active_shape_key
        set_shape_key_values(left_shape_key, original_name + ".split_001", original_value, original_min, original_max,
                            original_vertex_group, original_relation)

        # Create Right Version
        bpy.ops.object.shape_key_clear()
        original_shape_key.vertex_group = 'split_shape_key_right'
        original_shape_key.value = 1.0

        bpy.ops.object.shape_key_add(from_mix=True)
        right_shape_key = bpy.context.object.active_shape_key
        set_shape_key_values(right_shape_key, original_name + ".split_002", original_value, original_min, original_max,
                            original_vertex_group, original_relation)


        # Paste Keyframes from Original Shape Key
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            transfer_animation(anim_data, original_name, left_shape_key, right_shape_key)

        # Remove Original Shape Key
        set_active_shape_key(original_name)
        bpy.ops.object.shape_key_remove(all=False)
        if anim_data:
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{original_name}"].value':
                    anim_data.action.fcurves.remove(fcurve)
                    break

        # Remove Vertex Groups
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group="split_shape_key_left")
        bpy.ops.object.vertex_group_remove()
        bpy.ops.object.vertex_group_set_active(group="split_shape_key_right")
        bpy.ops.object.vertex_group_remove()
        bpy.ops.mesh.select_all(action='DESELECT')

        # Restore Values
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key.value = values.get(shape_key.name, 0.0)
        obj.data.shape_keys.key_blocks[left_shape_key.name].value = original_value
        obj.data.shape_keys.key_blocks[right_shape_key.name].value = original_value

        # Move Shape Keys to Correct Position in UI
        new_index = (len(obj.data.shape_keys.key_blocks) - active_index) - 2
        bpy.ops.object.mode_set(mode='OBJECT')
        for _ in range(new_index):
            set_active_shape_key(left_shape_key.name)
            bpy.ops.object.shape_key_move(type='UP')
            set_active_shape_key(right_shape_key.name)
            bpy.ops.object.shape_key_move(type='UP')

        bpy.ops.object.mode_set(mode=mode)
        set_active_shape_key(left_shape_key.name)
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
