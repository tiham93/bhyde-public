# lsp-ruff settings
# ruff: noqa: E402
bl_info = {
    "name": "Bhyde-testing",
    "author": "Long Phan",
    "version": (0, 1, 5),
    "blender": (3, 6, 0),
    "location": "View3D > UI > LP Tools",
    "description": "Fetch reference images by tags from local Hydrus database",
    "doc_url": "",
    "tracker_url": "",
    "category": "3D View",
}
if 'bpy' in locals():
    import importlib
    if 'modal_controls' in locals():
        importlib.reload(modal_controls)
    if 'client_utils' in locals():
        importlib.reload(client_utils)
    if 'preferences' in locals():
        importlib.reload(preferences)
    if 'draw_handler' in locals():
        importlib.reload(draw_handler)
    if 'string_utils' in locals():
        importlib.reload(string_utils)
    if 'global_vars' in locals():
        importlib.reload(global_vars)
    if 'save_state' in locals():
        importlib.reload(save_state)
import os
import bpy
from . import string_utils
from . import client_utils
from . import preferences
from . import modal_controls
from . import draw_handler
from . import save_state
from . import global_vars
from .global_vars import preview_collections
from .global_vars import draw_handlers
from .global_vars import searching

from math import floor, ceil 
from random import random  
import bpy.utils.previews  

class LP_PT_BhydePanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Bhyde"
    bl_category = "LP Tools"

    def draw(self, context):
        layout = self.layout
        layout.row().operator(modal_controls.LP_OT_BhydeModal.bl_idname, text='Start Modal Controls')
        layout.row().prop(context.scene.bhyde_props, 'select_mode', expand=True)
        layout.row().prop(context.scene.bhyde_props, 'project_tag', text='Project Tag')
        layout.row().prop(context.scene.bhyde_props, 'search_1', text='Hydrus Tags 1')
        layout.row().prop(context.scene.bhyde_props, 'search_2', text='Hydrus Tags 2')
        if context.scene.bhyde_props.select_mode == 'MNL':
            layout.row().prop(context.scene.bhyde_props, 'search_limit', text='Limit Results')
        layout.row().prop(context.scene.bhyde_props, 'sort_type')
        row = layout.row()
        row.prop(context.scene.bhyde_props, 'search_auto_wildcard', text='Auto Wildcard', toggle=1)
        row.prop(context.scene.bhyde_props, 'search_all_namespaces', text='All Namespaces', toggle=1)
        row = layout.row()
        row.active_default = True
        row.operator(LP_OT_RunBhyde.bl_idname, text='Search')
        layout.row().operator(save_state.BH_OT_LoadSceneState.bl_idname, text='Load State')
        layout.row().operator(save_state.BH_OT_SaveSceneState.bl_idname, text='Save State')
        if context.scene.bhyde_props.select_mode == 'MNL':
            layout.row().template_icon_view(context.scene.bhyde_props, 'select_item')
        if len( global_vars.history ):
            layout.row().label(text='History')
            layout.row().template_icon_view(context.scene.bhyde_props, 'select_history')

class LP_OT_RunBhyde(bpy.types.Operator):
    bl_label='Search Hydrus images by tags'
    bl_idname='view3d.run_bhyde'
    bl_options={'UNDO','REGISTER','INTERNAL'}

    def execute(self, context):
        global searching

        client = bpy.app.driver_namespace.get('hydrus_client')
        if not client:
            print('Hydrus Client not found. Initiating...')
            client = client_utils.instantiate_client(preferences.get_prefs(context))

        props = context.scene.bhyde_props
        if props.select_mode == 'MNL':
            searching = True
            return {'FINISHED'}

        if props.select_mode == 'RND':
            tag_list, tag_list_str = string_utils.process_querries(context)
            # print('tag list sent:', tag_list)   #DEBUG
            metadata, count = client_utils.hydrus_get_metadata(context, tag_list, client)
            if count == -1:
                self.report({'ERROR'}, 'Connection Error')
                return {'CANCELLED'}
            if count == 0:
                self.report({'INFO'}, 'No results')
                return {'FINISHED'}
            id = floor(random()*count)
            print('picked id:', id)     #DEBUG
            hash = metadata['metadata'][id]['hash']
            print('hash:', hash)        #DEBUG
            draw_images(context, [hash,])

        return {'FINISHED'}

