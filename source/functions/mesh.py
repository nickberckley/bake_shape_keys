import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def store_shape_key_values(obj):
    """Returns dict of shape keys and their values"""

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
    """Sets shape key properties from given `properties` dictionary"""

    for prop, value in properties.items():
        if hasattr(shape_key, prop):
            if prop == 'name' and name:
                setattr(shape_key, prop, name)
            else:
                setattr(shape_key, prop, value)


def set_active_shape_key(obj, shape_key):
    """Sets active shape key index to the index of the key with the given name"""

    obj.active_shape_key_index = obj.data.shape_keys.key_blocks.keys().index(shape_key.name)


def duplicate_shape_key(obj):
    """Duplicates active shape key by soloing it and adding new shape key from the mix"""

    obj.show_only_shape_key = True
    dupe_shape_key = obj.shape_key_add(from_mix=True)
    obj.show_only_shape_key = False

    return dupe_shape_key


def remove_shape_key(obj, shape_key):
    """Removes given shape key from object and deletes it's animation data"""

    # Remove Animation Data
    anim_data = obj.data.shape_keys.animation_data
    if anim_data:
        for fcurve in anim_data.action.fcurves:
            if fcurve.data_path == f'key_blocks["{shape_key.name}"].value':
                anim_data.action.fcurves.remove(fcurve)
                break

    # Remove Shape Key
    obj.shape_key_remove(shape_key)


def reposition_shape_key(obj, shape_keys, active_index, *keys, mode=None, offset=2):
    """Moves up given keys to be below active shape key"""

    if mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')

    new_index = (len(shape_keys.key_blocks) - active_index) - offset
    for key in keys:
        set_active_shape_key(obj, key)
        for _ in range(new_index):
            bpy.ops.object.shape_key_move(type='UP')

    if mode == 'EDIT':
        bpy.ops.object.mode_set(mode=mode)
