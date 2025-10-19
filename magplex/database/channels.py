from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

@dataclass
class Channel:
    device_uid: UUID
    channel_id: int
    creation_timestamp: datetime

def get_enabled_channels(conn, device_uid):
    with conn.cursor() as cursor:
        query = """
            select device_uid, channel_id, creation_timestamp
            from channels
            where device_uid = %(device_uid)s
        """
        cursor.execute(query, locals())
        return [Channel(*row) for row in cursor]

def insert_enabled_channel(conn, device_uid, channel_id):
    with conn.cursor() as cursor:
        query = """
            insert into channels (device_uid, channel_id)
            values (%(device_uid)s, %(channel_id)s)
        """
        cursor.execute(query, locals())

def delete_enabled_channel(conn, device_uid, channel_id):
    with conn.cursor() as cursor:
        query = """
            delete from channels
            where device_uid = %(device_uid)s
            and channel_id = %(channel_id)s
        """
        cursor.execute(query, locals())