# create drawer object for each image and store in global_vars.draw_handlers
def draw_images(context, hashes:list):
    if not len(hashes):
        if global_vars.DEBUG:
            print('DEBUG:', 'nothing to draw')
        return

    #TODO only processing 1st image hash
    drawer = draw_handler.View3dDrawHandler(context, hashes[0], 'HASH')
    drawer.add_handler(context, from_history=False)
    draw_handlers.append(drawer)

# scene props callback: panel draw > enum > enum items?
def enum_thumbnails_callback(self, context):
    global searching
    if context is None:
        return []

    bhyde_props = context.scene.bhyde_props
    if bhyde_props.select_mode != 'MNL':
        return []

    #TODO add history: store previous searches/preview collections in preview_collections 
    pcol = preview_collections['main']
    if not searching:
        return pcol.select_item
    tag_list, tag_list_str = string_utils.process_querries(context)
    if pcol.tag_list_str == tag_list_str and bhyde_props.sort_type != 'RANDOM':
        searching = False
        return pcol.select_item

    client = bpy.app.driver_namespace.get('hydrus_client')
    if not client:
        print("Hydrus Client not found. Initiating...")
        client = client_utils.instantiate_client(preferences.get_prefs(context))

    metadata, count = client_utils.hydrus_get_metadata(context, tag_list, client)

    #CONTINUE HERE uncomment and continue
    search_limit = bhyde_props.search_limit
    if search_limit > 0:
        if count > search_limit:
    #         page_count = ceil(count/search_limit)
    #         page_id = bhyde_props.page_id
            count = search_limit

    enum_items = []
    for i in range(count):
        hash = metadata['metadata'][i]['hash']
        # print('thumb hash', i, hash)        #DEBUG
        icon = pcol.get(hash)
        if not icon:
            thumbpath = string_utils.hash_to_path(hash, preferences.get_prefs(context).db_path, 'THUMBNAIL')
            icon = pcol.load(hash, thumbpath, 'IMAGE')        #OLD
            #TEST faster thumbnail loading
            # icon = pcol.new(hash)
            # icon_source = bpy.data.images.load(thumbpath)
            # icon.icon_size = icon_source.size
            # icon.icon_pixels_float = icon_source.pixels
            # # icon.is_icon_custom = True
            # bpy.data.images.remove(icon_source)
        enum_items.append((hash, hash, '', icon.icon_id, i))

    if count != -1:     # dont update history if connection error
        pcol.select_item = enum_items
        pcol.tag_list_str = tag_list_str
    searching = False
    return pcol.select_item

# scene props callback: panel draw > enum > enum items > select?
def select_item_callback(self, context):
    if context.scene.bhyde_props.select_mode != 'MNL':
        print('Select mode is not manual. Skipping..')
        return
    hash = context.scene.bhyde_props.select_item
    draw_images(context, [hash,])

def select_item_from_history_callback(self, context):
    if context.scene.bhyde_props.select_mode != 'MNL':
        print('Select mode is not manual. Skipping..')
        return
    hash = context.scene.bhyde_props.select_history
    global_vars.history[hash].add_handler(context, from_history=True)

def force_draw_update_callback(self, context):
    pass

def tag_search_fuzzy_callback(self, context, edit_text):
    # regex search over large tag db too slow
    # return fuzzy_finder.fuzzy_match_result(edit_text, bpy.app.driver_namespace['hydrus_tag_list'], 15)
    # use hydrus_api for this instead
    tags = edit_text.split(',')
    active_tag = tags[len(tags)-1].strip() 
    tags = tags[0:-1]
    # print(tags)                           #DEBUG
    # print('active tag', active_tag)       #DEBUG
    client = bpy.app.driver_namespace.get('hydrus_client')
    if not client:
        client = client_utils.instantiate_client(preferences.get_prefs(context))
    suggestions = client_utils.get_tag_list(client, active_tag)
    result = []
    for suggestion in suggestions:
        result.append(','.join(tags) + ', ' + suggestion if len(tags) > 0 else suggestion)
    # print(result)                         #DEBUG
    return result

