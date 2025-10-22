import json

import magplex.device.tasks as tasks
from magplex.utilities.database import RedisPool


def _get_channels_cache_key(device_uid):
    return f'magplex:device:{device_uid}:channels'


def get_channels(device_uid):
    cache_conn = RedisPool().get_connection()
    cache_key = _get_channels_cache_key(device_uid)
    channel_list = cache_conn.get(cache_key)
    if channel_list is not None:
        return json.loads(channel_list)
    channel_list = tasks.set_channels()
    cache_conn.set(cache_key, json.dumps(channel_list, default=str), ex=3600)
    return channel_list

