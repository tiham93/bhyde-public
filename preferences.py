if 'bpy' in locals():
	import importlib
	if 'client_utils' in locals():
		importlib.reload(client_utils)
import bpy
from . import client_utils
import os
if 'bpy' not in locals():
	import importlib
	if 'client_utils' in locals():
		importlib.reload(client_utils)

def instantiate_client_callback(self, context):
	prefs=get_prefs(context)
	client_utils.instantiate_client(prefs)

class LP_PF_AddonPreferences(bpy.types.AddonPreferences):
	bl_idname = __package__
	api_key: bpy.props.StringProperty(update=instantiate_client_callback)
	api_url: bpy.props.StringProperty(update=instantiate_client_callback)
	db_path: bpy.props.StringProperty(subtype='DIR_PATH')

	def read_json(self):
		import json
		json_file_path = os.path.dirname(os.path.abspath(__file__)) + '/preferences.json'
		if not os.path.exists(json_file_path):
			return
		# print('\n============DEBUG==============')
		# print (json_file_path)
		# print('=============DEBUG=============\n')
		with open(os.path.abspath(json_file_path), 'r') as file:
			data = json.load(file)
			self['api_key'] = data['api_key']
			self['api_url'] = data['api_url']
			self['db_path'] = data['db_path']

	def write_json(self):
		import json
		json_file_path = os.path.dirname(os.path.abspath(__file__)) + '/preferences.json'
		data = {}
		data["api_key"] = self.api_key
		data["api_url"] = self.api_url
		data["db_path"] = self.db_path
		json_data = json.dumps(data, indent=4)
		with open(json_file_path,'w') as file:
			file.write(json_data)

	def draw(self, context):
		layout = self.layout
		if (not self.api_key) and (not self.api_url) and (not self.db_path):
			self.read_json()
		layout.row().prop(self, 'api_key')
		layout.row().prop(self, 'api_url')
		layout.row().prop(self, 'db_path')

def get_prefs(context) -> LP_PF_AddonPreferences:
	return context.preferences.addons[__package__].preferences

classes = [
	LP_PF_AddonPreferences
]

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	get_prefs(bpy.context).read_json()

def unregister():
	get_prefs(bpy.context).write_json()
	for cls in classes:
		bpy.utils.unregister_class(cls)
