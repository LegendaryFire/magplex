import logging
import sys
import time

import psycopg
import redis

import magplex
from magplex import database
from magplex.utilities import logs
from magplex.utilities.database import PostgresPool, RedisPool
from magplex.utilities.device import DeviceManager
from magplex.utilities.environment import Variables
from magplex.utilities.scheduler import TaskManager
from version import version

# Initialize logging.
logs.initialize()
logging.info(f"MagPlex v{version} by LegendaryFire")


# Check & make sure all environment variables are provided.
if not Variables.valid():
    logging.error("Missing environment variables.")
    sys.exit()


# Test Redis cache connection.
cache_conn = RedisPool.get_client()
try:
    cache_conn.ping()
    logging.info(f"Connected to Redis database at {Variables.REDIS_HOST}:{Variables.REDIS_PORT}.")
except redis.exceptions.RedisError:
    logging.error(f"Unable to connect to Redis server at {Variables.REDIS_HOST}:{Variables.REDIS_PORT}.")
    time.sleep(5)
    sys.exit()


# Test Postgres database connection.
try:
    db_conn = PostgresPool.get_connection()
    with db_conn.cursor() as cur:
        cur.execute("SELECT 1")
        cur.fetchone()
    db_conn.rollback()
    PostgresPool.put_connection(db_conn)
    logging.info(f"Connected to Postgres database at {Variables.POSTGRES_HOST}:{Variables.POSTGRES_PORT}.")
except psycopg.Error as ex:
    logging.error(f"Unable to connect to Postgres server at {Variables.POSTGRES_HOST}:{Variables.POSTGRES_PORT}.")
    time.sleep(5)
    sys.exit()


# Create database if it doesn't already exist.
logging.info("Creating Postgres database schema if it doesn't already exist.")
db_conn = PostgresPool.get_connection()
database.create_database(db_conn)
PostgresPool.put_connection(db_conn)


# Start background task scheduler.
scheduler = TaskManager.get_scheduler()
scheduler.start()


# Create STB profile and device.
device = DeviceManager.get_device()

if __name__ == '__main__':
    app = magplex.create_app()
    app.stb = device
    app.run(host='0.0.0.0', port=8080, use_reloader=False)
