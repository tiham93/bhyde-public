import bgl
import bpy
import os
import gpu
from gpu_extras.batch import batch_for_shader

with open(os.path.dirname(__file__) + '/vertex.glsl', 'r') as file:
    vertex_shader = file.read()
with open(os.path.dirname(__file__) + '/frag.glsl', 'r') as file:
    frag_shader = file.read()

shader = gpu.types.GPUShader(vertex_shader, frag_shader)

plane_verts = ( (0,0), (1,0), (1,1), (0,1) )
batch = batch_for_shader(shader, 'TRI_FAN', { 'pos': plane_verts })

def draw_tex(tex, pos, draw_size, crop_area = (0,0,1,1)):
    shader.bind()
    region = bpy.context.region
    # region_size = (1000,1000)
    region_size = (region.width, region.height) 
    shader.uniform_sampler('image', tex)
    shader.uniform_float('cropArea', crop_area)
    shader.uniform_float('regionSize', region_size)
    shader.uniform_float('drawSize', draw_size)
    shader.uniform_float('drawPos', pos)
    batch.draw(shader)
    pass
    
def draw_tex_movie(img_block, frame, pos, draw_size, crop_area = (0,0,1,1)):
    shader.bind()
    img_block.gl_load(frame=bpy.context.scene.frame_current)
    bgl.glActiveTexture(bgl.GL_TEXTURE0)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, img_block.bindcode)
    img_block.update()
    region = bpy.context.region
    region_size = (region.width, region.height)
    shader.uniform_float('cropArea', crop_area)
    shader.uniform_float('regionSize', region_size)
    shader.uniform_float('drawSize', draw_size)
    shader.uniform_float('drawPos', pos)
    batch.draw(shader)