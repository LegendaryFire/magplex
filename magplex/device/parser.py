from magplex.device.database import Channel, Genre


def parse_genre(genre):
    genre = {
        'genre_id': genre.get('id'),
        'genre_number': genre.get('number'),
        'genre_name': genre.get('title')
    }

    for value in genre.values():
        if value is None:
            return None

    genre.update({
        'device_uid': None,
        'modified_timestamp': None,
        'creation_timestamp': None
    })

    return Genre(**genre)



def parse_channel(channel, genres):
    if not isinstance(channel, dict):
        return None

    available_genres = [g.genre_id for g in genres]
    genre_id = channel.get('tv_genre_id')
    if genre_id is not None and int(genre_id) not in available_genres:
        return None

    channel = {
        'channel_id': int(channel.get('id')) if channel.get('id') else None,
        'channel_number': int(channel.get('number')) if channel.get('number') else None,
        'channel_name': channel.get('name'),
        'channel_hd': channel.get('hd', '0') == '1',
        'genre_id': int(channel.get('tv_genre_id')) if channel.get('tv_genre_id') else None,
        'stream_id': channel.get('cmds', [{}])[0].get('id')
    }

    for value in channel.values():
        if value is None:
            return None

    channel.update({
        'device_uid': None,
        'channel_enabled': None,
        'channel_stale': None,
        'modified_timestamp': None,
        'creation_timestamp': None
    })

    return Channel(**channel)
