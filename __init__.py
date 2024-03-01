bl_info = {
    "name": "Bake Shape Keys",
    "description": "Shape Key Operations for Stop-Motion Animation",
    "author": "Nika Kutsniashvili (nickberckley)",
    "version": (1, 1),
    "blender": (3, 5, 0),
    "doc_url": "https://blendermarket.com/products/bake-shape-keys", 
    "tracker_url": "https://blenderartists.org/t/bake-shape-keys-stop-motion-and-3d-printing-add-on/1458920",
    "location": "Object > Animation menu in Object Mode",
    "category": "Animation",
}

import bpy, subprocess, os
from pathlib import Path
from . import shape_key_operators

##### ---------------------------------- PREFERENCES ---------------------------------- #####

def update_sidemenu_category(self, context):
    try:
        bpy.utils.unregister_class(VIEW3D_PT_bake_shape_key_panel)
    except:
        pass
    VIEW3D_PT_bake_shape_key_panel.bl_category = self.sidepanel_category
    bpy.utils.register_class(VIEW3D_PT_bake_shape_key_panel)
#    context.preferences.addons[__name__].preferences.sidepanel_category = self.sidepanel_category

#    for cls in panel_classes:
#        try:
#            bpy.utils.unregister_class(cls)
#        except:
#            pass
#        cls.bl_category = self.category
#        bpy.utils.register_class(cls)

class BakeShapeKeysPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    show_sidepanel: bpy.props.BoolProperty(
        name="Sidebar (N-menu)",
        description="Add 'Bake Shape Keys' panel in the UI",
        default=True
    )
    sidepanel_category: bpy.props.StringProperty(
        name="Sidebar Category",
        description="Category for the panel in the Sidebar (N-menu)",
        default="Animate",
        update=update_sidemenu_category
    )

    show_shape_key_panel: bpy.props.BoolProperty(
        name="Shape Key Panel",
        description="Add 'Bake Shape Keys' buttons in the Object Data > Shape Keys (also in Shape Key Specials menu)",
        default=True
    )
    
#    show_context_menu: bpy.props.BoolProperty(
#        name="3D Viewport Context Menu",
#        description="Add 'Copy Data Names' button in the 3D viewport object context menu",
#        default=True
#    )
#    show_outline_menu: bpy.props.BoolProperty(
#        name="Outliner Context Menu",
#        description="Add 'Copy Data Names' button in the outliner context menus (for objects and collections)",
#        default=True
#    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        col = layout.column(heading="'Bake Shape Keys' Location")
        col.prop(self, "show_shape_key_panel")
        col.prop(self, "show_sidepanel")
        row = col.row(align=True)
        row.prop(self, "sidepanel_category")
        
#        layout.separator()
#        col = layout.column(heading="Add 'Copy Data Names' Button")
#        col.prop(self, "show_context_menu", text="3D Viewport Context Menu")
#        col.prop(self, "show_outline_menu", text="Outliner Context Menus")
        
        if not self.show_sidepanel:
            row.enabled = False

##### ---------------------------------- OPERATORS ---------------------------------- #####

class OBJECT_OT_insert_keyframe_shape_key(bpy.types.Operator):
    bl_idname = "object.add_shape_key_keyframe_operator"
    bl_label = "Insert Keyframe for All Shape Keys"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.data.shape_keys is not None

    def execute(self, context):
        for shape_key in context.object.data.shape_keys.key_blocks:
            if shape_key.name != 'Basis':
                shape_key.keyframe_insert("value")
        return {'FINISHED'}



