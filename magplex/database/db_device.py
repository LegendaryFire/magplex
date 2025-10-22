from dataclasses import dataclass
from uuid import UUID
from datetime import datetime


@dataclass
class DeviceProfile:
    device_uid: UUID
    user_uid: UUID
    mac_address: str
    device_id1: str
    device_id2: str
    signature: str
    portal: str
    language: str
    timezone: str
    modified_timestamp: datetime
    creation_timestamp: datetime


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


def get_user_device(conn):
    with conn.cursor() as cursor:
        query = """
            select device_uid, user_uid, mac_address, device_id1, device_id2, signature,
                portal, language, timezone, modified_timestamp, creation_timestamp
            from devices
        """
        cursor.execute(query, locals())
        row = cursor.fetchone()
        return DeviceProfile(*row) if row else None


def get_user_devices(conn, user_uid):
    with conn.cursor() as cursor:
        query = """
            select device_uid, user_uid, mac_address, device_id1, device_id2, signature,
                portal, language, timezone, modified_timestamp, creation_timestamp
            from devices
            where user_uid = %(user_uid)s
        """
        cursor.execute(query, locals())
        return [DeviceProfile(*row) for row in cursor]


def insert_user_device(conn, user_uid, mac_address, device_id1, device_id2, signature, portal, language, timezone):
    with conn.cursor() as cursor:
        query = """
            insert into devices (user_uid, mac_address, device_id1, device_id2, signature, portal, language, timezone)
            values (%(user_uid)s, %(mac_address)s, %(device_id1)s, %(device_id2)s, %(signature)s, %(portal)s,
                    %(language)s, %(timezone)s)
            on conflict (user_uid) do update
            set mac_address = excluded.mac_address, device_id1 = excluded.device_id1, device_id2 = excluded.device_id2,
                signature = excluded.signature, portal = excluded.portal, language = excluded.language,
                timezone = excluded.timezone, modified_timestamp = now()
        """
        cursor.execute(query, locals())
        return None


def insert_channel(conn, device_uid, channel_id, channel_number, channel_name, channel_hd, genre_id,
                   stream_id, channel_enabled=None):
    with conn.cursor() as cursor:
        query = """
            insert into channels (device_uid, channel_id, channel_number, channel_name, channel_hd, genre_number,
                                  stream_id, channel_enabled)
            values (%(device_uid), %(channel_id)s, %(channel_number)s, %(channel_name)s, %(channel_hd)s,
                    %(channel_enabled)s, %(stream_id)s,
                    (select genre_id from genres where device_uid = %(device_uid)s and genre_number = %(genre_number)s))
            on conflict (device_uid, channel_id)
            do update set channel_number = excluded.channel_number, channel_name = excluded.channel_name,
                          channel_hd = excluded.channel_hd, genre_id = excluded.genre_id,
                          stream_id = excluded.stream_id, coalesce(excluded.channel_enabled, channels.channel_enabled)
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


def get_channels(conn, device_uid, channel_enabled=None):
    with conn.cursor() as cursor:
        query = """
            select device_uid, channel_id, channel_number, channel_name, channel_hd, channel_enabled, genre_id,
                   stream_id, creation_timestamp
            from channels
            where device_uid = %(device_uid)s
            and (%(channel_enabled)s is null or channel_enabled = %(channel_enabled)s)
        """
        cursor.execute(query, locals())
        return [Channel(*row) for row in cursor]


def update_channel_status(conn, device_uid, channel_id, channel_enabled):
    with conn.cursor() as cursor:
        query = """
            update channels set channel_enabled = %(channel_enabled)s
            where device_uid = %(device_uid)s
            and channel_id = %(channel_id)s
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

