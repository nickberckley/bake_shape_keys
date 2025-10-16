import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def shape_key_poll(context):
    """Check for correct type of `context.object` and that it has at least one more shape key besides basis"""

    if not context.object:
        return False

    obj = context.object

    if obj.type not in ('MESH'):
        return False
    if not obj.data.shape_keys:
        return False
    if len(obj.data.shape_keys.key_blocks) < 2:
        return True
    else:
        return True


def animation_poll(context):
    """Checks that shape keys of `context.object` are animated"""

    if not shape_key_poll(context):
        return False
    if not context.object.data.shape_keys.animation_data:
        return False
    else:
        return True
