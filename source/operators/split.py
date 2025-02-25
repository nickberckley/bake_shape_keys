import bpy

from ..functions.animation import (
    transfer_animation,
)
from ..functions.mesh import (
    store_active_shape_key,
    set_shape_key_values,
    duplicate_shape_key,
    remove_shape_key,
    reposition_shape_key,
)
from ..functions.poll import (
    shape_key_poll,
)


##### ---------------------------------- OPERATORS ---------------------------------- #####

class OBJECT_OT_shape_key_split(bpy.types.Operator):
    bl_idname = "object.shape_key_split"
    bl_label = "Split Shape Key"
    bl_description = "Split active shape key into two parts based on edit mode selection"
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
            self.report({'INFO'}, "Basis shape key can't be split")
            return {'CANCELLED'}

        if not any(v.select for v in obj.data.vertices):
            self.report({'INFO'}, "Nothing is selected in edit mode")
            return {'CANCELLED'}

        if mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # store_values
        original_shape_key, sk_properties = store_active_shape_key(obj)


        # Create Vertex Groups
        verts_left = []
        verts_right = []
        for vert in obj.data.vertices:
            if vert.select == True:
                verts_left.append(vert.index)
            else:
                verts_right.append(vert.index)

        group_left = obj.vertex_groups.new(name="shape_key_split_left")
        group_left.add(verts_left, weight=1, type='ADD')

        group_right = obj.vertex_groups.new(name="shape_key_split_right")
        group_right.add(verts_right, weight=1, type='ADD')


        # Add Left Shape Key
        original_shape_key.vertex_group = "shape_key_split_left"
        left_shape_key = duplicate_shape_key(obj)
        set_shape_key_values(left_shape_key, sk_properties, name=sk_properties["name"] + ".split_001")
        obj.vertex_groups.remove(group_left)

        # Add Right Shape Key
        original_shape_key.vertex_group = 'shape_key_split_right'
        right_shape_key = duplicate_shape_key(obj)
        set_shape_key_values(right_shape_key, sk_properties, name=sk_properties["name"] + ".split_002")
        obj.vertex_groups.remove(group_right)

        # Transfer Animation
        transfer_animation(shape_keys, original_shape_key, left_shape_key, right_shape_key)

        # Move Shape Keys to the Correct Position
        reposition_shape_key(obj, shape_keys, active_index, left_shape_key, right_shape_key, mode=mode)

        # Remove Original Shape Key
        remove_shape_key(obj, original_shape_key)

        return {'FINISHED'}



##### ---------------------------------- REGISTERING ---------------------------------- #####

classes = [
    OBJECT_OT_shape_key_split,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
