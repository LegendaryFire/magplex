from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    user_uid: UUID
    username: str
    modified_timestamp: datetime
    creation_timestamp: datetime


@dataclass
class UserSession:
    session_uid: UUID
    user_uid: UUID
    ip_address: str
    expiration_timestamp: datetime
    creation_timestamp: datetime


@dataclass
class UserApi:
    api_key: UUID
    user_uid: UUID
    creation_timestamp: datetime


@dataclass
class DeviceProfile:
    device_uid: UUID
    user_uid: UUID
    mac_address: str
    device_id1: str
    device_id2: str
    signature: str
    portal: str
    timezone: str
    modified_timestamp: datetime
    creation_timestamp: datetime


def validate_user(conn, username, password):
    with conn.cursor() as cursor:
        query = """
            select user_uid, username, modified_timestamp, creation_timestamp
            from users
            where username = %(username)s
            and password = crypt(%(password)s, password)
        """
        cursor.execute(query, locals())
        row = cursor.fetchone()
        return User(*row) if row else None


def get_user(conn, user_uid):
    with conn.cursor() as cursor:
        query = """
            select user_uid, username, modified_timestamp, creation_timestamp
            from users
            where user_uid = %(user_uid)s
        """
        cursor.execute(query, locals())
        row = cursor.fetchone()
        return User(*row) if row else None


def update_username(conn, user_uid, username):
    with conn.cursor() as cursor:
        query = """
            update users
            set username = %(username)s
            where user_uid = %(user_uid)s
        """
        cursor.execute(query, locals())


def update_password(conn, user_uid, password):
    with conn.cursor() as cursor:
        query = """
            update users
            set password = crypt(%(password)s, gen_salt('bf'))
            where user_uid = %(user_uid)s
        """
        cursor.execute(query, locals())

        # Expire any existing sessions, forcing any sessions for that user to reauthenticate.
        query = """
            update user_sessions set expiration_timestamp = current_timestamp
            where user_uid = %(user_uid)s
        """
        cursor.execute(query, locals())


def get_user_session(conn, session_uid):
    with conn.cursor() as cursor:
        query = """
            select session_uid, user_uid, ip_address, expiration_timestamp, creation_timestamp
            from user_sessions
            where session_uid = %(session_uid)s
            and expiration_timestamp > current_timestamp
        """
        cursor.execute(query, locals())
        for row in cursor:
            return UserSession(*row)
        return None


def insert_user_session(conn, user_uid, ip_address, expiration_timestamp):
    with conn.cursor() as cursor:
        query = """
            insert into user_sessions (user_uid, ip_address, expiration_timestamp)
            values (%(user_uid)s, %(ip_address)s, %(expiration_timestamp)s)
            returning session_uid, user_uid, ip_address, expiration_timestamp, creation_timestamp
        """
        cursor.execute(query, locals())
        row = cursor.fetchone()
        return UserSession(*row) if row else None


def validate_api_key(conn, api_key):
    with conn.cursor() as cursor:
        query = """
            select api_key, user_uid, creation_timestamp
            from user_keys
            where api_key = %(api_key)s
        """
        cursor.execute(query, locals())
        for row in cursor:
            return UserApi(*row)
        return None


def get_api_key(conn, user_uid):
    with conn.cursor() as cursor:
        query = """
            select api_key, user_uid, creation_timestamp
            from user_keys
            where user_uid = %(user_uid)s
        """
        cursor.execute(query, locals())
        for row in cursor:
            return UserApi(*row)
        return None


def insert_api_key(conn, user_uid):
    with conn.cursor() as cursor:
        query = """
            insert into user_keys (api_key, user_uid, creation_timestamp)
            values (gen_random_uuid(), %(user_uid)s, current_timestamp)
            on conflict (user_uid) do update
            set api_key = gen_random_uuid(), user_uid = %(user_uid)s, creation_timestamp = current_timestamp
        """
        cursor.execute(query, locals())
        return None


def delete_api_key(conn, user_uid):
    with conn.cursor() as cursor:
        query = """
            delete from user_keys
            where user_uid = %(user_uid)s
        """
        cursor.execute(query, locals())
        return None


def expire_user_session(conn, session_uid):
    with conn.cursor() as cursor:
        query = """
            update user_sessions set expiration_timestamp = current_timestamp
            where session_uid = %(session_uid)s
        """
        cursor.execute(query, locals())
        return None


def get_device_profile_by_uid(conn, device_uid):
    with conn.cursor() as cursor:
        query = """
            select device_uid, user_uid, mac_address, device_id1, device_id2, signature,
                portal, timezone, modified_timestamp, creation_timestamp
            from devices
            where device_uid = %(device_uid)s
            limit 1
        """
        cursor.execute(query, locals())
        row = cursor.fetchone()
        return DeviceProfile(*row) if row else None


def get_device_profile_by_user(conn, user_uid):
    with conn.cursor() as cursor:
        query = """
            select device_uid, user_uid, mac_address, device_id1, device_id2, signature,
                portal, timezone, modified_timestamp, creation_timestamp
            from devices
            where user_uid = %(user_uid)s
            limit 1
        """
        cursor.execute(query, locals())
        row = cursor.fetchone()
        return DeviceProfile(*row) if row else None



def insert_user_device(conn, user_uid, mac_address, device_id1, device_id2, signature, portal, timezone):
    with conn.cursor() as cursor:
        query = """
            insert into devices (user_uid, mac_address, device_id1, device_id2, signature, portal, timezone)
            values (%(user_uid)s, %(mac_address)s, %(device_id1)s, %(device_id2)s, %(signature)s, 
                    %(portal)s, %(timezone)s)
            on conflict (user_uid) do update
            set mac_address = excluded.mac_address, device_id1 = excluded.device_id1, device_id2 = excluded.device_id2,
                signature = excluded.signature, portal = excluded.portal, timezone = excluded.timezone, 
                modified_timestamp = now()
        """
        cursor.execute(query, locals())
        return None
