import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def shape_key_poll(context):
    """Check that context object has at least one more shape key besides basis"""
    obj = context.object

    if (obj and obj.type == 'MESH') and (obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) >= 2):
        return True
    else:
        return False


def animation_poll(context):
    """Check that objects shape keys are animated"""
    shape_keys = context.object.data.shape_keys
    anim_data = shape_keys.animation_data

    if anim_data:
        return True
    else:
        return False
