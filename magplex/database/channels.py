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
    stream_id: int
    creation_timestamp: datetime


def insert_channel(conn, device_uid, channel_id, channel_number, channel_name, channel_hd, channel_enabled,
                   genre_id, stream_id):
    with conn.cursor() as cursor:
        query = """
            insert into channels (device_uid, channel_id, channel_number, channel_name, channel_hd, channel_enabled,
                genre_id, stream_id)
            values (%(device_uid), %(channel_id)s, %(channel_number)s, %(channel_name)s, %(channel_hd)s,
                    %(channel_enabled)s, %(genre_id)s, %(stream_id)s)
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


def delete_channel(conn, device_uid, channel_id):
    with conn.cursor() as cursor:
        query = """
        delete from channels
            where device_uid = %(device_uid)s
            and channel_id = %(channel_id)s
        """
        cursor.execute(query, locals())


def get_enabled_channels(conn, device_uid):
    with conn.cursor() as cursor:
        query = """
            select device_uid, channel_id, channel_number, channel_name, channel_hd, channel_enabled, genre_id,
                   stream_id, creation_timestamp
            from channels
            where device_uid = %(device_uid)s
        """
        cursor.execute(query, locals())
        return [Channel(*row) for row in cursor]


def update_channel_enabled(conn, device_uid, channel_id, channel_enabled):
    with conn.cursor() as cursor:
        query = """
            update channels set channel_enabled = %(channel_enabled)s
            where device_uid = %(device_uid)s
            and channel_id = %(channel_id)s
        """
        cursor.execute(query, locals())
