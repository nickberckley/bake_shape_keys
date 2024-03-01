import bpy
#from inspect import currentframe, getframeinfo


#### ------------------------------ FUNCTIONS ------------------------------ ####

def remember_shape_key_values(self, context, obj):
    shape_key_values = {}
    for shape_key in obj.data.shape_keys.key_blocks:
        shape_key_values[shape_key.name] = shape_key.value
    return shape_key_values

def set_active_shape_key(name):
    bpy.context.object.active_shape_key_index = bpy.context.object.data.shape_keys.key_blocks.keys().index(name)


#### ------------------------------ OPERATORS ------------------------------ ####

class MESH_OT_split_shape_key(bpy.types.Operator):
    bl_idname = "mesh.split_shape_key"
    bl_description = "Split active shape key into two parts based on edit mode selection"
    bl_label = "Split Shape Key"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.active_object.data.shape_keys is not None

    def execute(self, context):
        obj = bpy.context.object
        if not any(v.select for v in obj.data.vertices):
            self.report({'INFO'}, "Nothing is selected in Edit Mode")
            return {'CANCELLED'}
        
        if obj.data.shape_keys.key_blocks.find(obj.active_shape_key.name) == 0:
            self.report({'INFO'}, "This operation can't be performed on basis shape key")
            return {'CANCELLED'}
        
        mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.active_object.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        
        # Create Vertex Groups 
        vertex_group_l = obj.vertex_groups.new(name="split_shape_key_left")
        selected_vertices = [v.index for v in obj.data.vertices if v.select]
        for vertex in selected_vertices:
            bpy.ops.object.vertex_group_assign()
            
        bpy.ops.mesh.select_all(action='INVERT')
        vertex_group_r = obj.vertex_groups.new(name="split_shape_key_right")
        selected_vertices = [v.index for v in obj.data.vertices if v.select]
        for vertex in selected_vertices:
            bpy.ops.object.vertex_group_assign()

        # Store Values
        shape_keys = obj.data.shape_keys.key_blocks
        values = remember_shape_key_values(self, context, obj)
        active_index = shape_keys.find(obj.active_shape_key.name)
        bpy.ops.object.mode_set(mode='OBJECT')
        saved_shape_key = bpy.context.object.active_shape_key
        original_name = saved_shape_key.name
        original_value = saved_shape_key.value
        min_value = saved_shape_key.slider_min
        max_value = saved_shape_key.slider_max
        original_vertex_group = saved_shape_key.vertex_group
        original_relation = saved_shape_key.relative_key
        
        # Create Left Version
        bpy.ops.object.shape_key_clear()
        saved_shape_key.vertex_group = 'split_shape_key_left'
        saved_shape_key.value = 1.0
        bpy.ops.object.shape_key_add(from_mix=True)
        bpy.context.object.active_shape_key.name = original_name + ".split_001"
        left_shape_key = bpy.context.object.active_shape_key
        left_shape_key.slider_min = min_value
        left_shape_key.slider_max = max_value
        left_shape_key.vertex_group = original_vertex_group
        left_shape_key.relative_key = original_relation

        # Create Right Version
        bpy.ops.object.shape_key_clear()
        saved_shape_key.vertex_group = 'split_shape_key_right'
        saved_shape_key.value = 1.0
        bpy.ops.object.shape_key_add(from_mix=True)
        bpy.context.object.active_shape_key.name = original_name + ".split_002"
        right_shape_key = bpy.context.object.active_shape_key
        right_shape_key.slider_min = min_value
        right_shape_key.slider_max = max_value
        right_shape_key.vertex_group = original_vertex_group
        right_shape_key.relative_key = original_relation

        # Paste Keyframes from Original Shape Key
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{original_name}"].value':
                    original_fcurve = fcurve
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        value = keyframe.co[1]
                        
                        left_shape_key.value = value
                        left_shape_key.keyframe_insert(data_path="value", frame=frame)
                        
                        right_shape_key.value = value
                        right_shape_key.keyframe_insert(data_path="value", frame=frame)

            # Paste Interpolation from Original Keyframes
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{left_shape_key.name}"].value' or fcurve.data_path == f'key_blocks["{right_shape_key.name}"].value':
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        for orig_keyframe in original_fcurve.keyframe_points:
                            if int(orig_keyframe.co[0]) == frame:
                                keyframe.interpolation = orig_keyframe.interpolation
                                keyframe.easing = orig_keyframe.easing
                                keyframe.handle_left_type = orig_keyframe.handle_left_type
                                keyframe.handle_right_type = orig_keyframe.handle_right_type
                                keyframe.handle_left = orig_keyframe.handle_left
                                keyframe.handle_right = orig_keyframe.handle_right
                                break

        # Remove Original Shape Key
        set_active_shape_key(original_name)
        bpy.ops.object.shape_key_remove(all=False)
        if anim_data:
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{original_name}"].value':
                    anim_data.action.fcurves.remove(fcurve)
                    break
        
        # Remove Vertex Groups
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_set_active(group='split_shape_key_left')
        bpy.ops.object.vertex_group_remove()
        bpy.ops.object.vertex_group_set_active(group='split_shape_key_right')
        bpy.ops.object.vertex_group_remove()
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # Restore Values
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key.value = values.get(shape_key.name, 0.0)
        obj.data.shape_keys.key_blocks[left_shape_key.name].value = original_value
        obj.data.shape_keys.key_blocks[right_shape_key.name].value = original_value
        
        # Move Shape Keys to Correct Position in UI
        new_index = (len(obj.data.shape_keys.key_blocks) - active_index) - 2
        bpy.ops.object.mode_set(mode='OBJECT')
        for _ in range(new_index):
            set_active_shape_key(left_shape_key.name)
            bpy.ops.object.shape_key_move(type='UP')
            set_active_shape_key(right_shape_key.name)
            bpy.ops.object.shape_key_move(type='UP')
        
        bpy.ops.object.mode_set(mode=mode)
        set_active_shape_key(left_shape_key.name)
        return {'FINISHED'}


