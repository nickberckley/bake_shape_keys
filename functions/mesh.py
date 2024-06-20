import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def remember_shape_key_values(self, context, obj):
    shape_key_values = {}
    for shape_key in obj.data.shape_keys.key_blocks:
        shape_key_values[shape_key.name] = shape_key.value
    return shape_key_values


def set_active_shape_key(name):
    bpy.context.object.active_shape_key_index = bpy.context.object.data.shape_keys.key_blocks.keys().index(name)
