import bpy


##### ---------------------------------- OPERATORS ---------------------------------- #####

class OBJECT_PT_shape_key_copy(bpy.types.Operator):
    # Idea and original code by Robert Rioux (Blender Bob)

    bl_idname = "object.shape_key_copy"
    bl_label = "Copy Shape Keys"
    bl_description = ("Transfer shape keys from selected objects to active object\n"
                      "Vertex positions are transferred by index. Different number of vertices or index will give unpredictable results")
    bl_options = {'REGISTER', 'UNDO'}

    existing_only: bpy.props.BoolProperty(
        name = "Only for Existing Keys",
        description = ("Instead of creating new shape keys, operator will transfer vertex positions and shape key values\n"
                       "to existing shape keys on target object with same names as ones on source objects")
    )
    copy_values: bpy.props.BoolProperty(
        name = "Copy Values",
        description = "Copy shape key values as well",
        default = False,
    )

    @classmethod
    def poll(cls, context):
        if context.active_object:
            if context.mode == 'OBJECT':
                if len(context.selected_objects) > 1:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False


    def execute(self, context):
        sources = context.selected_objects
        target = context.active_object

        for source in sources:
            if source == target:
                continue
            if source.type != target.type:
                continue
            if not source.data.shape_keys or len(source.data.shape_keys.key_blocks) < 2:
                continue

            # filter_shape_keys
            if self.existing_only:
                if not target.data.shape_keys:
                    filtered_keys = []
                else:
                    filtered_keys = [key for key in source.data.shape_keys.key_blocks[1:] if key.name in target.data.shape_keys.key_blocks]
            else:
                filtered_keys = source.data.shape_keys.key_blocks[1:]


            for key in filtered_keys:
                if key.lock_shape:
                    continue
                if self.existing_only and key.name not in target.data.shape_keys.key_blocks:
                    continue

                # Create Basis
                if target.data.shape_keys is None:
                    basis = target.shape_key_add(from_mix=False)
                    basis.name = "Basis"

                # Add New Shape Key & Transfer Values
                if self.existing_only:
                    copy = target.data.shape_keys.key_blocks[key.name]
                else:
                    copy = target.shape_key_add(from_mix=False)

                copy.name = key.name
                copy.slider_min = key.slider_min
                copy.slider_max = key.slider_max
                copy.mute = key.mute

                if key.vertex_group != None and key.vertex_group in target.vertex_groups:
                    copy.vertex_group = str(key.vertex_group)
                if key.relative_key.name in target.data.shape_keys.key_blocks:
                    copy.relative_key = target.data.shape_keys.key_blocks[key.relative_key.name]
                if self.copy_values:
                    copy.value = key.value

                # Transfer Vertex Positions
                for source_vert, target_vert in zip(key.data, copy.data):
                    target_vert.co = source_vert.co

        self.report({'INFO'}, f"Shape keys copied from selected objects to '{target.name}'")
        return {'FINISHED'}
    


##### ---------------------------------- REGISTRATION ---------------------------------- #####

classes = [
    OBJECT_PT_shape_key_copy,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
