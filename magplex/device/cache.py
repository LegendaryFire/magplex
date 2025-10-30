import json

import magplex.device.tasks as tasks
from magplex.device.database import Channel
from magplex.utilities.serializers import DataclassEncoder


def _get_device_timeout_key(instance_id):
    return f'magplex:device:{instance_id}:timeout'


def _get_access_token_key(device_uid):
    return f'magplex:device:{device_uid}:token'


def _get_access_random_key(device_uid):
    return f'magplex:device:{device_uid}:random'


def _get_channels_cache_key(device_uid):
    return f'magplex:device:{device_uid}:channels'


def set_device_timeout(conn, instance_id):
    cache_key = _get_device_timeout_key(instance_id)
    expiry = 30
    conn.set(cache_key, int(True), ex=expiry, nx=True)


def get_device_timeout(conn, instance_id):
    cache_key = _get_device_timeout_key(instance_id)
    return conn.exists(cache_key)


def expire_channels(conn, device_uid):
    cache_key = _get_channels_cache_key(device_uid)
    conn.delete(cache_key)


def get_access_token(conn, device_uid):
    cache_key = _get_access_token_key(device_uid)
    token = conn.get(cache_key)
    return token


def set_access_token(conn, device_uid, token):
    cache_key = _get_access_token_key(device_uid)
    conn.set(cache_key, token, ex=3600)  # Auto-expire every hour.


def get_access_random(conn, device_uid):
    cache_key = _get_access_random_key(device_uid)
    token = conn.get(cache_key)
    return token


def set_access_random(conn, device_uid, random):
    cache_key = _get_access_random_key(device_uid)
    conn.set(cache_key, random, ex=3600)


def expire_access(conn, device_uid):
    access_cache_key = _get_access_token_key(device_uid)
    random_cache_key = _get_access_random_key(device_uid)
    conn.delete([access_cache_key, random_cache_key])


# TODO: Rewrite everything below this.
def _get_channel_ids_key(instance_id):
    return f'magplex:device:{instance_id}:channel:ids'

def _get_channel_guide_key(instance_id: str, channel_id: str) -> str:
    return f"magplex:device:{instance_id}:channel:{channel_id}:guide"

def get_all_channel_ids(conn, instance_id):
    cache_key = _get_channel_ids_key(instance_id)
    channel_ids = conn.smembers(cache_key)
    return [cid for cid in channel_ids]

def insert_channel_id(conn, instance_id, channel_id):
    cache_key = _get_channel_ids_key(instance_id)
    conn.sadd(cache_key, channel_id)


def get_all_channel_guides(conn, instance_id):
    # Get all stored channels.
    channel_ids = get_all_channel_ids(conn, instance_id)
    if not channel_ids:
        return []

    # Get the channel guide key for each channel.
    keys = [_get_channel_guide_key(instance_id, cid) for cid in channel_ids]

    # Get all the channel guides.
    channel_guide_list = conn.mget(keys)

    # Deserialize the data.
    channel_guides = []
    for i, data in enumerate(channel_guide_list):
        if data:
            channel_guides.append(json.loads(data))
    return channel_guides

def get_channel_guide(conn, instance_id, channel_id):
    cache_key = _get_channel_guide_key(instance_id, channel_id)
    channel_guide = conn.get(cache_key)
    channel_guide = json.loads(channel_guide) if channel_guide else None
    return channel_guide

def insert_channel_guide(conn, instance_id, channel_id, channel_guide):
    expiry = 3 * 3600
    cache_key = _get_channel_guide_key(instance_id, channel_id)
    conn.set(cache_key, json.dumps(channel_guide, cls=DataclassEncoder), ex=expiry)
