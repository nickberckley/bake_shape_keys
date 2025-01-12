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
        shape_keys = obj.data.shape_keys.key_blocks
        active_sk = obj.active_shape_key_index
        mode = context.object.mode

        if active_sk == 0:
            self.report({'INFO'}, "Basis shape key can't be split")
            return {'CANCELLED'}

        if not any(v.select for v in obj.data.vertices):
            self.report({'INFO'}, "Nothing is selected in edit mode")
            return {'CANCELLED'}

        bpy.ops.object.mode_set(mode='OBJECT')

        # Store Values
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


        # create_left_key
        obj.show_only_shape_key = True
        original_shape_key.vertex_group = "shape_key_split_left"
        left_shape_key = obj.shape_key_add(from_mix=True)
        set_shape_key_values(left_shape_key, sk_properties, name=sk_properties["name"] + ".split_001")

        # create_right_key
        original_shape_key.vertex_group = 'shape_key_split_right'
        right_shape_key = obj.shape_key_add(from_mix=True)
        set_shape_key_values(right_shape_key, sk_properties, name=sk_properties["name"] + ".split_002")

        # Transfer Animation
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            transfer_animation(anim_data, sk_properties["name"], left_shape_key, right_shape_key)

        # Move Shape Keys to the Correct Position
        reposition_shape_key(obj, shape_keys, active_sk, mode, left_shape_key, right_shape_key)


        # Remove Original Shape Key
        obj.shape_key_remove(original_shape_key)
        if anim_data:
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{sk_properties["name"]}"].value':
                    anim_data.action.fcurves.remove(fcurve)
                    break

        # Remove Vertex Groups
        obj.vertex_groups.remove(group_left)
        obj.vertex_groups.remove(group_right)

        # restore_properties
        obj.show_only_shape_key = False

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
