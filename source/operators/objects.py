import bpy

from ..functions.poll import (
    shape_key_poll,
    animation_poll,
)


##### ---------------------------------- OPERATORS ---------------------------------- #####

class OBJECT_OT_objects_from_shape_keys(bpy.types.Operator):
    bl_idname = "object.objects_from_shape_keys"
    bl_label = "Objects from Shape Keys"
    bl_description = ("Creates new object for every frame that has different Shape Key values within the selected frame range.\n"
                      "Can be used to turn keyframed mesh into separate objects.\nDuplicated meshes will be given unique name for origanizational purposes")
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
        if not shape_key_poll(context):
            return False
        if not animation_poll(context):
            cls.poll_message_set("Shape keys on active object are not animated")
            return False
        else:
            return True


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
        obj.hide_set(True)

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



##### ---------------------------------- REGISTERING ---------------------------------- #####

classes = [
    OBJECT_OT_objects_from_shape_keys,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
