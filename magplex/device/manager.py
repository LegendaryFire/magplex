from magplex import users
from magplex import PostgresConnection
from magplex.device.device import Device


class DeviceManager:
    @classmethod
    def get_user_device(cls, user_uid):
        db_conn = PostgresConnection()
        device_profile = users.database.get_user_device_profile(db_conn, user_uid)
        if device_profile is None:
            return None
        db_conn.close()
        return Device(device_profile)
