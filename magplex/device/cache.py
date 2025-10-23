import json

import magplex.device.tasks as tasks


def _get_device_timeout_key(instance_id):
    return f'magplex:device:{instance_id}:timeout'


def _get_bearer_token_key(instance_id):
    return f'magplex:device:{instance_id}:token'


def _get_channels_cache_key(device_uid):
    return f'magplex:device:{device_uid}:channels'


def set_device_timeout(conn, instance_id):
    cache_key = _get_device_timeout_key(instance_id)
    expiry = 30
    conn.set(cache_key, int(True), ex=expiry, nx=True)


def get_device_timeout(conn, instance_id):
    cache_key = _get_device_timeout_key(instance_id)
    return conn.exists(cache_key) == 0


def get_channels(conn, device_uid):
    cache_key = _get_channels_cache_key(device_uid)
    channel_list = conn.get(cache_key)
    if channel_list is not None:
        return json.loads(channel_list)
    channel_list = tasks.set_channels()
    conn.set(cache_key, json.dumps(channel_list, default=str), ex=3600)
    return channel_list


def expire_channels(conn, device_uid):
    cache_key = _get_channels_cache_key(device_uid)
    conn.delete(cache_key)


def get_bearer_token(conn, instance_id):
    cache_key = _get_bearer_token_key(instance_id)
    token = conn.get(cache_key)
    return token


def set_bearer_token(conn, instance_id, token):
    cache_key = _get_bearer_token_key(instance_id)
    conn.set(cache_key, token)