def enum_history_callback(self, context):
    enum_items = []
    pcol = preview_collections['main']
    if len( global_vars.history ) == len(pcol.select_history):
        return pcol.select_history
    for i, hash in enumerate(global_vars.history):
        # print('history hash:', hash)    #DEBUG
        icon = pcol.get(hash)
        if not icon:
            thumbpath = string_utils.hash_to_path(hash, preferences.get_prefs(context).db_path, 'THUMBNAIL')
            icon = pcol.load(hash, thumbpath, 'IMAGE')
        enum_items.append((hash, hash, '', icon.icon_id, i))
    pcol.select_history = enum_items
    return enum_items

class BhydeProps(bpy.types.PropertyGroup):
    controlling: bpy.props.BoolProperty(default=False, update=force_draw_update_callback)
    search_auto_wildcard: bpy.props.BoolProperty(default=True)
    search_all_namespaces: bpy.props.BoolProperty(default=True)
    search_limit: bpy.props.IntProperty(default=50)
    search_1: bpy.props.StringProperty(search=tag_search_fuzzy_callback)
    search_2: bpy.props.StringProperty(search=tag_search_fuzzy_callback)
    project_tag: bpy.props.StringProperty(search=tag_search_fuzzy_callback)
    drawing_state: bpy.props.StringProperty(default='[]')
    history_state: bpy.props.StringProperty(default='[]')
    
    select_mode: bpy.props.EnumProperty(
        name = 'Image Select Mode',
        description = 'Random or Manual Selection',
        items = {
            ('RND', 'Random', 'Select one random image from result'),
            ('MNL', 'Manual', 'Select images to draw manually')},
        default = 'MNL')
    select_item: bpy.props.EnumProperty(
        name = 'Select Item',
        items = enum_thumbnails_callback,
        update = select_item_callback )
    select_history: bpy.props.EnumProperty(
        name = 'History',
        items = enum_history_callback,
        update = select_item_from_history_callback )
    sort_type: bpy.props.EnumProperty(
        name = 'Sort Result',
        items = {
            ('IMPORT_TIME', 'Import Time', ''),
            ('RANDOM', 'Random', ''),
        },
        default = 'RANDOM' )


classes = [
    BhydeProps,
    LP_PT_BhydePanel, 
    LP_OT_RunBhyde,
]    

def register():
    print('\n===========================')
    print('Registering LP Addon: bhyde')
    preferences.register()
    prefs = preferences.get_prefs(bpy.context)
    for cls in classes:
        bpy.utils.register_class(cls)
    save_state.register()
    modal_controls.register()
    bpy.types.Scene.bhyde_props = bpy.props.PointerProperty(type=BhydeProps)

    pcol = bpy.utils.previews.new()
    pcol.tag_list_str = ''
    pcol.select_item = ()
    pcol.select_history = ()
    preview_collections['main'] = pcol
    client_utils.instantiate_client(prefs)
    print('api_key:', prefs.api_key)
    print('api_url:', prefs.api_url)
    print('db_path:', prefs.db_path)
    print('===========================\n')

def unregister():
    print('\n===========================')
    print('Unregistering LP Addon: bhyde')
    for cls in classes:
        bpy.utils.unregister_class(cls)
    save_state.unregister()
    modal_controls.unregister()
    preferences.unregister()
    del bpy.types.Scene.bhyde_props

    for pcol in preview_collections.values():
        bpy.utils.previews.remove(pcol)
    preview_collections.clear()
    for drawer in draw_handlers:
        drawer.remove_handler(to_history=False)
    draw_handlers.clear()
    global_vars.history.clear()
    print('===========================\n')

if __name__ == '__main__':
    register()