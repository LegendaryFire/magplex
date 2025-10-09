import multiprocessing
import os

from redis import Redis, RedisError

worker_class = "gthread"
workers = 2 * multiprocessing.cpu_count() + 1
threads = 8
bind = "0.0.0.0:8000"


def on_starting(server):
    """
    Called once before any workers are forked.
    Perfect place to flush Redis once.
    """
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = os.getenv('REDIS_PORT', 6379)
    try:
        r = Redis(host=redis_host, port=redis_port, db=0)
        r.flushall()
    except RedisError:
        server.log.info("Unable to flush Redis cache.")
