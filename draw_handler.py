if 'bpy' in locals():
    import importlib
    if 'image_shader' in locals():
        importlib.reload(image_shader)
    if 'global_vars' in locals():
        importlib.reload(global_vars)
    if 'string_utils' in locals():
        importlib.reload(string_utils)
    if 'preferences' in locals():
        importlib.reload(preferences)
import bpy
from . import image_shader
from . import global_vars
from . import string_utils
from . import preferences
from .string_utils import hash_to_path as h2p
import gpu
from mathutils import Vector
import os

class View3dDrawHandler:
    def __init__(self, context, img_source:str, source_type:str):
        if source_type == 'PATH':
            self.hash = ''
            self.img_path = img_source
        elif source_type == 'HASH':
            self.hash = img_source
            self.img_path = h2p(self.hash, preferences.get_prefs(context).db_path, 'IMAGE')
        try:
            self.img = bpy.data.images.load(self.img_path, check_existing=True)
        except:
            if global_vars.DEBUG:
                print('DEBUG:', 'bpy.data.images failed to load file', self.img_path, ':file doesnt exist or unsupported file type')
            self.img = bpy.data.images.load(os.path.join(os.path.dirname(__file__), 'error.jpg'))

        self.img_size = Vector(self.img.size)
        self.movie_frame = 1
        self.size_control = 1
        self.draw_pos = Vector((0,0))
        self.crop_area = (0,0,1,1)
        if self.img.frame_duration == 1:
            self.texture = gpu.texture.from_image(self.img)
            self.type = 'IMAGE'
            bpy.data.images.remove(self.img)
        elif self.img.frame_duration > 1:
            self.texture = None
            self.type = 'MOVIE'

    def draw(self, context):
        rw = context.region.width
        rh = context.region.height
        w, h = self.img_size[0], self.img_size[1]
        size_ratio = (rw+rh)/(w+h)/2.5
        w*=size_ratio*self.size_control
        h*=size_ratio*self.size_control
        self.draw_size = (w,h)
        if self.type == 'IMAGE':
            image_shader.draw_tex(self.texture, self.draw_pos, self.draw_size, self.crop_area)
        elif self.type == 'MOVIE':
            image_shader.draw_tex_movie(self.img, self.movie_frame, self.draw_pos, self.draw_size, self.crop_area)

    def add_handler(self, context, from_history:bool=False):
        self.handler = bpy.types.SpaceView3D.draw_handler_add(self.draw, (context,), 'WINDOW', 'POST_PIXEL')
        if from_history:
            global_vars.draw_handlers.append(self)
            del global_vars.history[self.hash]

    def remove_handler(self, to_history:bool=True):
        try:
            bpy.types.SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')
        except:  # noqa: E722
            if global_vars.DEBUG:
                print('DEBUG:', 'cant remove handler', self.hash)
            pass
        if to_history:
            if global_vars.DEBUG:
                print('DEBUG:', 'moved to history')
            global_vars.history[self.hash] = self
            try:
                global_vars.draw_handlers.remove(self)
            except:
                pass

    def verify_img_datablock(self):
        try:
            self.img.get('name')
            return True
        except: #noqa
            return False

    #DEBUG
    def verify_driver_namespace(self):
        if self in bpy.app.driver_namespace.values():
            print('im still here')
            return True
        print('im lost man')
        return False


    def mouse_inside(self, context, event: bpy.types.Event) -> bool:
        abs_pos = self.get_abs_pos(context)
        min_x = abs_pos[0] + self.crop_area[0] * self.draw_size[0]
        min_y = abs_pos[1] + self.crop_area[1] * self.draw_size[1]
        max_x = abs_pos[0] + self.crop_area[2] * self.draw_size[0]
        max_y = abs_pos[1] + self.crop_area[3] * self.draw_size[1]
        return (
            event.mouse_region_x >= min_x and
            event.mouse_region_y >= min_y and
            event.mouse_region_x <= max_x and
            event.mouse_region_y <= max_y )

    def get_abs_pos(self, context):
        rw = context.region.width
        rh = context.region.height
        draw_pos_x = self.draw_pos[0] * rw 
        draw_pos_y = self.draw_pos[1] * rh
        return (draw_pos_x, draw_pos_y)

    def crop(self, context, initial_mouse, end_mouse):
        abs_pos = self.get_abs_pos(context)
        min_x = min(initial_mouse[0], end_mouse[0])
        max_x = max(initial_mouse[0], end_mouse[0])
        min_y = min(initial_mouse[1], end_mouse[1])
        max_y = max(initial_mouse[1], end_mouse[1])
        min_x = max(min_x, abs_pos[0])
        min_y = max(min_y, abs_pos[1])
        max_x = min(max_x, abs_pos[0] + self.draw_size[0])
        max_y = min(max_y, abs_pos[1] + self.draw_size[1])
        min_x = (min_x - abs_pos[0]) / self.draw_size[0]
        min_y = (min_y - abs_pos[1]) / self.draw_size[1]
        max_x = (max_x - abs_pos[0]) / self.draw_size[0]
        max_y = (max_y - abs_pos[1]) / self.draw_size[1]
        self.crop_area = (min_x, min_y, max_x, max_y)

    def scale(self, context, initial_mouse, end_mouse, initial_size):
        offset = (Vector(end_mouse) - Vector(initial_mouse)) * 0.002
        offset_sum = offset[0] + offset[1]
        self.size_control = initial_size + offset_sum
        return self.size_control

    def update_handler(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self.handler, 'WINDOW')
        self.handler = bpy.types.SpaceView3D.draw_handler_add(self.draw, (context,), 'WINDOW', 'POST_PIXEL')

    # def __del__(self):
    #     self.remove_handler(to_history=False)