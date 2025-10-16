import bpy
import os

from .functions.poll import shape_key_poll


#### ------------------------------ MENUS ------------------------------ ####

def animation_menu(self, context):
    layout = self.layout

    # import_icons
    pcoll = preview_collections["main"]
    keyframe_shape_key = pcoll["keyframe_shape_key"]
    bake_shape_key = pcoll["bake_shape_key"]

    if context.mode == 'OBJECT':
        layout.separator()
        layout.operator("object.shape_key_keyframe_all", text="Insert Keyframe for Shape Keys", icon_value=keyframe_shape_key.icon_id)
        layout.operator("object.shape_key_action_bake", icon_value=bake_shape_key.icon_id)
        layout.operator("object.objects_from_shape_keys")


def shape_keys_panel(self, context):
    layout = self.layout
    obj = context.active_object

    if shape_key_poll(context) and len(obj.data.shape_keys.key_blocks) >= 3:
        layout.separator()
        layout.operator("object.shape_key_keyframe_all", text="Keyframe All Shape Keys")


def copy_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("object.shape_key_transfer_all")


def shape_key_context_menu(self, context):
    layout = self.layout
    layout.operator("object.shape_key_split", text="Split", icon='SCULPTMODE_HLT')
    layout.operator("object.shape_key_duplicate", text="Duplicate (w/ Animation)", icon='DUPLICATE')


def shape_key_extras(self, context):
    layout = self.layout
    layout.separator()
    layout.menu("OBJECT_MT_shape_key_merge", text="Merge Shape Keys")


class OBJECT_MT_shape_key_merge(bpy.types.Menu):
    bl_idname = "OBJECT_MT_shape_key_merge"
    bl_label = "Merge"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.shape_key_merge", text="Merge Up", icon='TRIA_UP').direction='TOP'
        layout.operator("object.shape_key_merge_all", text="Merge Up (All the Way)", icon='SORT_DESC').direction='TOP'
        layout.operator("object.shape_key_merge_all", text="Merge Down (All the Way)", icon='SORT_ASC').direction='DOWN'
        layout.operator("object.shape_key_merge", text="Merge Down", icon='TRIA_DOWN').direction='DOWN'



#### ------------------------------ REGISTRATION ------------------------------ ####

preview_collections = {}

classes = [
    OBJECT_MT_shape_key_merge,
]


def register():
    import bpy.utils.previews

    for cls in classes:
        bpy.utils.register_class(cls)

    # PREVIEWS
    pcoll = bpy.utils.previews.new()
    icon_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("keyframe_shape_key", os.path.join(icon_dir, "keyframe_shape_key.png"), 'IMAGE')
    pcoll.load("bake_shape_key", os.path.join(icon_dir, "bake_shape_key.png"), 'IMAGE')
    preview_collections["main"] = pcoll

    # MENUS
    bpy.types.VIEW3D_MT_object_animation.append(animation_menu)
    bpy.types.DATA_PT_shape_keys.append(shape_keys_panel)
    bpy.types.MESH_MT_shape_key_tree_context_menu.prepend(shape_key_context_menu)
    bpy.types.MESH_MT_shape_key_context_menu.append(shape_key_extras)
    bpy.types.VIEW3D_MT_make_links.append(copy_menu)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # PREVIEWS
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    # MENUS
    bpy.types.VIEW3D_MT_object_animation.remove(animation_menu)
    bpy.types.MESH_MT_shape_key_tree_context_menu.remove(shape_key_context_menu)
    bpy.types.MESH_MT_shape_key_context_menu.remove(shape_key_extras)
    bpy.types.DATA_PT_shape_keys.remove(shape_keys_panel)
    bpy.types.VIEW3D_MT_make_links.remove(copy_menu)
