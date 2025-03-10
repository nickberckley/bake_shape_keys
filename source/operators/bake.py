import bpy

from ..functions.poll import (
    shape_key_poll,
    animation_poll,
)


##### ---------------------------------- OPERATORS ---------------------------------- #####

class OBJECT_OT_shape_key_keyframe_all(bpy.types.Operator):
    bl_idname = "object.shape_key_keyframe_all"
    bl_label = "Insert Keyframe for All Shape Keys"
    bl_description = "Keyframe all shape keys of the active object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return shape_key_poll(context)

    def execute(self, context):
        obj = context.object
        for key in obj.data.shape_keys.key_blocks:
            if key != obj.data.shape_keys.key_blocks[0]:
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
    start_frame: bpy.props.IntProperty(
        name = "Start Frame",
        min = 1,
        default = 1,
    )
    end_frame: bpy.props.IntProperty(
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
        description = "Inserted keyframes will have constant interpolation between them",
        default = True
    )

    @classmethod
    def poll(cls, context):
        if shape_key_poll(context):
            if animation_poll(context):
                return True
            else:
                cls.poll_message_set("Shape keys on active object are not animated")
                return False
        else:
            return False

    def invoke(self, context, event):
        self.start_frame = context.scene.frame_start
        self.end_frame = context.scene.frame_end

        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # define_frame_range
        initial_frame = context.scene.frame_current
        if self.follow_scene_range:
            self.start_frame = context.scene.frame_start
            self.end_frame = context.scene.frame_end


        for obj in context.selected_objects:
            shape_keys = obj.data.shape_keys.key_blocks
            basis = shape_keys[0]

            # Inserting Keyframes
            for key in shape_keys:
                if key != basis:
                    for frame in range(self.start_frame, self.end_frame + 1, self.step):
                        context.scene.frame_set(frame)
                        key.keyframe_insert(data_path="value")

            # Set Constant Interpolation
            if self.constant_interpolation:
                for fcurve in obj.data.shape_keys.animation_data.action.fcurves:
                    if not fcurve.data_path.startswith("key_blocks"):
                        continue
                    if basis.name in fcurve.data_path:
                        continue

                    for keyframe in fcurve.keyframe_points:
                        if self.start_frame <= keyframe.co[0] <= self.end_frame:
                            keyframe.interpolation = 'CONSTANT'


        context.scene.frame_set(initial_frame)
        self.report({'INFO'}, "Shape key action successfully baked for selected object(s)")        
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        # frame_range
        layout.prop(self, "follow_scene_range")
        col = layout.column(align=True)
        row = col.row()
        row.prop(self, "start_frame", text="Frame Range")
        row.prop(self, "end_frame", text="")
        layout.prop(self, "step")

        layout.separator()
        layout.prop(self, "constant_interpolation")

        if self.follow_scene_range:
            col.enabled = False



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