class MESH_OT_duplicate_shape_key(bpy.types.Operator):
    bl_idname = "mesh.duplicate_shape_key"
    bl_label = "Duplicate Shape Key"
    bl_description = "Make a duplicated copy of active shape key"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.active_object.data.shape_keys is not None
    
    def execute(self, context):
        obj = bpy.context.object
        mode = bpy.context.object.mode
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        
        # Store Values
        shape_keys = obj.data.shape_keys.key_blocks
        values = remember_shape_key_values(self, context, obj)
        active_index = shape_keys.find(obj.active_shape_key.name)
        saved_shape_key = bpy.context.object.active_shape_key
        original_name = saved_shape_key.name
        original_value = saved_shape_key.value
        min_value = saved_shape_key.slider_min
        max_value = saved_shape_key.slider_max
        original_vertex_group = saved_shape_key.vertex_group
        original_relation = saved_shape_key.relative_key
        
        if active_index == 0:
            self.report({'INFO'}, "This operation can't be performed on basis shape key")
            return {'CANCELLED'}
        
        # New Shape Key from Mix
        for item in bpy.context.object.data.shape_keys.key_blocks:
            item.value = 0.0
        bpy.context.object.active_shape_key.value = 1.0
        bpy.ops.object.shape_key_add(from_mix=True)
        bpy.context.object.active_shape_key.name = original_name + '.001'
        bpy.context.object.active_shape_key.value = original_value
        dupe_shape_key = bpy.context.object.active_shape_key
        dupe_shape_key.slider_min = min_value
        dupe_shape_key.slider_max = max_value
        dupe_shape_key.vertex_group = original_vertex_group
        dupe_shape_key.relative_key = original_relation
        
        # Paste Keyframes from Original Shape Key
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{original_name}"].value':
                    original_fcurve = fcurve
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        value = keyframe.co[1]
                        
                        dupe_shape_key.value = value
                        dupe_shape_key.keyframe_insert(data_path="value", frame=frame)

            # Paste Interpolation from Original Keyframes
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{dupe_shape_key.name}"].value':
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        for orig_keyframe in original_fcurve.keyframe_points:
                            if int(orig_keyframe.co[0]) == frame:
                                keyframe.interpolation = orig_keyframe.interpolation
                                keyframe.easing = orig_keyframe.easing
                                keyframe.handle_left_type = orig_keyframe.handle_left_type
                                keyframe.handle_right_type = orig_keyframe.handle_right_type
                                keyframe.handle_left = orig_keyframe.handle_left
                                keyframe.handle_right = orig_keyframe.handle_right
                                break
            
        # Restore Values
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key.value = values.get(shape_key.name, 0.0)
            
        # Move Shape Keys to Correct Position in UI
        new_index = (len(obj.data.shape_keys.key_blocks) - active_index) - 2
        bpy.ops.object.mode_set(mode='OBJECT')
        for _ in range(new_index):
            set_active_shape_key(dupe_shape_key.name)
            bpy.ops.object.shape_key_move(type='UP')
            
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}
    

