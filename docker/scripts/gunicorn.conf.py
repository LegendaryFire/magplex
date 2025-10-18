import logging
import multiprocessing

from app_setup import initialize
from magplex.utilities.database import PostgresPool

# Configuration
MAX_PG_CONNECTIONS = 100
MIN_WORKERS = 1
MIN_THREADS = 1

# Auto-calculate workers and threads based on max connection count
cpu_count = multiprocessing.cpu_count()
workers = max(MIN_WORKERS, cpu_count // 2)
threads_per_worker = max(MIN_THREADS, MAX_PG_CONNECTIONS // workers)


# Gunicorn settings
worker_class = "gthread"
workers = workers
threads = threads_per_worker
bind = "0.0.0.0:8000"


def on_starting(server):
    initialize()

def post_fork(server, worker):
    # Master process is forked with a non-thread safe pool. Pool must be closed.
    PostgresPool.close_pool()

    # Set the pool name so it's easy to identify.
    PostgresPool.set_pool_name(f"pool-{worker.pid}")

    # Set the minimum and maximum pool size which respects connection limit.
    PostgresPool.set_min_size(min(2, threads_per_worker))
    PostgresPool.set_max_size(threads_per_worker)

    # Create a new thread pool per worker.
    PostgresPool.connect()
