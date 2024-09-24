if 'bpy' in locals():
	import importlib
	if 'global_vars' in locals():
		importlib.reload(global_vars)
	if 'draw_handler' in locals():
		importlib.reload(draw_handler)
import bpy
import json
from mathutils import Vector
from . import global_vars
from . import draw_handler

class BH_OT_LoadSceneState(bpy.types.Operator):
	bl_label = 'Load Saved Refs'
	bl_idname = 'bh.load_from_scene'
	bl_options = {'UNDO', 'REGISTER'}

	@classmethod
	def poll(cls, context):
		has_drawing_data = len(json.loads(context.scene.bhyde_props.drawing_state)) > 0
		has_history_data = len(json.loads(context.scene.bhyde_props.history_state)) > 0
		return has_drawing_data or has_history_data

	def execute(self, context):
		load_from_scene(context)
		return {'FINISHED'}

class BH_OT_SaveSceneState(bpy.types.Operator):
	bl_label = 'Save Refs State'
	bl_idname = 'bh.save_to_scene'
	bl_options = {'UNDO', 'REGISTER'}

	def execute(self, context):
		save_to_scene(context)
		return {'FINISHED'}


def save_to_scene(context):
	drawing_data = []
	for drawer in global_vars.draw_handlers:
		drawing_data.append({
			'hash': drawer.hash,
			'movie_frame': drawer.movie_frame,
			'size_control': drawer.size_control,
			'draw_pos': list(drawer.draw_pos),
			'crop_area': drawer.crop_area })
	history_data = []
	for hash in global_vars.history:
		drawer = global_vars.history[hash]
		history_data.append({
			'hash': drawer.hash,
			'movie_frame': drawer.movie_frame,
			'size_control': drawer.size_control,
			'draw_pos': list(drawer.draw_pos),
			'crop_area': drawer.crop_area })
	context.scene.bhyde_props.drawing_state = json.dumps(drawing_data)
	context.scene.bhyde_props.history_state = json.dumps(history_data)

def load_from_scene(context):
	if global_vars.DEBUG:
		print('DEBUG:', '==============loading from scene')
	# clear current drawing state before loading
	for drawer in global_vars.draw_handlers:
		drawer.remove_handler(to_history=False)
	global_vars.draw_handlers.clear()
	if global_vars.DEBUG:
		print('DEBUG:', 'purged global_vars.draw_handlers')
	global_vars.history.clear()
	if global_vars.DEBUG:
		print('DEBUG:', 'hidtory len', len(global_vars.history))

	drawing_data = json.loads(context.scene.bhyde_props.drawing_state)
	history_data = json.loads(context.scene.bhyde_props.history_state)
	for item in drawing_data:
		drawer = draw_handler.View3dDrawHandler(context, item['hash'], 'HASH')
		drawer.movie_frame = item['movie_frame']
		drawer.size_control = item['size_control']
		drawer.draw_pos = Vector( item['draw_pos'] )
		drawer.crop_area = item['crop_area']
		drawer.add_handler(context, from_history=False)
		global_vars.draw_handlers.append(drawer)
	for item in history_data:
		drawer = draw_handler.View3dDrawHandler(context, item['hash'], 'HASH')
		drawer.movie_frame = item['movie_frame']
		drawer.size_control = item['size_control']
		drawer.draw_pos = Vector( item['draw_pos'] )
		drawer.crop_area = item['crop_area']
		if global_vars.DEBUG:
			print('DEBUG:', 'add to history only, nothing to remove')
		drawer.remove_handler(to_history=True)

classes = [
	BH_OT_LoadSceneState,
	BH_OT_SaveSceneState
]

def register():
	for cls in classes:
		bpy.utils.register_class(cls)

def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)
