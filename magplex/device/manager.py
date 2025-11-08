from magplex import PostgresConnection, users
from magplex.device.device import Device


class DeviceManager:
    _devices = {}

    @classmethod
    def get_user_device(cls, device_uid):
        device_uid = str(device_uid)
        if device_uid in cls._devices:
            return cls._devices.get(device_uid)

        db_conn = PostgresConnection()
        device_profile = users.database.get_device_profile_by_uid(db_conn, device_uid)
        if device_profile is None:
            return None
        db_conn.close()
        user_device = Device(device_profile)
        cls._devices.update({user_device.device_uid: user_device})
        return user_device
