import logging

import werkzeug

from magplex import RedisPool
from magplex.utilities.variables import Environment

REDIS_BUFFER_CHANNEL = "logs"
REDIS_LOG_BUFFER = "log_buffer"
REDIS_LINE_LIMIT = 1000

class RedisLogHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.redis = RedisPool.get_connection()
            self.redis.ping()
            self.redis.delete(REDIS_LOG_BUFFER)
            self.connected = True
        except Exception:
            self.redis = None
            self.connected = False

    def emit(self, record):
        try:
            msg = self.format(record)
            if not self.connected or not self.redis:
                return

            try:
                pipe = self.redis.pipeline()
                pipe.publish(REDIS_BUFFER_CHANNEL, msg)
                pipe.lpush(REDIS_LOG_BUFFER, msg)
                pipe.ltrim(REDIS_LOG_BUFFER, 0, REDIS_LINE_LIMIT - 1)
                pipe.execute()
            except Exception:
                self.connected = False
        except Exception:
            pass


def initialize():
    werkzeug.serving._log_add_style = False
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if Environment.DEBUG else logging.INFO)
    root.handlers.clear()
    stream = logging.StreamHandler()
    redis_handler = RedisLogHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
    stream.setFormatter(formatter)
    redis_handler.setFormatter(formatter)
    root.addHandler(stream)
    root.addHandler(redis_handler)