class OBJECT_OT_bake_shape_keys_animation(bpy.types.Operator):
    bl_idname = "object.bake_shape_key_animation"
    bl_label = "Bake Shape Key Action"
    bl_description = "Insert keyframes for all Shape Keys on selected objects within frame range"
    bl_options = {'REGISTER', 'UNDO'}
    
    follow_scene_range: bpy.props.BoolProperty(
        name="Scene Frame Range",
        description="Bake between frame range as defined in scene properties",
        default=False
    )
    start_frame: bpy.props.IntProperty(
        name="Start Frame",
        default=1, min=1
    )
    end_frame: bpy.props.IntProperty(
        name="End Frame",
        default=100, min=1
    )
    step: bpy.props.IntProperty(
        name="Step",
        default=1, min=1, max=4
    )
    
    even_odd_frames: bpy.props.EnumProperty(
        name="Even/Odd Frames",
        items=(
            ("Even", "Even Frames", "Insert keyframes on even frames"),
            ("Odd", "Odd Frames", "Insert keyframes on odd frames")
        ),
        default="Odd",
        description="If Step is set to an even number you can choose to bake animation on either even or odd numbered frames"
    )
    constant_interpolation: bpy.props.BoolProperty(
        name="Constant Interpolation",
        description="Inserted keyframes will have constant interpolation between them",
        default=True
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.data.shape_keys is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if self.follow_scene_range:
            self.start_frame = bpy.context.scene.frame_start
            self.end_frame = bpy.context.scene.frame_end
            
        for obj in bpy.context.selected_objects:
            # Inserting Keyframes
            for key in obj.data.shape_keys.key_blocks:
                if key.name != 'Basis':
                    if self.step == 2:
                        start = self.start_frame + (self.even_odd_frames == "Odd")
                        for frame in range(start, self.end_frame+1, 2):
                            bpy.context.scene.frame_set(frame)
                            key.keyframe_insert(data_path='value', index=-1)
                    elif self.step == 4:
                        start = self.start_frame + (self.even_odd_frames == "Odd")
                        for frame in range(start, self.end_frame+1, 4):
                            bpy.context.scene.frame_set(frame)
                            key.keyframe_insert(data_path='value', index=-1)
                    else:
                        for frame in range(self.start_frame, self.end_frame+1, self.step):
                            bpy.context.scene.frame_set(frame)
                            key.keyframe_insert(data_path='value', index=-1)
            
            # Constant Interpolation
            if self.constant_interpolation:
                for fcurve in obj.data.shape_keys.animation_data.action.fcurves:
                    if fcurve.data_path.startswith("key_blocks") and \
                        any(self.start_frame <= keyframe.co[0] <= self.end_frame for keyframe in fcurve.keyframe_points):
                        for keyframe in fcurve.keyframe_points:
                            if self.start_frame <= keyframe.co[0] <= self.end_frame:
                                keyframe.interpolation = 'CONSTANT' 
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        layout.prop(self, "follow_scene_range")
        col = layout.column(align=True)
        row = col.row()
        row.prop(self, "start_frame", text="Frame Range")
        row.prop(self, "end_frame", text="")
        layout.prop(self, "step")
        col2 = layout.column()
        col2.prop(self, "even_odd_frames")
        layout.prop(self, "constant_interpolation")
        
        if self.follow_scene_range:
            col.enabled = False
        if self.step % 2 == 0:
            col2.enabled = True
        else:
            col2.enabled = False



class OBJECT_OT_objects_from_shape_keys(bpy.types.Operator):
    bl_idname = "object.objects_from_shape_keys"
    bl_label = "Objects from Shape Keys"
    bl_description = "Creates new object for every frame that has different Shape Key values within the selected frame range.\nCan be used to turn keyframed mesh into separate objects.\nDuplicated meshes will be given unique name for origanizational purposes"
    bl_options = {'REGISTER', 'UNDO'}
    
    delete_duplicates: bpy.props.BoolProperty(
        name="Delete Duplicates",
        description="If duplicated object is exact copy of previous one it will be deleted automatically",
        default=True
    )
    
    start_frame: bpy.props.IntProperty(
        name="Start Frame",
        default=1, min=1
    )
    end_frame: bpy.props.IntProperty(
        name="End Frame",
        default=10, min=1
    )
    step: bpy.props.IntProperty(
        name="Step", 
        default=1, min=1, max=4
    )
    
    keyframes_only: bpy.props.BoolProperty(
        name="Keyframes Only",
        description="Duplicate object only on keyframed frames instead of on every frame that has different shape key values", 
        default=False
    )
    
    keep_position: bpy.props.BoolProperty(
        name="Keep Position",
        description="If enabled duplicated objects will have same position as original. Otherwise they'll move along the selected axis",
        default=False
    )
    move_axis: bpy.props.EnumProperty(
        name="Move on Axis",
        description="Axis to move the duplicated objects on",
        items=[('X', "X", "Move on X axis"),
               ('Y', "Y", "Move on Y axis"),
               ('Z', "Z", "Move on Z axis")],
        default = 'X',
    )
    offset_distance: bpy.props.FloatProperty(
        name="Offset",
        description="Distance to move each object by",
        subtype='DISTANCE', unit='LENGTH',
        default=2.0
    )

    hide_duplicates: bpy.props.BoolProperty(
        name="Hide Duplicates",
        description="If enabled collection containing newly created objects will be hidden in the viewport",
        default=False
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.data.shape_keys is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        obj = context.active_object
        move_axis_index = 'XYZ'.index(self.move_axis)
        
        # Create Collection
        duplicates_collection = bpy.data.collections.new(obj.name + "_duplicates")
        obj.users_collection[0].children.link(duplicates_collection)
        
        # Define Timeline
        if self.keyframes_only:
            keyframe_frames = set()
            for fcurve in obj.data.shape_keys.animation_data.action.fcurves:
                if fcurve.data_path.startswith("key_blocks"):
                    keyframe_frames.update(int(keyframe.co[0]) for keyframe in fcurve.keyframe_points)
            keyframe_frames &= set(range(self.start_frame, self.end_frame + 1, self.step))
        else:
            keyframe_frames = range(self.start_frame, self.end_frame + 1, self.step)

        # Iteration
        prev_obj = None
        for frame in sorted(keyframe_frames):
            context.scene.frame_set(frame)

            # Duplicating the Object
            obj_copy = obj.copy()
            obj_copy.data = obj.data.copy()
            obj_copy.name = obj.name + "_frame_" + str(frame)
            
            context.collection.objects.link(obj_copy)
            bpy.ops.object.select_all(action='DESELECT')
            obj_copy.select_set(True)
            context.view_layer.objects.active = obj_copy

            # Applying Shape Keys
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
            obj_copy.select_set(False)

            # Mesh Naming Convention
            name = ''.join([self._get_name(key) for key in obj.data.shape_keys.key_blocks if key.name != 'Basis'])
            if self.delete_duplicates:
                data_type = type(obj.data)
                if data_type == bpy.types.Mesh:
                    if bpy.data.meshes.get(name) is not None:
                        bpy.data.objects.remove(obj_copy)
                        continue
                elif data_type == bpy.types.Curve:
                    if bpy.data.curves.get(name) is not None:
                        obj = bpy.data.objects.get(name)
                        bpy.data.objects.delete(obj_copy)
                        continue
                elif data_type == bpy.types.Lattice:
                    if bpy.data.lattices.get(name) is not None:
                        bpy.data.objects.remove(obj_copy)
                        continue
                    
            if len(name) < 6:
                obj_copy.data.name = obj.name + "_shape_key_" + name
            else:
                obj_copy.data.name = name
            
            # Move to Collection
            duplicates_collection.objects.link(obj_copy)
            for coll in obj_copy.users_collection:
                if coll != duplicates_collection:
                    coll.objects.unlink(obj_copy)
                    
            # Offset Duplicates
            if not self.keep_position:
                if prev_obj is not None:
                    obj_copy.location[move_axis_index] = prev_obj.location[move_axis_index] + self.offset_distance
                prev_obj = obj_copy

        # Reset Everything
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        context.scene.frame_set(self.start_frame)
        if self.hide_duplicates:
            duplicates_collection.hide_viewport = True
        
        # Report
        num_duplicates = len(duplicates_collection.objects)
        self.report({'INFO'}, "{} objects created".format(num_duplicates))
        return {'FINISHED'}
    
    def _get_name(self, key):
        value = key.value
        if value.is_integer():
            return chr(int(value) + 65)
        elif value < 1:
            return str(int(value * 100))
        else:
            integer_part = chr(int(value) + 64)
            decimal_part = str(int((value % 1) * 100))
            return f"{integer_part}{decimal_part}"
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        layout.prop(self, "delete_duplicates")
        col = layout.column(align=True)
        row = col.row()
        row.prop(self, "start_frame", text="Frame Range")
        row.prop(self, "end_frame", text="")
        layout.prop(self, "step")
        layout.prop(self, "keyframes_only")
        layout.separator()
        layout.prop(self, "keep_position")
        col2 = layout.column(align=True)
        row = col2.row(align=True)
        row.prop(self, "move_axis", expand=True)
        col2.prop(self, "offset_distance")
        layout.prop(self, "hide_duplicates")
        
        if self.keep_position:
            col2.enabled = False


#class OBJECT_OT_shape_key_renamer(bpy.types.Operator):
#    bl_idname = "object.shape_key_renamer"
#    bl_label = "Rename Object After Shape Key Values"
#    bl_options = {'REGISTER', 'UNDO'}

#    def execute(self, context):
#        mesh = context.object.data
#        if mesh is not None:
#            name = ''.join([self._get_name(key) for key in mesh.shape_keys.key_blocks if key.name != 'Basis'])
#            if len(name) < 6:
#                mesh.data.name = obj.name + "_ShapeKey_" + name
#            else:
#                mesh.data.name = name
#        return {'FINISHED'}

#    def _get_name(self, key):
#        value = key.value
#        if value.is_integer():
#            return chr(int(value) + 65)
#        elif value < 1:
#            return str(int(value * 100))
#        else:
#            integer_part = chr(int(value) + 64)
#            decimal_part = str(int((value % 1) * 100))
#            return f"{integer_part}{decimal_part}"
        

#class OBJECT_OT_copy_data_names(bpy.types.Operator):
#    bl_idname = "object.copy_data_names"
#    bl_label = "Copy Data Names"
#    bl_description = "Copy Object Data Names to Clipboard"
#    
#    def execute(self, context):
#        mesh_names = []
#        for obj in bpy.context.selected_objects:
#            mesh_names.append(obj.data.name)
#        clipboard_text = '\n'.join(mesh_names)
#        bpy.context.window_manager.clipboard = clipboard_text
#        self.report({'INFO'}, "Object data names copied to clipboard")
#        return {'FINISHED'}
#    
#class OBJECT_OT_copy_data_names_collection(bpy.types.Operator):
#    bl_idname = "object.copy_collection_data_names"
#    bl_label = "Copy Data Names"
#    bl_description = "Copy Object Data Names to Clipboard for All Objects Inside the Collection"
#    
#    def execute(self, context):
#        collection = context.collection
#        mesh_names = []
#        for obj in collection.objects:
#            mesh_names.append(obj.data.name)
#        clipboard_text = '\n'.join(mesh_names)
#        bpy.context.window_manager.clipboard = clipboard_text
#        self.report({'INFO'}, "Object data names copied to clipboard")
#        return {'FINISHED'}



##### ---------------------------------- MENUS ---------------------------------- #####

class VIEW3D_PT_bake_shape_key_panel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_add_shape_key_keyframe_panel"
    bl_label = "Bake Shape Keys"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Animate"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        prefs = bpy.context.preferences.addons[__name__].preferences
        if prefs.show_sidepanel:
            return True
        else:
            return False

    def draw(self, context):
        layout = self.layout
        layout.operator("object.add_shape_key_keyframe_operator", text="Insert Keyframe for Shape Keys")
        layout.operator("object.bake_shape_key_animation")
        layout.operator("object.objects_from_shape_keys")

        
def bake_shape_keys_animation_menu(self, context):
    layout = self.layout
    pcoll = preview_collections["main"]
    keyframe_shapekey = pcoll["keyframe_shapekey"]
    bake_shapekey = pcoll["bake_shapekey"]
    
    if bpy.context.mode == "OBJECT":
        layout.separator()
        layout.operator("object.add_shape_key_keyframe_operator", text="Insert Keyframe for Shape Keys", icon_value=keyframe_shapekey.icon_id)
        layout.operator("object.bake_shape_key_animation", icon_value=bake_shapekey.icon_id)
        layout.operator("object.objects_from_shape_keys")


#def bake_shape_keys_context_menu(self, context):
#    layout = self.layout
#    preferences = bpy.context.preferences.addons[__name__].preferences
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
#    preferences = bpy.context.preferences.addons[__name__].preferences
#    if preferences.show_outline_menu:
#        layout.separator()
#        layout.operator("object.copy_collection_data_names")

    
def bake_shape_keys_panel_menu(self, context):
    layout = self.layout
    active_object = bpy.context.active_object
    preferences = bpy.context.preferences.addons[__name__].preferences
    if preferences.show_shape_key_panel:
        if active_object and active_object.data.shape_keys and len(active_object.data.shape_keys.key_blocks) >= 3:
            layout.separator()
            layout.operator("object.add_shape_key_keyframe_operator", text="Keyframe All Shape Keys")
#            layout.operator("object.bake_shape_key_animation")

##### ---------------------------------- REGISTERING ---------------------------------- #####

preview_collections = {}
classes = [
        VIEW3D_PT_bake_shape_key_panel,
        OBJECT_OT_insert_keyframe_shape_key,
        OBJECT_OT_bake_shape_keys_animation,
        OBJECT_OT_objects_from_shape_keys,
#       OBJECT_OT_shape_key_renamer,
#       OBJECT_OT_copy_data_names,
#       OBJECT_OT_copy_data_names_collection,
        BakeShapeKeysPreferences,
]

def register():
    from bpy.utils import register_class
    import bpy.utils.previews
    for cls in classes :
        register_class(cls)

    prefs = bpy.context.preferences.addons[__name__].preferences
    update_sidemenu_category(prefs, bpy.context)
        
    bpy.types.VIEW3D_MT_object_animation.append(bake_shape_keys_animation_menu)
#    bpy.types.VIEW3D_MT_object_context_menu.append(bake_shape_keys_context_menu)
#    bpy.types.OUTLINER_MT_object.append(bake_shape_keys_context_menu)
#    bpy.types.OUTLINER_MT_collection.append(bake_shape_keys_collection_menu)
    bpy.types.DATA_PT_shape_keys.append(bake_shape_keys_panel_menu)
    
    pcoll = bpy.utils.previews.new()
    icon_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("keyframe_shapekey", os.path.join(icon_dir, "keyframe_shapekey.png"), 'IMAGE')
    pcoll.load("bake_shapekey", os.path.join(icon_dir, "bake_shapekey.png"), 'IMAGE')
    preview_collections["main"] = pcoll

    shape_key_operators.register()

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes) :
        unregister_class(cls)
        
    bpy.types.VIEW3D_MT_object_animation.remove(bake_shape_keys_animation_menu)
#    bpy.types.VIEW3D_MT_object_context_menu.append(bake_shape_keys_context_menu)
#    bpy.types.OUTLINER_MT_object.append(bake_shape_keys_context_menu)
#    bpy.types.OUTLINER_MT_collection.append(bake_shape_keys_collection_menu)
    bpy.types.DATA_PT_shape_keys.remove(bake_shape_keys_panel_menu)

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    
    shape_key_operators.unregister()

if __name__ == "__main__":
    register()
