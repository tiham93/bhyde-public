import bpy
import os
from typing import Tuple

def process_querries(context) -> Tuple[list, str]:
    tag_list = []
    tag_list_str = ''
    if context is None:
        return tag_list, tag_list_str

    bhyde_props = context.scene.bhyde_props
    pj_tag = bhyde_props.project_tag
    string1 = bhyde_props.search_1
    string2 = bhyde_props.search_2

    # print('tag string 1:', string1) #DEBUG
    if string1:
        tag_list.extend(string1.split(','))
    # print('tag string 2:', string2) #DEBUG
    if string2:
        tag_list.extend(string2.split(','))
    # print('project tag:', pj_tag)   #DEBUG
    if pj_tag:
        tag_list.append(bhyde_props.project_tag)
    # print('tag list initial:', tag_list)    #DEBUG

    # strip whitespaces at start and end of tags (from separator ', ' etc.)
    for i in range(len(tag_list)):
        tag_list[i] = tag_list[i].strip()
    # print('tag list stripped:', tag_list)   #DEBUG

    # remove empty elements (from empty querries, etc.)
    i = 0
    while i < len(tag_list):
        if tag_list[i] == '':
            tag_list.remove(tag_list[i])
        else:
            i += 1
    # print('tag list removed empty:', tag_list)  #DEBUG

    # dedupe and sort tag list then convert to tag_list_str (used to indentify and avoid regenerate the same search result enum)
    tag_list = sorted(list(dict.fromkeys(tag_list)))
    # print('tag list deduped & sorted:', tag_list)   #DEBUG
    if bhyde_props.search_auto_wildcard:
        for i in range(len(tag_list)):
            if not tag_list[i] == pj_tag:
                tag_list[i] += '*'
    if bhyde_props.search_all_namespaces:
        for i in range(len(tag_list)):
            if not tag_list[i] == pj_tag:
                tag_list[i] = '*:' + tag_list[i]
    print('tag list w/ wildcards & namespaces:', tag_list)   #DEBUG
    tag_list_str = ', '.join(tag_list)
    # print('tag_list_str:', tag_list_str)    #DEBUG

    return tag_list, tag_list_str

def hash_to_path(hash:str, db_path:str, type:str) -> str | None:
    #TODO cleanup db_path to proper usable format
    if not os.path.exists(db_path):
        raise ValueError('Invalid db_path')
    if type == 'THUMBNAIL':
        exts = ['.thumbnail']
        db_subfolder_prefix = 't'
    elif type == 'IMAGE':
        exts = list(bpy.path.extensions_image)
        exts.extend(list(bpy.path.extensions_movie))
        db_subfolder_prefix = 'f'
    else:
        raise ValueError('Wrong image type for hash_to_path func')
    for ext in exts:
        path_check = db_path + db_subfolder_prefix + hash[0:2] + '/' + hash + ext
        if os.path.exists(path_check):
            return path_check
    else:
        print('Failed path check: not found in database or not an image')
        return


