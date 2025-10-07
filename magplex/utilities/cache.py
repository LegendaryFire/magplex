import json


def _get_bearer_token_key(instance_id):
    return f'magplex:device:{instance_id}:token'

def _get_channel_ids_key(instance_id):
    return f'magplex:device:{instance_id}:channel:ids'

def _get_channel_key(instance_id: str, channel_id: str) -> str:
    return f"magplex:device:{instance_id}:channel:{channel_id}"

def _get_channel_guide_key(instance_id: str, channel_id: str) -> str:
    return f"magplex:device:{instance_id}:channel:{channel_id}:guide"

def get_bearer_token(conn, instance_id):
    cache_key = _get_bearer_token_key(instance_id)
    token = conn.get(cache_key)
    if token is not None:
        token = token.decode("utf-8")
    return token

def set_bearer_token(conn, instance_id, token):
    cache_key = _get_bearer_token_key(instance_id)
    conn.set(cache_key, token)

def get_all_channel_ids(conn, instance_id):
    cache_key = _get_channel_ids_key(instance_id)
    channel_ids = conn.smembers(cache_key)
    return [cid.decode() for cid in channel_ids]

def insert_channel_id(conn, instance_id, channel_id):
    cache_key = _get_channel_ids_key(instance_id)
    conn.sadd(cache_key, channel_id)

def get_all_channels(conn, instance_id):
    # Get all stored channels.
    channel_ids = get_all_channel_ids(conn, instance_id)
    if not channel_ids:
        return []

    # Get the channel guide key for each channel.
    keys = [_get_channel_key(instance_id, cid) for cid in channel_ids]

    # Get all the channel guides.
    channel_list = conn.mget(keys)

    # Deserialize the data.
    channels = []
    for i, data in enumerate(channel_list):
        if data:
            channels.append(json.loads(data))
    return channels

def insert_channel(conn, instance_id, channel_id, channel):
    expiry = 3 * 3600
    cache_key = _get_channel_key(instance_id, channel_id)
    conn.set(cache_key, json.dumps(channel), ex=expiry)

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

def insert_channel_guide(conn, instance_id, channel_id, channel_guide):
    expiry = 3 * 3600
    cache_key = _get_channel_guide_key(instance_id, channel_id)
    conn.set(cache_key, json.dumps(channel_guide), ex=expiry)