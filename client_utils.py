import bpy
from typing import Tuple
import hydrus_api

def hydrus_get_metadata(context, tag_list: list, client:hydrus_api.Client) -> Tuple[dict, int]: 
    sort_type = bpy.context.scene.bhyde_props.sort_type
    if sort_type == 'IMPORT_TIME':
        file_sort_type = hydrus_api.FileSortType.IMPORT_TIME
    elif sort_type == 'RANDOM':
        file_sort_type = hydrus_api.FileSortType.RANDOM
    try:
        file_ids = client.search_files(tag_list, file_sort_type=file_sort_type)
    except: #noqa
        print('Connection error/tag_list format error')
        return {}, -1

    ids = file_ids['file_ids']
    if not len(ids):
        print('Found 0 results with provided tags')
        return {}, 0
    print('found %s results with provided tags' % len(ids))
    # print(ids)    #DEBUG
    return client.get_file_metadata(file_ids=ids), len(ids)

def instantiate_client(prefs):
    dns = bpy.app.driver_namespace
    current_client = dns.get('hydrus_client')
    if current_client:
        if prefs.api_key == current_client.access_key and prefs.api_url.rstrip('/') == current_client.api_url:
            return current_client

    client = hydrus_api.Client(prefs.api_key, api_url=prefs.api_url)
    if not client:
        raise Exception('Client instantiating failed')
    dns['hydrus_client'] = client

    try:
        print(client.verify_access_key())
    except:  # noqa: E722
        print('Client initiated but cannot connect to verify_access_key')
    hydrus_tag_list = dns.get('hydrus_tag_list')
    if not hydrus_tag_list or not len(hydrus_tag_list):
        dns['hydrus_tag_list'] = get_tag_list(dns['hydrus_client'])

    return dns['hydrus_client']

def get_tag_list(client: hydrus_api.Client, text=None) -> list[str]:
    tag_list = []
    if text is not None:
        tag = '*:' + text + '*'
    else:
        tag = '*:'
    try:
        tags_json = client.search_tags(tag, None)
    except:     #noqa
        print('Connection Error')
        return tag_list
    tag_dict_list = tags_json['tags']
    for tag_dict in tag_dict_list:
        tag_list.append(tag_dict['value'])
    return tag_list



