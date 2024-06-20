import bpy


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



##### ---------------------------------- REGISTERING ---------------------------------- #####

classes = [
    OBJECT_OT_insert_keyframe_shape_key,
    OBJECT_OT_bake_shape_keys_animation,
]

def register():
    for cls in classes :
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes) :
        bpy.utils.unregister_class(cls)
