from magplex.device.device import Device


class DeviceManager:
    _devices = {}

    @classmethod
    def get_user_device(cls, device_uid):
        device_uid = str(device_uid)
        if device_uid in cls._devices:
            return cls._devices.get(device_uid)

        user_device = Device(device_uid)
        cls._devices.update({user_device.device_uid: user_device})
        return user_device
