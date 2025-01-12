import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def store_shape_key_values(obj):
    """Returns list of shape keys, active shape key index and dictionary of shape key values"""

    shape_key_values = {}
    if obj.data.shape_keys:
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key_values[shape_key.name] = shape_key.value

    return shape_key_values


def store_active_shape_key(obj):
    """Returns active shape key and dictionary of its properties"""

    shape_key = obj.active_shape_key
    properties = {prop.identifier: getattr(shape_key, prop.identifier)
                  for prop in shape_key.bl_rna.properties if not prop.is_readonly}

    return shape_key, properties


def set_shape_key_values(shape_key, properties, name=None):
    """Sets shape key properties from dictionary"""

    for prop, value in properties.items():
        if hasattr(shape_key, prop):
            if prop == 'name' and name:
                setattr(shape_key, prop, name)
            else:
                setattr(shape_key, prop, value)


def set_active_shape_key(obj, name):
    obj.active_shape_key_index = obj.data.shape_keys.key_blocks.keys().index(name)


def reposition_shape_key(obj, shape_keys, active_index, mode, *keys, offset=2):
    """Moves up shape key to be below active shape key"""

    bpy.ops.object.mode_set(mode='OBJECT')

    new_index = (len(shape_keys) - active_index) - offset
    for key in keys:
        set_active_shape_key(obj, key.name)
        for _ in range(new_index):
            bpy.ops.object.shape_key_move(type='UP')

    bpy.ops.object.mode_set(mode=mode)
