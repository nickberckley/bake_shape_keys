import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def shape_key_poll(context):
    """Check for correct context object and that it has at least one more shape key besides basis"""

    if context.object:
        obj = context.object
        if obj.type == 'MESH' and (obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) >= 2):
            return True
        else:
            return False
    else:
        return False


def animation_poll(context):
    """Check that objects shape keys are animated"""

    if context.object:
        if context.object.data.shape_keys:
            anim_data = context.object.data.shape_keys.animation_data
            if anim_data:
                return True
            else:
                return False
        else:
            return False
    else:
        return False
