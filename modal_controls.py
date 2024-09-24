if 'bpy' in locals():
    import importlib
    if 'global_vars' in locals():
        importlib.reload(global_vars)
    if 'draw_handler' in locals():
        importlib.reload(draw_handler)
import bpy
from . import global_vars
from . import draw_handler
from bpy.props import FloatVectorProperty, StringProperty
from mathutils import Vector

drawer = None
class LP_OT_BhydeModal(bpy.types.Operator):
    bl_idname = "view3d.bhyde_modal_control"
    bl_label = "Bhyde Hotkey Controls"

    offset: FloatVectorProperty( name="Offset", size=2, )
    mode: StringProperty(default='normal')

    def select_drawer(self, context, event) -> draw_handler.View3dDrawHandler:
        handler_count = len(global_vars.draw_handlers)
        # print(handler_count)    #DEBUG
        for i in range(handler_count):
            drawer = global_vars.draw_handlers[handler_count-i-1]
            if drawer.mouse_inside(context, event):
                # print(i)    #DEBUG
                return drawer

    #TODO add quick type search & hide/unhide image & next/prev image
    def modal(self, context, event):
        global drawer
        mode = self.mode
        bhyde_props = context.scene.bhyde_props
        # print(bhyde_props.controlling)  #DEBUG
        # print(event.type)   #DEBUG

        if not context.area or not context.region or context.region.type != 'WINDOW':
            return {'CANCELLED'}
        if event.type in {'RET'}:
            context.area.header_text_set(None)
            return {'FINISHED'}
        if not bhyde_props.controlling:
            drawer = self.select_drawer(context, event)
        if mode == 'normal':
            context.area.header_text_set('RUNNING MODAL')
            if event.type in {'Q', 'ESC'}:
                context.area.header_text_set(None)
                return {'FINISHED'}
            # G = MOVE, S = SCALE mode
            if drawer is None:
                return {'PASS_THROUGH'}
            if event.type == 'G':
                self.mode = 'move_key'
                self._initial_mouse = Vector((event.mouse_x, event.mouse_y))
                self._initial_location = Vector(drawer.draw_pos)
                bhyde_props.controlling = True
            elif event.type == 'S':
                self.mode = 'scale_key'
                self._initial_mouse = Vector((event.mouse_x, event.mouse_y))
                self._initial_size = drawer.size_control
                bhyde_props.controlling = True
            # MOUSE GRAB MODE
            elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                self.mode = 'move'
                self._initial_mouse = Vector((event.mouse_x, event.mouse_y))
                self._initial_location = Vector(drawer.draw_pos)
                bhyde_props.controlling = True
            elif event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
                self.mode = 'scale'
                self._initial_mouse = Vector((event.mouse_region_x, event.mouse_region_y))
                self._initial_size = drawer.size_control
                bhyde_props.controlling = True
            elif event.type == 'C':
                self.mode = 'crop'
                self._initial_mouse = Vector((event.mouse_region_x, event.mouse_region_y))
                bhyde_props.controlling = True
            elif event.type == 'H' and event.value == 'PRESS':
                drawer.remove_handler(to_history=True)
                bhyde_props.controlling = False

        elif mode == 'crop':
            if event.type == 'MOUSEMOVE':
                drawer.crop(context, self._initial_mouse, (event.mouse_region_x, event.mouse_region_y))
                context.area.header_text_set('CROPPING')
                bhyde_props.controlling = True
            if event.type == 'LEFTMOUSE':
                self.mode = 'normal'
                context.area.header_text_set('DONE CROPPING')
                bhyde_props.controlling = False
            elif event.type == 'R':
                drawer.crop_area = (0,0,1,1)
                context.area.header_text_set('CROP RESET')
                self.mode = 'normal'
                bhyde_props.controlling = False
            elif event.type in {'RIGHTMOUSE','ESC'}:
                drawer.crop_area = (0,0,1,1)
                self.mode = 'normal'
                context.area.header_text_set('CANCELLED CROPPING')
                bhyde_props.controlling = False
                if event.type == 'ESC':
                    context.area.header_text_set(None)
                    return {'CANCELLED'}
        elif mode == 'move_key':
            # G = MOVE, S = SCALE mode
            if event.type == 'MOUSEMOVE':
                self.offset = Vector((event.mouse_x, event.mouse_y)) - self._initial_mouse
                self.offset[0] /= context.region.width
                self.offset[1] /= context.region.height
                drawer.draw_pos = self._initial_location + Vector(self.offset)
                context.area.header_text_set("Offset {:.4f} {:.4f}".format(*self.offset))
                bhyde_props.controlling = True
            elif event.type == 'LEFTMOUSE':
                self.mode = 'normal'
                context.area.header_text_set('DONE MOVING')
                bhyde_props.controlling = False
            elif event.type in {'RIGHTMOUSE','ESC'}:
                self.mode = 'normal'
                drawer.draw_pos = self._initial_location
                context.area.header_text_set('CANCELLED MOVING')
                bhyde_props.controlling = False
                if event.type == 'ESC':
                    context.area.header_text_set(None)
                    return {'CANCELLED'}

        elif mode == 'move':
            # MOUSE GRAB MODE
            if event.type == 'MOUSEMOVE':
                self.offset = Vector((event.mouse_x, event.mouse_y)) - self._initial_mouse
                self.offset[0] /= context.region.width
                self.offset[1] /= context.region.height
                drawer.draw_pos = self._initial_location + Vector(self.offset)
                context.area.header_text_set("Offset {:.4f} {:.4f}".format(*self.offset))
                bhyde_props.controlling = True
            elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self.mode = 'normal'
                context.area.header_text_set('DONE MOVING')
                bhyde_props.controlling = False
            elif event.type in {'ESC'}:
                self.mode = 'normal'
                drawer.draw_pos = self._initial_location
                context.area.header_text_set(None)
                bhyde_props.controlling = False
                return {'CANCELLED'}

        elif mode == 'scale':
            # MOUSE GRAB MODE
            if event.type == 'MOUSEMOVE':
                scale = drawer.scale(context, self._initial_mouse, (event.mouse_region_x, event.mouse_region_y), self._initial_size)
                context.area.header_text_set("Scale " + str(scale))
                bhyde_props.controlling = True
            elif event.type == 'RIGHTMOUSE' and event.value == 'RELEASE':
                self.mode = 'normal'
                context.area.header_text_set('DONE SCALING')
                bhyde_props.controlling = False
            elif event.type in {'ESC'}:
                self.mode = 'normal'
                drawer.size_control = self._initial_size
                context.area.header_text_set(None)
                bhyde_props.controlling = False
                return {'CANCELLED'}

        elif mode == 'scale_key':
            # G = MOVE, S = SCALE mode
            if event.type == 'MOUSEMOVE':
                scale = drawer.scale(context, self._initial_mouse, (event.mouse_region_x, event.mouse_region_y), self._initial_size)
                context.area.header_text_set("Offset " + str(offset_sum))
                bhyde_props.controlling = True
            elif event.type == 'LEFTMOUSE':
                self.mode = 'normal'
                context.area.header_text_set('DONE SCALING')
                bhyde_props.controlling = False
            elif event.type in {'RIGHTMOUSE', 'ESC'}:
                self.mode = 'normal'
                drawer.size_control = self._initial_size
                context.area.header_text_set('CANCELLED SCALING')
                bhyde_props.controlling = False
                if event.type == 'ESC':
                    context.area.header_text_set(None)
                    return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type != 'VIEW_3D':
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}
        if not context.region or context.region.type != 'WINDOW':
            return {'CANCELLED'}
        if not len(global_vars.draw_handlers):
            print('No image being drawn')
            return {'CANCELLED'}
        if global_vars.DEBUG:
            print('DEBUG:', 'global_vars.draw_handlers count:', len(global_vars.draw_handlers))
        context.scene.bhyde_props.controlling = False
        self.mode = 'normal'
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(LP_OT_BhydeModal)


def unregister():
    bpy.utils.unregister_class(LP_OT_BhydeModal)