class MESH_OT_merge_shape_keys(bpy.types.Operator):
    bl_idname = "mesh.merge_shape_keys"
    bl_label = "Merge Shape Keys (All the Way)"
    bl_description = "Merge active shape key with all shape keys on above or bellow of it\nWarning: If shape key values are animated, new merged shape key will inherit the animation from active shape key, rest of the animation will be lost\nMerged shape key will also inherit vertex group and 'relative to' from active shape key"
    bl_options = {'REGISTER', 'UNDO'}
    
    direction: bpy.props.StringProperty()
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.active_object.data.shape_keys is not None
    
    def execute(self, context):
        obj = bpy.context.object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        
        # Store Values
        shape_keys = obj.data.shape_keys.key_blocks
        values = remember_shape_key_values(self, context, obj)
        active_index = shape_keys.find(obj.active_shape_key.name)
        saved_shape_key = shape_keys[active_index]
        original_name = saved_shape_key.name
        original_value = saved_shape_key.value
        min_value = saved_shape_key.slider_min
        max_value = saved_shape_key.slider_max
        original_vertex_group = saved_shape_key.vertex_group
        original_relation = saved_shape_key.relative_key
        
        # Restrictions
        if active_index == 0:
            self.report({'INFO'}, "This operation can't be performed on basis shape key")
            return {'CANCELLED'}
        
        if active_index == len(shape_keys) - 1 and self.direction == "DOWN":
            self.report({'INFO'}, "Nothing below to merge with")
            return {'CANCELLED'}

        if active_index != -1:
            # Select Top Shape Keys
            shape_keys_above = []
            for i in range(active_index + 1, len(shape_keys)):
                if shape_keys[i].name != shape_keys[0].name:
                    shape_keys_above.append(shape_keys[i])
            
            # Select Bottom Shape keys
            shape_keys_below = []
            for i in range(active_index - 1, -1, -1):
                if shape_keys[i].name != shape_keys[0].name:
                    shape_keys_below.append(shape_keys[i])
        
        # Merge Up
        if self.direction == "TOP":
            for shape_key in shape_keys_above:
                shape_key.value = 0.0
            for shape_key in shape_keys_below:
                shape_key.mute = False
                shape_key.value = 1.0
            bpy.ops.object.shape_key_add(from_mix=True)
            bpy.context.object.active_shape_key.name = original_name + '.merged'
            merged_shape_key = bpy.context.object.active_shape_key
            bpy.ops.object.shape_key_move(type='TOP')
            
        # Merge Down
        elif self.direction == "DOWN":
            for shape_key in shape_keys_below:
                shape_key.value = 0.0
            for shape_key in shape_keys_above:
                shape_key.mute = False
                shape_key.value = 1.0
            bpy.ops.object.shape_key_add(from_mix=True)
            bpy.context.object.active_shape_key.name = original_name + '.merged'
            merged_shape_key = bpy.context.object.active_shape_key
            
        merged_shape_key.slider_min = min_value
        merged_shape_key.slider_max = max_value
        merged_shape_key.vertex_group = original_vertex_group
        merged_shape_key.relative_key = original_relation
            
        # Paste Keyframes from Original Shape Key
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{original_name}"].value':
                    original_fcurve = fcurve
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        value = keyframe.co[1]
                        
                        merged_shape_key.value = value
                        merged_shape_key.keyframe_insert(data_path="value", frame=frame)

            # Paste Interpolation from Original Keyframes
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{merged_shape_key.name}"].value':
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        for orig_keyframe in original_fcurve.keyframe_points:
                            if int(orig_keyframe.co[0]) == frame:
                                keyframe.interpolation = orig_keyframe.interpolation
                                keyframe.easing = orig_keyframe.easing
                                keyframe.handle_left_type = orig_keyframe.handle_left_type
                                keyframe.handle_right_type = orig_keyframe.handle_right_type
                                keyframe.handle_left = orig_keyframe.handle_left
                                keyframe.handle_right = orig_keyframe.handle_right
                                break
        
        # Remove Shape Keys
        filtered_shape_keys = shape_keys_below if self.direction == "TOP" else shape_keys_above
        for shape_key in filtered_shape_keys:
            set_active_shape_key(shape_key.name)
            bpy.ops.object.shape_key_remove(all=False)
        set_active_shape_key(original_name)
        bpy.ops.object.shape_key_remove(all=False)
        
        for item in filtered_shape_keys:
            name = item.name
            if anim_data:
                for fcurve in anim_data.action.fcurves:
                    if fcurve.data_path == f'key_blocks["{name}"].value':
                        anim_data.action.fcurves.remove(fcurve)
            
        # Restore Values
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key.value = values.get(shape_key.name, 0.0)
        set_active_shape_key(merged_shape_key.name)
        bpy.context.object.active_shape_key.value = original_value
        
        return {'FINISHED'}


