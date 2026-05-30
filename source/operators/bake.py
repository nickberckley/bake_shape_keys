import bpy

from ..functions.animation import (
    ensure_channelbag,
)
from ..functions.poll import (
    has_shape_keys,
)


##### ---------------------------------- OPERATORS ---------------------------------- #####

class OBJECT_OT_shape_key_keyframe_all(bpy.types.Operator):
    bl_idname = "object.shape_key_keyframe_all"
    bl_label = "Keyframe All Shape Key Values"
    bl_description = "Keyframe all shape keys of the active object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return has_shape_keys(context.object)

    def execute(self, context):
        obj = context.object
        for key in obj.data.shape_keys.key_blocks:
            # Skip 'Basis' Key
            if key == obj.data.shape_keys.key_blocks[0]:
                continue
            key.keyframe_insert("value")

        return {'FINISHED'}


class OBJECT_OT_shape_key_action_bake(bpy.types.Operator):
    bl_idname = "object.shape_key_action_bake"
    bl_label = "Bake Shape Key Action"
    bl_description = "Insert keyframes for all shape keys on selected objects on every frame within frame range"
    bl_options = {'REGISTER', 'UNDO'}

    follow_scene_range: bpy.props.BoolProperty(
        name = "Scene Frame Range",
        description = "Bake between frame range start and end as defined in scene properties",
        default = False,
    )
    frame_start: bpy.props.IntProperty(
        name = "Start Frame",
        min = 1,
        default = 1,
    )
    frame_end: bpy.props.IntProperty(
        name = "End Frame",
        min = 1,
        default = 100,
    )
    step: bpy.props.IntProperty(
        name = "Step",
        min = 1, max = 4,
        default = 1,
    )

    constant_interpolation: bpy.props.BoolProperty(
        name = "Constant Interpolation",
        description = "All inserted keyframes will have constant interpolation",
        default = True
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        # frame_range
        layout.prop(self, "follow_scene_range")
        col = layout.column(align=True)
        row = col.row()
        row.prop(self, "frame_start", text="Frame Range")
        row.prop(self, "frame_end", text="")
        if self.follow_scene_range:
            col.enabled = False

        layout.prop(self, "step")

        layout.separator()
        layout.prop(self, "constant_interpolation")

    def invoke(self, context, event):
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end

        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # Define Frame Range
        initial_frame = context.scene.frame_current
        if self.follow_scene_range:
            self.frame_start = context.scene.frame_start
            self.frame_end = context.scene.frame_end

        if self.frame_start > self.frame_end:
            self.report({'ERROR'}, "Start frame cannot be higher than the end frame")
            return {'CANCELLED'}

        # Filter Selection
        objects = self._filter_objects(context)
        if len(objects) == 0:
            self.report({'WARNING'}, "No objects with animated shape keys in selection")
            return {'CANCELLED'}

        for obj in objects:
            shape_keys = obj.data.shape_keys.key_blocks
            basis = shape_keys[0]

            # Inserting Keyframes
            for frame in range(self.frame_start, self.frame_end + 1, self.step):
                context.scene.frame_set(frame)
                for key in shape_keys:
                    if key == basis:
                        continue
                    key.keyframe_insert(data_path="value")

            # Set Constant Interpolation
            if self.constant_interpolation:
                channelbag = ensure_channelbag(obj.data.shape_keys)
                for fcurve in channelbag.fcurves:
                    if not fcurve.data_path.startswith("key_blocks"):
                        continue
                    if basis.name in fcurve.data_path:
                        continue

                    for keyframe in fcurve.keyframe_points:
                        if self.frame_start <= keyframe.co[0] <= self.frame_end:
                            keyframe.interpolation = 'CONSTANT'

        context.scene.frame_set(initial_frame)
        self.report({'INFO'}, "Shape key action successfully baked for selected object(s)")
        return {'FINISHED'}

    def _filter_objects(self, context):
        """Get the list of applicable objects (with animated shape keys)."""

        # Initial list of selected objects.
        objects = list(context.selected_objects)
        if context.active_object not in objects:
            objects.append(context.active_object)

        filtered = []
        for obj in objects:
            if has_shape_keys(obj, check_animated=True):
                filtered.append(obj)

        return filtered


##### ---------------------------------- REGISTERING ---------------------------------- #####

classes = [
    OBJECT_OT_shape_key_keyframe_all,
    OBJECT_OT_shape_key_action_bake,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
