import bpy


#### ------------------------------ FUNCTIONS ------------------------------ ####

def transfer_animation(shape_keys, source, *targets):
    """Transfers animation from one shape key to another"""

    anim_data = shape_keys.animation_data
    if anim_data is None or anim_data.action is None:
        return

    # Transfer F-Curves
    original_fcurve = None
    for fcurve in anim_data.action.fcurves:
        if fcurve.data_path == f'key_blocks["{source.name}"].value':
            original_fcurve = fcurve
            for keyframe in fcurve.keyframe_points:
                for target in targets:
                    target.value = keyframe.co[1]
                    target.keyframe_insert(data_path="value", frame=int(keyframe.co[0]))

        # transfer_properties_of_original_keyframes
        target_fcurves = {f'key_blocks["{target.name}"].value' for target in targets}
        if fcurve.data_path in target_fcurves:
            for keyframe in fcurve.keyframe_points:
                frame = int(keyframe.co[0])
                if original_fcurve:
                    for original_keyframe in original_fcurve.keyframe_points:
                        if int(original_keyframe.co[0]) == frame:
                            keyframe.interpolation = original_keyframe.interpolation
                            keyframe.easing = original_keyframe.easing
                            keyframe.amplitude = original_keyframe.amplitude
                            keyframe.back = original_keyframe.back
                            keyframe.period = original_keyframe.period
                            keyframe.type = original_keyframe.type

                            keyframe.handle_left = original_keyframe.handle_left
                            keyframe.handle_left_type = original_keyframe.handle_left_type
                            keyframe.handle_right = original_keyframe.handle_right
                            keyframe.handle_right_type = original_keyframe.handle_right_type
                            break