class MESH_OT_merge_shape_keys_single(bpy.types.Operator):
    bl_idname = "mesh.merge_shape_keys_single"
    bl_label = "Merge Shape Keys"
    bl_description = "Merge active shape key with shape key above or below it\nWarning: If shape key values are animated, new merged shape key will inherit the animation from active shape key, rest of the animation will be lost\nMerged shape key will also inherit range min and max values, vertex group and relations from active shape key"
    bl_options = {'REGISTER', 'UNDO'}
    
    direction: bpy.props.StringProperty()
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH' and context.active_object.data.shape_keys is not None
    
    def execute(self, context):
        obj = bpy.context.object
        mode = bpy.context.object.mode
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        
        # Store Values
        shape_keys = obj.data.shape_keys.key_blocks
        values = remember_shape_key_values(self, context, obj)
        active_index = shape_keys.find(obj.active_shape_key.name)
        saved_shape_key = shape_keys[active_index]
        original_name = saved_shape_key.name
        original_value = saved_shape_key.value
        min_value = saved_shape_key.slider_min
        max_value = saved_shape_key.slider_max
        original_vertex_group = saved_shape_key.vertex_group
        original_relation = saved_shape_key.relative_key
        
        # Restrictions
        if active_index == 0:
            self.report({'INFO'}, "This operation can't be performed on basis shape key")
            return {'CANCELLED'}
        
        if active_index == len(shape_keys) - 1 and self.direction == "DOWN":
            self.report({'INFO'}, "Nothing below to merge with")
            return {'CANCELLED'}

        # Select Shape Keys
        above_index = active_index - 1
        above_shape_key = shape_keys[above_index]
        below_index = active_index + 1
        below_shape_key = shape_keys[below_index] if not active_index == len(shape_keys) - 1 else None

        filtered_shape_keys = []
        for i, shape_key in enumerate(shape_keys):
            if self.direction == "TOP":
                if i != active_index and i != above_index:
                    filtered_shape_keys.append(shape_key)
            elif self.direction == "DOWN":
                if i != active_index and i != below_index:
                    filtered_shape_keys.append(shape_key)
        
        # Merge Up
        if self.direction == "TOP":
            saved_shape_key.value = 1.0
            above_shape_key.value = 1.0
            saved_shape_key.mute = False
            above_shape_key.mute = False
        # Merge Down
        elif self.direction == "DOWN":
            saved_shape_key.value = 1.0
            below_shape_key.value = 1.0
            saved_shape_key.mute = False
            below_shape_key.mute = False
        for shape_key in filtered_shape_keys:
            shape_key.value = 0.0
            
        bpy.ops.object.shape_key_add(from_mix=True)
        bpy.context.object.active_shape_key.name = original_name + '.merged'
        merged_shape_key = bpy.context.object.active_shape_key
        merged_shape_key.slider_min = min_value
        merged_shape_key.slider_max = max_value
        merged_shape_key.vertex_group = original_vertex_group
        merged_shape_key.relative_key = original_relation
        
        # Paste Keyframes from Original Shape Key
        anim_data = obj.data.shape_keys.animation_data
        if anim_data:
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{original_name}"].value':
                    original_fcurve = fcurve
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        value = keyframe.co[1]
                        
                        merged_shape_key.value = value
                        merged_shape_key.keyframe_insert(data_path="value", frame=frame)

            # Paste Interpolation from Original Keyframes
            for fcurve in anim_data.action.fcurves:
                if fcurve.data_path == f'key_blocks["{merged_shape_key.name}"].value':
                    for keyframe in fcurve.keyframe_points:
                        frame = int(keyframe.co[0])
                        for orig_keyframe in original_fcurve.keyframe_points:
                            if int(orig_keyframe.co[0]) == frame:
                                keyframe.interpolation = orig_keyframe.interpolation
                                keyframe.easing = orig_keyframe.easing
                                keyframe.handle_left_type = orig_keyframe.handle_left_type
                                keyframe.handle_right_type = orig_keyframe.handle_right_type
                                keyframe.handle_left = orig_keyframe.handle_left
                                keyframe.handle_right = orig_keyframe.handle_right
                                break
        
        # Remove Shape Keys
        set_active_shape_key(original_name)
        bpy.ops.object.shape_key_remove(all=False)
        if self.direction == "TOP":
            set_active_shape_key(above_shape_key.name)
            bpy.ops.object.shape_key_remove(all=False)
            if anim_data:
                for fcurve in anim_data.action.fcurves:
                    if fcurve.data_path in [f'key_blocks["{original_name}"].value', f'key_blocks["{above_shape_key.name}"].value']:
                        anim_data.action.fcurves.remove(fcurve)
            
        elif self.direction == "DOWN":
            set_active_shape_key(below_shape_key.name)
            bpy.ops.object.shape_key_remove(all=False)
            if anim_data:
                for fcurve in anim_data.action.fcurves:
                    if fcurve.data_path in [f'key_blocks["{original_name}"].value', f'key_blocks["{below_shape_key.name}"].value']:
                        anim_data.action.fcurves.remove(fcurve)
        
        # Restore Values
        for shape_key in obj.data.shape_keys.key_blocks:
            shape_key.value = values.get(shape_key.name, 0.0)
        set_active_shape_key(merged_shape_key.name)
        bpy.context.object.active_shape_key.value = original_value
            
        # Move Shape Keys to Correct Position in UI
        bpy.ops.object.mode_set(mode='OBJECT')
        if self.direction == "TOP":
            new_index = (len(obj.data.shape_keys.key_blocks) - active_index)
            for _ in range(new_index):
                bpy.ops.object.shape_key_move(type='UP')
        elif self.direction == "DOWN":
            new_index = (len(obj.data.shape_keys.key_blocks) - active_index) - 1
            for _ in range(new_index):
                bpy.ops.object.shape_key_move(type='UP')
                
        bpy.ops.object.mode_set(mode=mode)
        return {'FINISHED'}
    
    

