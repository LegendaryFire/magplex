import os
import shutil
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from version import version

base_directory = Path(__file__).resolve().parent.parent.parent
env_path = base_directory.joinpath('.env')
load_dotenv(env_path)

class Environment:
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = os.getenv('REDIS_PORT', 6379)

    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', 5432)
    POSTGRES_USER = os.getenv('POSTGRES_USER', None)
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', None)
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'postgres')

    BASE_DIR = base_directory
    BASE_LOG = os.path.join(BASE_DIR, 'logs', f"magplex-v{version}-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.log")
    BASE_FFMPEG = os.getenv('FFMPEG', None) or shutil.which('ffmpeg')
    BASE_CODEC = os.getenv('CODEC', False)

    @classmethod
    def valid(cls):
        return all(getattr(cls, variable) is not None for variable in dir(cls) if not variable.startswith('__'))
