import os
import shutil
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from version import version

base_directory = Path(__file__).resolve().parent.parent.parent
env_path = base_directory.joinpath('.env')
load_dotenv(env_path)

class Variables:
    BASE_DIR = base_directory
    BASE_LOG = os.path.join(BASE_DIR, 'logs', f"magplex-v{version}-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.log")
    BASE_FFMPEG = os.getenv('FFMPEG', None) or shutil.which('ffmpeg')
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
