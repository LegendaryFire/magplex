from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


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


def insert_user_device(conn, user_uid, mac_address, device_id1, device_id2, signature, portal, language, timezone):
    with conn.cursor() as cursor:
        query = """
            insert into devices (user_uid, mac_address, device_id1, device_id2, signature, portal, language, timezone)
            values (%(user_uid)s, %(mac_address)s, %(device_id1)s, %(device_id2)s, %(signature)s, %(portal)s,
                    %(language)s, %(timezone)s)
            on conflict (user_uid) do update
            set mac_address = excluded.mac_address,
                device_id1 = excluded.device_id1,
                device_id2 = excluded.device_id2,
                signature = excluded.signature,
                portal = excluded.portal,
                language = excluded.language,
                timezone = excluded.timezone,
                modified_timestamp = now()
        """
        cursor.execute(query, locals())
        return None
