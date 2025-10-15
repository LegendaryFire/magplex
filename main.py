import logging
import sys
import time
import zoneinfo

import psycopg
import redis
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.schedulers.background import BackgroundScheduler

import magplex
from magplex import database
from magplex.utilities import logs
from magplex.utilities.database import DBConnectionPool
from magplex.utilities.device import Device, Profile
from magplex.utilities.environment import Variables
from version import version

# Initialize logging.
logs.initialize()
logging.info(f"MagPlex v{version} by LegendaryFire")


# Check & make sure all environment variables are provided.
if not Variables.valid():
    logging.error("Missing environment variables.")
    sys.exit()


# Test Redis cache connection.
cache_conn = redis.Redis(host=Variables.REDIS_HOST, port=Variables.REDIS_PORT, db=0)
try:
    cache_conn.ping()
    logging.info(f"Connected to Redis database at {Variables.REDIS_HOST}:{Variables.REDIS_PORT}.")
except redis.exceptions.RedisError:
    logging.error(f"Unable to connect to Redis server at {Variables.REDIS_HOST}:{Variables.REDIS_PORT}.")
    time.sleep(5)
    sys.exit()


# Test Postgres database connection.
db_conn = DBConnectionPool(
    host=Variables.POSTGRES_HOST,
    port=Variables.POSTGRES_PORT,
    username=Variables.POSTGRES_USER,
    password=Variables.POSTGRES_PASSWORD,
    database=Variables.POSTGRES_DB
)
try:
    db_conn.ping_conn()
    logging.info(f"Connected to Postgres database at {Variables.POSTGRES_HOST}:{Variables.POSTGRES_PORT}.")
except psycopg.Error as ex:
    logging.error(f"Unable to connect to Postgres server at {Variables.POSTGRES_HOST}:{Variables.POSTGRES_PORT}.")
    time.sleep(5)
    sys.exit()

logging.info("Creating Postgres database schema if it doesn't already exist/")
cursor = db_conn.get_cursor()
database.create_database(cursor)
db_conn.close_conn()


# Start background task scheduler.
jobstores = {'default': RedisJobStore(host=Variables.REDIS_HOST, port=Variables.REDIS_PORT, db=1)}
scheduler = BackgroundScheduler(jobstores=jobstores, timezone=zoneinfo.ZoneInfo(Variables.STB_TIMEZONE))
scheduler.start()


# Create STB profile and device.
profile = Profile(
    portal=Variables.STB_PORTAL,
    mac=Variables.STB_MAC,
    language=Variables.STB_LANGUAGE,
    timezone=Variables.STB_TIMEZONE,
    device_id=Variables.STB_DEVICE_ID,
    device_id2=Variables.STB_DEVICE_ID2,
    signature=Variables.STB_SIGNATURE
)
device = Device(cache_conn, scheduler, profile)

if __name__ == '__main__':
    app = magplex.create_app()
    app.stb = device
    app.run(host='0.0.0.0', port=8080, use_reloader=False)
