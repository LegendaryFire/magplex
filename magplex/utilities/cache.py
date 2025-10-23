import json

from magplex.utilities.serializers import DataclassEncoder


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
