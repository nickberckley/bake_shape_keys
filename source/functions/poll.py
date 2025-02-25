import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def shape_key_poll(context):
    """Check for correct type of `context.object` and that it has at least one more shape key besides basis"""

    if context.object:
        obj = context.object
        if obj.type in ('MESH'):
            if obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) >= 2:
                return True
            else:
                return False
        else:
            return False
    else:
        return False


def animation_poll(context):
    """Checks that shape keys of `context.object` are animated"""

    if shape_key_poll(context):
        if context.object.data.shape_keys.animation_data:
            return True
        else:
            return False
    else:
        return False
