from dataclasses import dataclass
from uuid import UUID
from datetime import datetime


@dataclass
class Channel:
    device_uid: UUID
    channel_id: int
    channel_number: int
    channel_name: str
    channel_hd: bool
    channel_enabled: bool
    genre_id: int
    genre_name: str
    stream_id: int
    creation_timestamp: datetime


@dataclass
class ChannelGuide:
    device_uid: UUID
    channel_id: int
    title: str
    categories: list
    description: str
    start_timestamp: datetime
    end_timestamp: datetime
    modified_timestamp: datetime
    creation_timestamp: datetime


def insert_channel(conn, device_uid, channel_id, channel_number, channel_name, channel_hd, genre_number, stream_id):
    with conn.cursor() as cursor:
        query = """
            insert into channels (device_uid, channel_id, channel_number, channel_name, channel_hd, genre_id, stream_id)
            values (%(device_uid)s, %(channel_id)s, %(channel_number)s, %(channel_name)s, %(channel_hd)s,
                (select genre_id from genres where device_uid = %(device_uid)s and genre_number = %(genre_number)s),
                %(stream_id)s)
            on conflict (device_uid, channel_id)
            do update set channel_number = excluded.channel_number, channel_name = excluded.channel_name,
                channel_hd = excluded.channel_hd, genre_id = excluded.genre_id, stream_id = excluded.stream_id
        """
        cursor.execute(query, locals())


def get_channel(conn, device_uid, channel_id):
    with conn.cursor() as cursor:
        query = """
            select device_uid, channel_id, channel_number, channel_name, channel_hd, channel_enabled,
                genre_id, stream_id
            from channels
            where device_uid = %(device_uid)s
            and channel_id = %(channel_id)s
        """
        cursor.execute(query, locals())
        return [Channel(*row) for row in cursor]


def get_all_channels(conn, device_uid):
    with conn.cursor() as cursor:
        query = """
            select c.device_uid, channel_id, channel_number, channel_name, channel_hd, channel_enabled, g.genre_id,
                   g.genre_name, stream_id, c.creation_timestamp
            from channels c join genres g on c.genre_id = g.genre_id and c.device_uid = g.device_uid
            where c.device_uid = %(device_uid)s
        """
        cursor.execute(query, locals())
        return [Channel(*row) for row in cursor]


def get_enabled_channels(conn, device_uid):
    with conn.cursor() as cursor:
        query = """
            select c.device_uid, channel_id, channel_number, channel_name, channel_hd, channel_enabled, g.genre_id,
                   g.genre_name, stream_id, c.creation_timestamp
            from channels c join genres g on c.genre_id = g.genre_id and c.device_uid = g.device_uid
            where c.device_uid = %(device_uid)s
            and channel_enabled = true
        """
        cursor.execute(query, locals())
        return [Channel(*row) for row in cursor]


def get_disabled_channels(conn, device_uid):
    with conn.cursor() as cursor:
        query = """
            select c.device_uid, channel_id, channel_number, channel_name, channel_hd, channel_enabled, g.genre_id,
                   g.genre_name, stream_id, c.creation_timestamp
            from channels c join genres g on c.genre_id = g.genre_id and c.device_uid = g.device_uid
            where c.device_uid = %(device_uid)s
            and channel_enabled = false
        """
        cursor.execute(query, locals())
        return [Channel(*row) for row in cursor]


def update_channel_status(conn, device_uid, channel_id):
    with conn.cursor() as cursor:
        query = """
            update channels set channel_enabled = not channel_enabled
            where device_uid = %(device_uid)s
            and channel_id = %(channel_id)s
        """
        cursor.execute(query, locals())


def update_channels_status(conn, device_uid, channels_enabled):
    with conn.cursor() as cursor:
        query = """
            update channels set channel_enabled = %(channels_enabled)s
            where device_uid = %(device_uid)s
        """
        cursor.execute(query, locals())


def delete_channel(conn, device_uid, channel_id):
    with conn.cursor() as cursor:
        query = """
            delete from channels
                where device_uid = %(device_uid)s
                and channel_id = %(channel_id)s
        """
        cursor.execute(query, locals())


def get_channel_guides(conn, device_uid):
    with conn.cursor() as cursor:
        query = """
            select device_uid, channel_id, title, categories, description lower(timestamp_range) as start_timestamp,
                   upper(timestamp_range) as end_timestamp, modified_timestamp, creation_timestamp
            from channel_guides g
            join channels c on g.device_uid = c.device_uid and g.channel_id = c.channel_id
            where c.channel_enabled = true
            and g.device_uid = %(device_uid)s
        """
    cursor.execute(query, locals())
    return cursor.fetchall()


def insert_channel_guide(conn, device_uid, channel_id, title, categories, description, start_timestamp, end_timestamp):
    with conn.cursor() as cursor:
        query = """
            insert into channel_guides (device_uid, channel_id, title, categories, description, timestamp_range)
            values (%(device_uid)s, %(channel_id)s, %(title)s, %(categories)s, %(description)s,
                   tsrange(%(start_timestamp)s, %(end_timestamp)s, '['))
            on conflict (device_uid, channel_id, timestamp_range)
            do update set title = excluded.title, categories = excluded.categories, description = excluded.description,
                modified_timestamp = excluded.modified_timestamp
        """
        cursor.execute(query, locals())