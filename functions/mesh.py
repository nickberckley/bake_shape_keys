import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def store_shape_keys(obj):
    """Returns list of shape keys, active shape key index and dictionary of shape key values"""

    shape_keys = obj.data.shape_keys.key_blocks
    active = obj.active_shape_key_index

    # values
    values = {}
    for shape_key in obj.data.shape_keys.key_blocks:
        values[shape_key.name] = shape_key.value

    return shape_keys, active, values


def store_active_shape_key(obj):
    """Returns active shape key and all its properties"""

    shape_key = obj.active_shape_key

    name = shape_key.name
    value = shape_key.value
    min = shape_key.slider_min
    max = shape_key.slider_max
    vertex_group = shape_key.vertex_group
    relation = shape_key.relative_key
    
    return shape_key, name, value, min, max, vertex_group, relation


def set_shape_key_values(copy, name, value, min, max, vertex_group, relation):
    """Sets values for all shape key properties"""
    copy.name = name
    copy.value = value
    copy.slider_min = min
    copy.slider_max = max
    copy.vertex_group = vertex_group
    copy.relative_key = relation


def set_active_shape_key(name):
    bpy.context.object.active_shape_key_index = bpy.context.object.data.shape_keys.key_blocks.keys().index(name)
