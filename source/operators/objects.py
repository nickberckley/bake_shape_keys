import bpy
import numpy

from ..functions.poll import (
    shape_key_poll,
    animation_poll,
)


##### ---------------------------------- OPERATORS ---------------------------------- #####

class OBJECT_OT_objects_from_shape_keys(bpy.types.Operator):
    bl_idname = "object.objects_from_shape_keys"
    bl_label = "Objects from Shape Keys"
    bl_description = ("Iterates over a given frame range and creates a new object on every frame\n"
                      "if the shape key values are different from the previous frame, i.e. mesh is different")
    bl_options = {'REGISTER', 'UNDO'}

    delete_duplicates: bpy.props.BoolProperty(
        name="Delete Duplicates",
        description="Do not create a new object if the object with the same exact shape already exists",
        default=True,
    )
    consider_existing_objects: bpy.props.BoolProperty(
        name="Consider Existing Objects",
        description=("When checking for duplicates, consider objects that already exist in the scene.\n"
                     "If an object with the exact same mesh already exists in the scene, do not create a new one.\n"
                     "This is most useful when re-running the operator on the same object multiple times"),
        default=False,
    )

    start_frame: bpy.props.IntProperty(
        name="Start Frame",
        min=1,
        default=1,
    )
    end_frame: bpy.props.IntProperty(
        name="End Frame",
        min=1,
        default=10,
    )
    step: bpy.props.IntProperty(
        name="Step",
        min=1, max=4,
        default=1,
    )

    keyframes_only: bpy.props.BoolProperty(
        name="Keyframes Only",
        description="Duplicate object only on keyframed frames instead of on every frame that has different shape key values",
        default=False,
    )

    keep_position: bpy.props.BoolProperty(
        name="Keep Position",
        description="If enabled duplicated objects will have same position as original. Otherwise they'll move along the selected axis",
        default=False,
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
        default=2.0,
    )

    hide_duplicates: bpy.props.BoolProperty(
        name="Hide Duplicates",
        description="If enabled collection containing newly created objects will be hidden in the viewport",
        default=False,
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

        col = layout.column(align=True)
        col.prop(self, "delete_duplicates")
        if self.delete_duplicates:
            col.prop(self, "consider_existing_objects")
        col.separator()

        col = layout.column(align=False)
        row = col.row()
        row.prop(self, "start_frame", text="Frame Range")
        row.prop(self, "end_frame", text="")
        col.prop(self, "step")

        col.prop(self, "keyframes_only")
        col.separator()

        col = layout.column(align=True)
        col.prop(self, "keep_position")
        axis_col = layout.column(align=True)
        row = axis_col.row(align=True)
        row.prop(self, "move_axis", expand=True)
        axis_col.prop(self, "offset_distance")
        if self.keep_position:
            axis_col.enabled = False

        layout.prop(self, "hide_duplicates")


    def invoke(self, context, event):
        self.start_frame = context.scene.frame_start
        self.end_frame = context.scene.frame_end

        return context.window_manager.invoke_props_dialog(self)


    def execute(self, context):
        obj = context.object
        move_axis_index = 'XYZ'.index(self.move_axis)
        print("Starting 'Objects from Shape Keys' operator")

        # Create the Collection
        duplicates_collection = bpy.data.collections.new(obj.name + "_duplicates")
        obj.users_collection[0].children.link(duplicates_collection)

        # define_frame_range
        if self.keyframes_only:
            frame_range = set()
            for fcurve in obj.data.shape_keys.animation_data.action.fcurves:
                if fcurve.data_path.startswith("key_blocks"):
                    frame_range.update(int(keyframe.co[0]) for keyframe in fcurve.keyframe_points)
            frame_range &= set(range(self.start_frame, self.end_frame + 1, self.step))
        else:
            frame_range = range(self.start_frame, self.end_frame + 1, self.step)

        # Cache meshes in the scene
        scene_objects_cache = {}
        if self.consider_existing_objects:
            scene_objects_cache = self._cache_existing_objects(context, obj)

        unique_shape_keys_dict = {}
        prev_obj = None
        for frame in sorted(frame_range):
            context.scene.frame_set(frame)

            # Detect Duplicate
            match = None
            if self.delete_duplicates:
                sk_values, match = self._detect_duplicate(context, obj, obj.data, unique_shape_keys_dict, scene_objects_cache)

            if match:
                print(f"- Duplicate detected on the frame {frame}. Matching object: {match.name}")
            else:
                # Duplicate object
                obj_copy = obj.copy()
                obj_copy.data = obj.data.copy()
                obj_copy.name = obj_copy.data.name = obj.name + "_frame_" + str(frame)
                duplicates_collection.objects.link(obj_copy)

                # Cache shape key values to the dict of uniques
                if self.delete_duplicates:
                    unique_shape_keys_dict[sk_values] = obj_copy

                # Apply shape keys
                bpy.ops.object.select_all(action='DESELECT')
                obj_copy.select_set(True)
                context.view_layer.objects.active = obj_copy

                area = [area for area in context.screen.areas if area.type == 'VIEW_3D'][0]
                with context.temp_override(area=area):
                    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)

                obj_copy.select_set(False)

                # Offset from the previous duplicate
                if not self.keep_position:
                    if prev_obj is not None:
                        obj_copy.location[move_axis_index] = prev_obj.location[move_axis_index] + self.offset_distance
                    prev_obj = obj_copy

        # Reset everything
        context.view_layer.objects.active = obj
        obj.select_set(True)
        context.scene.frame_set(self.start_frame)
        if self.hide_duplicates:
            duplicates_collection.hide_viewport = True

        # Report
        num_duplicates = len(duplicates_collection.objects)
        self.report({'INFO'}, f"{num_duplicates} objects created. Check console for details about duplicates")
        obj.hide_set(True)

        return {'FINISHED'}


    def _cache_existing_objects(self, context, active_obj):
        """Creates a dictionary of existing mesh objects in the scene and numpy arrays of their vertex positions."""

        # Evaluate active object to get it's vertex count
        depsgraph = context.evaluated_depsgraph_get()
        eval_active_obj = active_obj.evaluated_get(depsgraph)
        eval_active_obj_vert_count = len(eval_active_obj.data.vertices)

        scene_objects_cache = {}
        for obj in context.scene.objects:
            if obj == active_obj:
                continue
            if obj.type != active_obj.type:
                continue

            eval_obj = obj.evaluated_get(depsgraph)

            # Skip objects with different vertex count than the active object
            eval_obj_vert_count = len(eval_obj.data.vertices)
            if eval_obj_vert_count != eval_active_obj_vert_count:
                continue

            verts_co = numpy.empty((eval_obj_vert_count * 3), dtype=numpy.float64)
            eval_obj.data.vertices.foreach_get("co", verts_co)

            scene_objects_cache[obj] = verts_co

        return scene_objects_cache


    def _detect_duplicate(self, context, obj, data, unique_shape_keys_dict, scene_objects_cache):
        """Checks if the exact match of the evaluated mesh (on the current frame) has already been created in loop (or exists in the scene)."""
        """Compares array of evaluated meshes vertex positions to other arrays in `unique_verts_dict` and returns match if found."""
        """If match is not found array is added to the dict as an unique."""

        match = None
        sk_values = None
        verts_co = None

        # Compare current shape key values to previously stored ones
        sk_values = tuple(key.value for key in data.shape_keys.key_blocks)
        if sk_values in unique_shape_keys_dict:
            match = unique_shape_keys_dict[sk_values]

        # Compare to existing objects in the scene
        if self.consider_existing_objects:
            depsgraph = context.evaluated_depsgraph_get()
            eval_obj = obj.evaluated_get(depsgraph)

            verts_co = numpy.empty((len(eval_obj.data.vertices) * 3), dtype=numpy.float64)
            eval_obj.data.vertices.foreach_get("co", verts_co)

            for key, values in scene_objects_cache.items():
                if numpy.array_equal(verts_co, values):
                    match = key
                    break

        return sk_values, match



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
