import bpy

from bpy_extras.anim_utils import action_ensure_channelbag_for_slot


#### ------------------------------ FUNCTIONS ------------------------------ ####

def ensure_channelbag(data_block):
    """Returns the channelbag of f-curves for a given ID, or None if ID doesn't have anim_data, action, or slot."""

    anim_data = data_block.animation_data
    if anim_data is None:
        return None

    action = anim_data.action
    if action is None:
        return None
    if action.is_empty:
        return None

    if anim_data.action_slot is None:
        return None

    channelbag = action_ensure_channelbag_for_slot(action, anim_data.action_slot)

    return channelbag


def transfer_animation(shape_keys, source, *targets):
    """Transfers animation (f-curve properties, keyframes, f-curve modifiers, and drivers) from one shape key to another"""

    anim_data = shape_keys.animation_data
    if anim_data is None:
        return

    channelbag = ensure_channelbag(shape_keys)
    if channelbag is not None:
        # Transfer F-Curves
        for fcurve in channelbag.fcurves:
            if fcurve.data_path == f'key_blocks["{source.name}"].value':
                # get_original_fcurve_properties
                original_fcurve_group = fcurve.group.name if fcurve.group else ""
                original_fcurve_properties = {prop.identifier: getattr(fcurve, prop.identifier)
                                                for prop in fcurve.bl_rna.properties if not prop.is_readonly}

                # get_original_keyframes
                original_keyframes = {}
                for keyframe in fcurve.keyframe_points:
                    key_properties = {prop.identifier: getattr(keyframe, prop.identifier) for prop in keyframe.bl_rna.properties if not prop.is_readonly}
                    original_keyframes[int(keyframe.co[0])] = key_properties

                # get_original_modifiers
                original_modifiers = {}
                for mod in fcurve.modifiers:
                    mod_properties = {prop.identifier: getattr(mod, prop.identifier) for prop in mod.bl_rna.properties if not prop.is_readonly}
                    original_modifiers[mod.type] = mod_properties


                for target in targets:
                    target_fcurve = channelbag.fcurves.new(f'key_blocks["{target.name}"].value', group_name=original_fcurve_group)

                    # copy_fcurve_properties
                    for prop, value in original_fcurve_properties.items():
                        if hasattr(fcurve, prop):
                            if prop not in ("data_path", "group", "is_valid"):
                                setattr(target_fcurve, prop, value)

                    # copy_keyframes
                    for keyframe, properties in original_keyframes.items():
                        new_key = target_fcurve.keyframe_points.insert(keyframe, properties["co"][1])
                        for prop, value in properties.items():
                            if hasattr(new_key, prop):
                                setattr(new_key, prop, value)

                    # copy_modifiers
                    for mod, properties in original_modifiers.items():
                        new_mod = target_fcurve.modifiers.new(mod)
                        for prop, value in properties.items():
                            if hasattr(new_mod, prop):
                                setattr(new_mod, prop, value)
                break

    # Transfer Drivers
    for driver in anim_data.drivers:
        if driver.data_path == f'key_blocks["{source.name}"].value':
            for target in targets:
                new_driver = anim_data.drivers.from_existing(src_driver=driver)
                new_driver.data_path = f'key_blocks["{target.name}"].value'
            break
