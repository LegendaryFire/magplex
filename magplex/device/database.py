from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Genre:
    device_uid: UUID | None
    genre_id: int
    genre_number: int
    genre_name: str
    modified_timestamp: datetime | None
    creation_timestamp: datetime | None


@dataclass(slots=True)
class Channel:
    device_uid: UUID | None
    channel_id: int
    channel_number: int
    channel_name: str
    channel_hd: bool
    channel_enabled: bool | None
    channel_stale: bool | None
    genre_id: int
    stream_id: int
    modified_timestamp: datetime | None
    creation_timestamp: datetime | None


@dataclass(slots=True)
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


@dataclass(slots=True)
class TaskLog:
    log_uid: UUID
    device_uid: UUID | None
    task_name: str
    started_timestamp: datetime
    completed_timestamp: datetime


def insert_genre(conn, device_uid, genre_id, genre_number, genre_name):
    with conn.cursor() as cursor:
        query = """
            insert into genres (device_uid, genre_id, genre_number, genre_name)
            values (%(device_uid)s, %(genre_id)s, %(genre_number)s, %(genre_name)s)
            on conflict (device_uid, genre_id)
            do update set genre_number = excluded.genre_number, genre_name = excluded.genre_name, 
                modified_timestamp = current_timestamp
        """
        cursor.execute(query, locals())


def get_all_genres(conn, device_uid, channel_enabled=None, channel_stale=None):
    with conn.cursor() as cursor:
        query = """
            select device_uid, genre_id, genre_number, genre_name, modified_timestamp, creation_timestamp
            from genres g
            where g.device_uid = %(device_uid)s
            and (%(channel_enabled)s::bool is null and %(channel_stale)s::bool is null)
            or exists (
                select 1 from channels c
                where c.device_uid = %(device_uid)s
                and c.genre_id = g.genre_id
                and (%(channel_enabled)s::bool is null or %(channel_enabled)s = c.channel_enabled)
                and (%(channel_stale)s::bool is null or %(channel_stale)s = c.channel_stale)
            )
        """
        cursor.execute(query, locals())
        return [Genre(*row) for row in cursor]


def get_enabled_channel_genres(conn, device_uid):
    with conn.cursor() as cursor:
        query = """
            select g.device_uid, g.genre_id, genre_number, genre_name, g.modified_timestamp, g.creation_timestamp
            from genres g
            where g.device_uid = %(device_uid)s
            and exists (
                select 1 from channels c
                where c.device_uid = %(device_uid)s
                and c.genre_id = g.genre_id
                and c.channel_enabled = true
            )
        """
        cursor.execute(query, locals())
        return [Genre(*row) for row in cursor]


def get_disabled_channel_genres(conn, device_uid):
    with conn.cursor() as cursor:
        query = """
            select g.device_uid, g.genre_id, genre_number, genre_name, g.modified_timestamp, g.creation_timestamp
            from genres g
            where g.device_uid = %(device_uid)s
            and exists (
                select 1 from channels c
                where c.device_uid = %(device_uid)s
                and c.genre_id = g.genre_id
                and c.channel_enabled = false
            )
        """
        cursor.execute(query, locals())
        return [Genre(*row) for row in cursor]


def insert_channel(conn, device_uid, channel_id, channel_number, channel_name, channel_hd, genre_id, stream_id):
    with conn.cursor() as cursor:
        query = """
            insert into channels (device_uid, channel_id, channel_number, channel_name, channel_hd, 
                                  genre_id, stream_id, channel_enabled)
            values (%(device_uid)s, %(channel_id)s, %(channel_number)s, %(channel_name)s, %(channel_hd)s,
                %(genre_id)s, %(stream_id)s, false)
            on conflict (device_uid, channel_id)
            do update set channel_number = excluded.channel_number, channel_name = excluded.channel_name,
                channel_hd = excluded.channel_hd, genre_id = excluded.genre_id, stream_id = excluded.stream_id,
                channel_stale = false, modified_timestamp = current_timestamp
        """
        cursor.execute(query, locals())


def get_channel(conn, device_uid, channel_id):
    with conn.cursor() as cursor:
        query = """
            select device_uid, channel_id, channel_number, channel_name, channel_hd, channel_enabled, channel_stale,
                   genre_id, stream_id, modified_timestamp, creation_timestamp
            from channels
            where device_uid = %(device_uid)s
            and channel_id = %(channel_id)s
        """
        cursor.execute(query, locals())
        for row in cursor:
            return Channel(*row)
        return None


def get_channels(conn, device_uid, channel_enabled=None, channel_stale=None, genre_id=None, q=None):
    with conn.cursor() as cursor:
        query = """
            select device_uid, channel_id, channel_number, channel_name, channel_hd, channel_enabled, channel_stale,
                   genre_id, stream_id, modified_timestamp, creation_timestamp
            from channels
            where device_uid = %(device_uid)s
            and (%(channel_enabled)s::bool is null or %(channel_enabled)s = channel_enabled)
            and (%(channel_stale)s::bool is null or %(channel_stale)s = channel_stale)
            and (%(genre_id)s::int is null or %(genre_id)s = genre_id)
            and (%(q)s::varchar is null or channel_name ilike '%%' || %(q)s || '%%')
            order by device_uid, genre_id, channel_number
        """
        cursor.execute(query, locals())
        return [Channel(*row) for row in cursor]


