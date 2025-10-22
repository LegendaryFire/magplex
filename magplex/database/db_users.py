from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    user_uid: UUID
    username: str
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

@dataclass
class UserSession:
    session_uid: UUID
    user_uid: UUID
    ip_address: str
    expiration_timestamp: datetime
    creation_timestamp: datetime


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


def expire_user_session(conn, session_uid):
    with conn.cursor() as cursor:
        query = """
            update user_sessions set expiration_timestamp = current_timestamp
            where session_uid = %(session_uid)s
        """
        cursor.execute(query, locals())
        return None