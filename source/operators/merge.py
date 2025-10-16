import bpy

from ..functions.animation import (
    transfer_animation,
)
from ..functions.mesh import (
    set_active_shape_key,
    store_shape_key_values,
    store_active_shape_key,
    set_shape_key_values,
    remove_shape_key,
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
                      "WARNING: If shape key values are animated, merged shape key will inherit the animation of active key.\n"
                      "Rest of the animation will be lost, as well as other properties from merged shape keys\n")
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        name = "Direction",
        items = [('TOP', "Top", ""),
                 ('DOWN', "Down", "")],
        default = 'DOWN',
    )

    @classmethod
    def poll(cls, context):
        return shape_key_poll(context)

    def execute(self, context):
        obj = context.object
        shape_keys = obj.data.shape_keys
        active_index = obj.active_shape_key_index
        mode = obj.mode

        if (active_index == 0) or (active_index == 1 and self.direction == 'TOP'):
            self.report({'INFO'}, "Basis shape key can't be merged with anything")
            return {'CANCELLED'}

        if (active_index == len(shape_keys.key_blocks) - 1) and self.direction == 'DOWN':
            self.report({'INFO'}, "No shape keys below to merge with")
            return {'CANCELLED'}

        if mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Get shape keys and their properties
        sk_values = store_shape_key_values(obj)
        original_shape_key, sk_properties = store_active_shape_key(obj)

        # Filter shape keys
        shape_keys_above = []
        shape_keys_below = []
        for i, key in enumerate(shape_keys.key_blocks):
            if i == active_index or i == 0:
                continue
            if i < active_index:
                shape_keys_above.append(key)
            else:
                shape_keys_below.append(key)

        # Merge Up
        if self.direction == 'TOP':
            for shape_key in shape_keys_below:
                shape_key.value = 0.0

            merged_shape_key = obj.shape_key_add(from_mix=True)
            set_active_shape_key(obj, merged_shape_key)
            bpy.ops.object.shape_key_move(type='TOP')

        # Merge Down
        elif self.direction == 'DOWN':
            for shape_key in shape_keys_above:
                shape_key.value = 0.0

            merged_shape_key = obj.shape_key_add(from_mix=True)

        # Transfer properties & animation
        set_shape_key_values(merged_shape_key, sk_properties, name=sk_properties["name"] + ".merged")
        transfer_animation(shape_keys, original_shape_key, merged_shape_key)

        # Remove shape keys
        filtered_shape_keys = shape_keys_above if self.direction == 'TOP' else shape_keys_below
        for shape_key in filtered_shape_keys + [original_shape_key]:
            remove_shape_key(obj, shape_key)

        # Restore values
        for shape_key in shape_keys.key_blocks:
            shape_key.value = sk_values.get(shape_key.name, 0.0)

        merged_shape_key.value = sk_properties["value"]
        set_active_shape_key(obj, merged_shape_key)

        if mode == 'EDIT':
            bpy.ops.object.mode_set(mode=mode)

        return {'FINISHED'}


class OBJECT_OT_shape_key_merge(bpy.types.Operator):
    bl_idname = "object.shape_key_merge"
    bl_label = "Merge Shape Keys"
    bl_description = ("Merge active shape key with shape key above or below it.\n"
                      "WARNING: If shape key values are animated, merged shape key will inherit the animation of active key.\n"
                      "Rest of the animation will be lost, as well as other properties from merged shape keys\n")
    bl_options = {'REGISTER', 'UNDO'}

    direction: bpy.props.EnumProperty(
        name = "Direction",
        items = [('TOP', "Top", ""),
                 ('DOWN', "Down", "")],
        default = 'DOWN',
    )

    @classmethod
    def poll(cls, context):
        return shape_key_poll(context)

    def execute(self, context):
        obj = context.object
        shape_keys = obj.data.shape_keys
        active_index = obj.active_shape_key_index
        mode = context.object.mode

        if (active_index == 0) or (active_index == 1 and self.direction == 'TOP'):
            self.report({'INFO'}, "Basis shape key can't be merged with anything")
            return {'CANCELLED'}

        if (active_index == len(shape_keys.key_blocks) - 1) and self.direction == 'DOWN':
            self.report({'INFO'}, "No shape keys below to merge with")
            return {'CANCELLED'}

        if mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # Get shape keys and their properties
        sk_values = store_shape_key_values(obj)
        original_shape_key, sk_properties = store_active_shape_key(obj)
        above_shape_key = shape_keys.key_blocks[active_index - 1]
        below_shape_key = shape_keys.key_blocks[active_index + 1] if active_index != len(shape_keys.key_blocks) - 1 else None

        # New Shape Key from Mix
        for shape_key in shape_keys.key_blocks:
            if shape_key == original_shape_key:
                continue
            if ((self.direction == 'TOP' and shape_key != above_shape_key) or
                (self.direction == 'DOWN' and shape_key != below_shape_key)):
                    shape_key.value = 0.0

        merged_shape_key = obj.shape_key_add(from_mix=True)

        # Transfer properties & animation
        set_shape_key_values(merged_shape_key, sk_properties, name=sk_properties["name"] + ".merged")
        transfer_animation(shape_keys, original_shape_key, merged_shape_key)

        # Move the shape key to the correct position in the UI
        reposition_shape_key(obj, shape_keys, active_index, merged_shape_key,
                             mode=mode, offset=0 if self.direction=='TOP' else 1)

        # Remove shape keys
        filtered_shape_keys = [original_shape_key, above_shape_key if self.direction=='TOP' else below_shape_key]
        for shape_key in filtered_shape_keys:
            remove_shape_key(obj, shape_key)

        # Restore values
        for shape_key in shape_keys.key_blocks:
            shape_key.value = sk_values.get(shape_key.name, 0.0)

        merged_shape_key.value = sk_properties["value"]
        set_active_shape_key(obj, merged_shape_key)

        if mode == 'EDIT':
            bpy.ops.object.mode_set(mode=mode)

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
