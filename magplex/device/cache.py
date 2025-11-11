def _get_device_timeout_key(instance_id):
    return f'magplex:device:{instance_id}:timeout'


def _get_device_access_token_key(device_uid):
    return f'magplex:device:{device_uid}:token'


def _get_device_access_random_key(device_uid):
    return f'magplex:device:{device_uid}:random'


def set_device_timeout(conn, instance_id):
    cache_key = _get_device_timeout_key(instance_id)
    expiry = 30
    conn.set(cache_key, int(True), ex=expiry, nx=True)


def get_device_timeout(conn, instance_id):
    cache_key = _get_device_timeout_key(instance_id)
    return conn.exists(cache_key)


def get_device_access_token(conn, device_uid):
    cache_key = _get_device_access_token_key(device_uid)
    token = conn.get(cache_key)
    return token


def set_device_access_token(conn, device_uid, token):
    cache_key = _get_device_access_token_key(device_uid)
    conn.set(cache_key, token, ex=3600)  # Auto-expire every hour.


def get_device_access_random(conn, device_uid):
    cache_key = _get_device_access_random_key(device_uid)
    token = conn.get(cache_key)
    return token


def set_device_access_random(conn, device_uid, random):
    cache_key = _get_device_access_random_key(device_uid)
    conn.set(cache_key, random, ex=3600)


def expire_device_access(conn, device_uid):
    access_cache_key = _get_device_access_token_key(device_uid)
    random_cache_key = _get_device_access_random_key(device_uid)
    conn.delete(access_cache_key, random_cache_key)
