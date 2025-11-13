import logging
import sys
import time

import psycopg
import redis

from magplex import Locale
from magplex.database.database import PostgresConnection, PostgresPool, RedisPool
from magplex.database.migrations import migrations
from magplex.utilities import logs
from magplex.utilities.scheduler import TaskManager, wake_scheduler
from magplex.utilities.variables import Environment
from version import version


def initialize():
    # Initialize logging.
    logs.initialize()
    logging.info(f"MagPlex v{version} by LegendaryFire")


    # Check & make sure all environment variables are provided.
    if not Environment.valid():
        logging.error("Missing environment variables.")
        sys.exit()

    # Test Redis cache connection.
    cache_conn = RedisPool.get_connection()
    try:
        cache_conn.ping()
        logging.info(f"Connected to Redis database at {Environment.REDIS_HOST}:{Environment.REDIS_PORT}.")
    except redis.exceptions.RedisError:
        logging.error(f"Unable to connect to Redis server at {Environment.REDIS_HOST}:{Environment.REDIS_PORT}.")
        time.sleep(30)
        sys.exit()


    # Test Postgres database connection.
    try:
        conn = PostgresConnection().get_connection(use_pool=False)
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        conn.close()
        logging.info(f"Connected to Postgres database at {Environment.POSTGRES_HOST}:{Environment.POSTGRES_PORT}.")
    except psycopg.Error:
        logging.error(f"Unable to connect to Postgres server at {Environment.POSTGRES_HOST}:{Environment.POSTGRES_PORT}.")
        time.sleep(30)
        sys.exit()


    # Create database if it doesn't already exist.
    logging.info("Creating Postgres database schema if it doesn't already exist.")
    migrations.create_database()
    migrations.run_missing_migrations()

    # TODO: Initialize all devices on startup, and add their background tasks to the queue.
    PostgresPool.close_pool()


def run_scheduler():
    # Start background task scheduler.
    scheduler = TaskManager.get_scheduler()
    scheduler.remove_all_jobs()
    scheduler.add_job(wake_scheduler, 'interval', id="wake_scheduler", seconds=5, replace_existing=True)
    logging.info(Locale.TASK_JOB_ADDED_SUCCESSFULLY)
    if not scheduler.running:
        scheduler.start()
