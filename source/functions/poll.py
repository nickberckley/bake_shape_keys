import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def has_shape_keys(obj, check_animated=False):
    """Check if a given object and has at least one shape key (besides basis)."""

    if obj.type not in ('MESH'):
        return False

    if not obj.data.shape_keys:
        return False

    if len(obj.data.shape_keys.key_blocks) < 2:
        return False

    if check_animated and not obj.data.shape_keys.animation_data:
        return False

    return True
