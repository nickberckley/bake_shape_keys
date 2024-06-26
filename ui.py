import bpy, os


#### ------------------------------ MENUS ------------------------------ ####

def bake_shape_keys_animation_menu(self, context):
    layout = self.layout

    # import_icons
    pcoll = preview_collections["main"]
    keyframe_shapekey = pcoll["keyframe_shapekey"]
    bake_shapekey = pcoll["bake_shapekey"]

    if bpy.context.mode == 'OBJECT':
        layout.separator()
        layout.operator("object.shape_key_keyframe_all", text="Insert Keyframe for Shape Keys", icon_value=keyframe_shapekey.icon_id)
        layout.operator("object.shape_key_action_bake", icon_value=bake_shapekey.icon_id)
        layout.operator("object.objects_from_shape_keys")


#def bake_shape_keys_context_menu(self, context):
#    layout = self.layout
#    preferences = bpy.context.preferences.addons[__package__].preferences
#    if context.area.type == 'VIEW_3D':
#        if preferences.show_context_menu:
#            layout.separator()
#            layout.operator("object.copy_data_names")
#    elif context.area.type == 'OUTLINER':
#        if preferences.show_outline_menu:
#            layout.separator()
#            layout.operator("object.copy_data_names")


#def bake_shape_keys_collection_menu(self, context):
#    layout = self.layout
#    preferences = bpy.context.preferences.addons[__package__].preferences
#    if preferences.show_outline_menu:
#        layout.separator()
#        layout.operator("object.copy_collection_data_names")


def bake_shape_keys_panel_menu(self, context):
    layout = self.layout
    obj = bpy.context.active_object

    if obj and obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) >= 3:
        layout.separator()
        layout.operator("object.shape_key_keyframe_all", text="Keyframe All Shape Keys")



#### ------------------------------ /specials/ ------------------------------ ####

def shape_key_extras_top(self, context):
    if bpy.context.active_object is not None and bpy.context.active_object.type == 'MESH':
        layout = self.layout
        layout.operator("object.shape_key_duplicate", icon='DUPLICATE')
        layout.operator("object.shape_key_split", icon='SCULPTMODE_HLT')


def shape_key_extras_bottom(self, context):
    if bpy.context.active_object is not None and bpy.context.active_object.type == 'MESH':
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
    pcoll.load("keyframe_shapekey", os.path.join(icon_dir, "keyframe_shapekey.png"), 'IMAGE')
    pcoll.load("bake_shapekey", os.path.join(icon_dir, "bake_shapekey.png"), 'IMAGE')
    preview_collections["main"] = pcoll

    # MENUS
    bpy.types.VIEW3D_MT_object_animation.append(bake_shape_keys_animation_menu)
    bpy.types.DATA_PT_shape_keys.append(bake_shape_keys_panel_menu)
    bpy.types.MESH_MT_shape_key_context_menu.prepend(shape_key_extras_top)
    bpy.types.MESH_MT_shape_key_context_menu.append(shape_key_extras_bottom)

#    bpy.types.VIEW3D_MT_object_context_menu.append(bake_shape_keys_context_menu)
#    bpy.types.OUTLINER_MT_object.append(bake_shape_keys_context_menu)
#    bpy.types.OUTLINER_MT_collection.append(bake_shape_keys_collection_menu)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # PREVIEWS
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()

    # MENUS
    bpy.types.VIEW3D_MT_object_animation.remove(bake_shape_keys_animation_menu)
    bpy.types.MESH_MT_shape_key_context_menu.remove(shape_key_extras_top)
    bpy.types.MESH_MT_shape_key_context_menu.remove(shape_key_extras_bottom)
    bpy.types.DATA_PT_shape_keys.remove(bake_shape_keys_panel_menu)

#    bpy.types.VIEW3D_MT_object_context_menu.append(bake_shape_keys_context_menu)
#    bpy.types.OUTLINER_MT_object.append(bake_shape_keys_context_menu)
#    bpy.types.OUTLINER_MT_collection.append(bake_shape_keys_collection_menu)