#### ------------------------------ MENUS ------------------------------ ####

def shape_key_extras_top(self, context):
    if bpy.context.active_object is not None and bpy.context.active_object.type == 'MESH':
        layout = self.layout
        layout.operator('mesh.duplicate_shape_key', icon="DUPLICATE")
        layout.operator('mesh.split_shape_key', icon="SCULPTMODE_HLT")

def shape_key_extras_bottom(self, context):
    if bpy.context.active_object is not None and bpy.context.active_object.type == 'MESH':
        layout = self.layout
        layout.separator()
        layout.menu("MESH_MT_shape_key_merge", text="Merge Shape Keys")


class MESH_MT_shape_key_merge(bpy.types.Menu):
    bl_idname = "MESH_MT_shape_key_merge"
    bl_label = "Merge"

    def draw(self, context):
        layout = self.layout
        layout.operator('mesh.merge_shape_keys_single', text='Merge Up', icon="TRIA_UP").direction='TOP'
        layout.operator('mesh.merge_shape_keys', text='Merge Up (All the Way)', icon="SORT_DESC").direction='TOP'
        layout.operator('mesh.merge_shape_keys', text='Merge Down (All the Way)', icon="SORT_ASC").direction='DOWN'
        layout.operator('mesh.merge_shape_keys_single', text='Merge Down', icon="TRIA_DOWN").direction='DOWN'



#### ------------------------------ REGISTRATION ------------------------------ ####

classes = [
    MESH_OT_split_shape_key,
    MESH_OT_duplicate_shape_key,
    MESH_OT_merge_shape_keys,
    MESH_OT_merge_shape_keys_single,
    MESH_MT_shape_key_merge,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.MESH_MT_shape_key_context_menu.prepend(shape_key_extras_top)
    bpy.types.MESH_MT_shape_key_context_menu.append(shape_key_extras_bottom)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.types.MESH_MT_shape_key_context_menu.remove(shape_key_extras_top)
    bpy.types.MESH_MT_shape_key_context_menu.remove(shape_key_extras_bottom)