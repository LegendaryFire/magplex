import os

from dotenv import load_dotenv

load_dotenv()

class Variables:
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = os.getenv('REDIS_PORT', 6379)
    STB_PORTAL = os.getenv('PORTAL', None)
    STB_MAC = os.getenv('MAC_ADDRESS', None)
    STB_LANGUAGE = os.getenv('STB_LANG', None)
    STB_TIMEZONE = os.getenv('TZ', None)
    STB_DEVICE_ID = os.getenv('DEVICE_ID', None)
    STB_DEVICE_ID2 = os.getenv('DEVICE_ID2', None)
    STB_SIGNATURE = os.getenv('SIGNATURE', None)

    @classmethod
    def valid(cls):
        return all(getattr(cls, variable) for variable in dir(cls) if not variable.startswith('__'))
