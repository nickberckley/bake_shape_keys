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

import bpy

from . import ui
from .operators import (
    bake,
    duplicate,
    merge,
    objects,
    split,
)


##### ---------------------------------- PREFERENCES ---------------------------------- #####

def update_sidemenu_category(self, context):
    try:
        bpy.utils.unregister_class(ui.VIEW3D_PT_bake_shape_key_panel)
    except:
        pass
    ui.VIEW3D_PT_bake_shape_key_panel.bl_category = self.sidepanel_category
    bpy.utils.register_class(ui.VIEW3D_PT_bake_shape_key_panel)
#    context.preferences.addons[__package__].preferences.sidepanel_category = self.sidepanel_category

#    for cls in panel_classes:
#        try:
#            bpy.utils.unregister_class(cls)
#        except:
#            pass
#        cls.bl_category = self.category
#        bpy.utils.register_class(cls)

class BakeShapeKeysPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

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


        

##### ---------------------------------- REGISTERING ---------------------------------- #####

classes = [
        BakeShapeKeysPreferences,
]

modules = [
    ui,
    bake,
    duplicate,
    merge,
    objects,
    split,
]

def register():
    from bpy.utils import register_class
    import bpy.utils.previews
    for cls in classes :
        register_class(cls)

    for module in modules:
        module.register()

    prefs = bpy.context.preferences.addons[__package__].preferences
    update_sidemenu_category(prefs, bpy.context)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes) :
        unregister_class(cls)

    for module in reversed(modules):
        module.unregister()


if __name__ == "__main__":
    register()