def update_channel(conn, device_uid, channel_id, channel_name=None, channel_hd=None, channel_enabled=None, channel_stale=None):
    with conn.cursor() as cursor:
        query = """
            update channels set channel_name = coalesce(%(channel_name)s, channel_name),
                channel_hd = coalesce(%(channel_hd)s, channel_hd),
                channel_enabled = coalesce(%(channel_enabled)s, channel_enabled),
                channel_stale = coalesce(%(channel_stale)s, channel_stale)
            where device_uid = %(device_uid)s
            and channel_id = %(channel_id)s
        """
        cursor.execute(query, locals())


def update_channels(conn, device_uid, channel_enabled=None, channel_stale=None):
    with conn.cursor() as cursor:
        query = """
            update channels set channel_enabled = coalesce(%(channel_enabled)s, channel_enabled),
                channel_stale = coalesce(%(channel_stale)s, channel_stale)
            where device_uid = %(device_uid)s
        """
        cursor.execute(query, locals())


def get_current_channel_guides(conn, device_uid):
    with conn.cursor() as cursor:
        query = """
            select g.device_uid, g.channel_id, title, categories, description, lower(timestamp_range) as start_timestamp,
                   upper(timestamp_range) as end_timestamp, g.modified_timestamp, g.creation_timestamp
            from channel_guides g
            join channels c on g.device_uid = c.device_uid and g.channel_id = c.channel_id
            where c.channel_enabled = true
            and c.channel_stale = false
            and g.device_uid = %(device_uid)s
            and upper(g.timestamp_range) > current_timestamp
        """
        cursor.execute(query, locals())
        return [ChannelGuide(*row) for row in cursor]


def get_channel_guide(conn, device_uid, channel_id):
    with conn.cursor() as cursor:
        query = """
            select g.device_uid, g.channel_id, title, categories, description, lower(timestamp_range) as start_timestamp,
                   upper(timestamp_range) as end_timestamp, g.modified_timestamp, g.creation_timestamp
            from channel_guides g
            join channels c on g.device_uid = c.device_uid and g.channel_id = c.channel_id
            where g.device_uid = %(device_uid)s
            and g.channel_id = %(channel_id)s
        """
        cursor.execute(query, locals())
        return [ChannelGuide(*row) for row in cursor]


def insert_channel_guide(conn, device_uid, channel_id, title, categories, description, start_timestamp, end_timestamp):
    with conn.cursor() as cursor:
        query = """
            insert into channel_guides (device_uid, channel_id, title, categories, description, timestamp_range)
            values (%(device_uid)s, %(channel_id)s, %(title)s, %(categories)s, %(description)s,
                tstzrange(%(start_timestamp)s, %(end_timestamp)s, '[)'))
            on conflict (device_uid, channel_id, timestamp_range)
            do update set title = excluded.title, categories = excluded.categories, description = excluded.description,
                timestamp_range = excluded.timestamp_range, modified_timestamp = current_timestamp
        """
        cursor.execute(query, locals())


def insert_device_task_log(conn, device_uid, task_name):
    with conn.cursor() as cursor:
        query = """
            insert into task_logs (device_uid, task_name)
            values (%(device_uid)s, %(task_name)s)
            returning log_uid
        """
        cursor.execute(query, locals())
        return cursor.fetchone()[0]


def update_device_task_log(conn, log_uid, completed_timestamp):
    with conn.cursor() as cursor:
        query = """
            update task_logs set completed_timestamp = %(completed_timestamp)s
            where log_uid = %(log_uid)s
        """
        cursor.execute(query, locals())


def delete_device_task_logs(conn, device_uid, is_completed=None):
    with conn.cursor() as cursor:
        query = """
            delete from task_logs
            where  device_uid = %(device_uid)s
            and ((%(is_completed)s::bool is null) or (completed_timestamp is not null) = %(is_completed)s)
        """
        cursor.execute(query, locals())


def get_latest_device_tasks(conn, device_uid, is_completed=None, limit=4):
    with conn.cursor() as cursor:
        query = """
            select log_uid, device_uid, task_name, started_timestamp, completed_timestamp
            from task_logs
            where device_uid = %(device_uid)s
            and ((%(is_completed)s::bool is null) or (completed_timestamp is not null) = %(is_completed)s)
            order by completed_timestamp desc, started_timestamp desc
            limit %(limit)s
        """
        cursor.execute(query, locals())
        return [TaskLog(*row) for row in cursor]


def update_device_id(conn, mac_address, device_id1, device_id2):
    with conn.cursor() as cursor:
        query = """
            update devices set device_id1 = %(device_id1)s, device_id2 = %(device_id2)s
            where mac_address = %(mac_address)s
        """
        cursor.execute(query, locals())