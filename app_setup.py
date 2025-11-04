import logging
import sys
import time

import psycopg
import redis

from magplex.database.database import PostgresConnection, PostgresPool, RedisPool
from magplex.database.migrations import migrations
from magplex.device.device import DeviceManager
from magplex.utilities import logs
from magplex.utilities.scheduler import TaskManager
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
        conn = PostgresConnection()
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


    # Start background task scheduler.
    scheduler = TaskManager.get_scheduler()
    if not scheduler.running:
        scheduler.start()

    # TODO: Initialize all devices on startup, and add their background tasks to the queue.
    """
    # Create STB profile and device.
    device = DeviceManager.get_device()
    if device is None:
        logging.warning("Unable to get device. It's likely that a STB device has not been configured yet.")
    """

    PostgresPool.close_pool()
