from magplex.device.database import Channel


def parse_channel(channel):
    if not isinstance(channel, dict):
        return None

    channel = {
        'channel_id': channel.get('id'),
        'channel_number': channel.get('number'),
        'channel_name': channel.get('name'),
        'channel_hd': channel.get('hd', '0') == '1',
        'genre_number': channel.get('tv_genre_id'),
        'stream_id': channel.get('cmds', [{}])[0].get('id')
    }

    for value in channel.values():
        if value is None:
            return None

    channel.update({
        'device_uid': None,
        'channel_enabled': None,
        'channel_stale': None,
        'genre_name': None,
        'modified_timestamp': None,
        'creation_timestamp': None
    })

    return Channel(**channel)
