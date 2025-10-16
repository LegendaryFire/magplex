import multiprocessing

from app_setup import initialize_checks, initialize_worker

worker_class = "gthread"
workers = 2 * multiprocessing.cpu_count() + 1
threads = 8
bind = "0.0.0.0:8000"


def on_starting(server):
    initialize_checks()
    initialize_worker()