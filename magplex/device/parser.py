from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from magplex.device.database import Channel, ChannelGuide, Genre


def parse_genre(genre):
    if not isinstance(genre, dict):
        return None

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


def parse_channel_guide(guide, timezone):
    if not isinstance(guide, dict):
        return None

    start_timestamp = datetime.fromtimestamp(int(guide.get('start_timestamp')), tz=ZoneInfo(timezone))
    end_timestamp = datetime.fromtimestamp(int(guide.get('stop_timestamp')), tz=ZoneInfo(timezone))
    if start_timestamp <= end_timestamp:
        return None

    title = guide.get('name') if guide.get('name') != 'No details available' else None
    if title is None:
        return None

    guide = {
        'channel_id': guide.get('ch_id'),
        'title': sanitize_guide_title(title),
        'description': guide.get('descr'),
        'categories':  [c.strip() for c in guide.get('category', str()).split(',') if c.strip()],
        'start_timestamp': round_guide_timestamp(start_timestamp),
        'end_timestamp': round_guide_timestamp(end_timestamp)
    }

    for value in guide.values():
        if value is None:
            return None

    guide.update({
        'device_uid': None,
        'modified_timestamp': None,
        'creation_timestamp': None
    })

    return ChannelGuide(**guide)


def round_guide_timestamp(timestamp: datetime) -> datetime:
    """Round a datetime to the nearest 30-minute mark."""
    difference = timedelta(minutes=timestamp.minute % 30, seconds=timestamp.second, microseconds=timestamp.microsecond)
    timestamp -= difference
    if difference >= timedelta(minutes=15):
        timestamp += timedelta(minutes=30)
    return timestamp


def sanitize_guide_title(title: str):
    if title is None:
        return None
    title = title.replace('\r', ' ').replace('\n', ' ')
    return ' '.join(title.split())
