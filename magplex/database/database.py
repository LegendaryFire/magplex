import logging

import psycopg
import psycopg_pool
import redis

from magplex.utilities.variables import Environment

logging.getLogger('psycopg.pool').setLevel(logging.DEBUG)

class PostgresConnection:
    def __init__(self):
        self._conn = None

    def get_connection(self):
        """Lazily get a live connection from the pool."""
        if self._conn is None or self._conn.closed:
            self._conn = PostgresPool.get_connection()
        return self._conn

    def cursor(self, *args, **kwargs):
        """Expose cursor() directly, lazily getting the connection."""
        return self.get_connection().cursor(*args, **kwargs)

    def commit(self):
        if self._conn:
            try:
                self._conn.commit()
            except psycopg.OperationalError:
                pass

    def rollback(self):
        if self._conn:
            try:
                self._conn.rollback()
            except psycopg.OperationalError:
                pass

    def close(self):
        """Return connection to pool instead of closing."""
        if self._conn:
            PostgresPool.put_connection(self._conn)
            self._conn = None

    def __enter__(self):
        return self.get_connection()

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


class PostgresPool:
    _pool = None
    _min_size = 4
    _max_size = 100
    _pool_name = None

    @classmethod
    def set_min_size(cls, min_size):
        cls._min_size = min_size

    @classmethod
    def set_max_size(cls, max_size):
        cls._max_size = max_size

    @classmethod
    def set_pool_name(cls, pool_name):
        cls._pool_name = pool_name

    @classmethod
    def get_connection(cls):
        if cls._pool is None:
            cls.connect()
        return cls._pool.getconn()


    @classmethod
    def put_connection(cls, conn):
        if cls._pool is not None:
            cls._pool.putconn(conn)


    @classmethod
    def connect(cls):
        if cls._pool is None:
            conninfo = (
                f"postgresql://{Environment.POSTGRES_USER}:"
                f"{Environment.POSTGRES_PASSWORD}@"
                f"{Environment.POSTGRES_HOST}:"
                f"{Environment.POSTGRES_PORT}/"
                f"{Environment.POSTGRES_DB}"
            )
            cls._pool = psycopg_pool.ConnectionPool(
                conninfo=conninfo,
                open=True,
                min_size=cls._min_size,
                max_size=cls._max_size,
                max_lifetime=900,
                max_idle=60
            )

    @classmethod
    def close_pool(cls):
        if cls._pool:
            cls._pool.close()
            pool = cls._pool
            cls._pool = None
            del pool  # Force the garbage collector to remove before fork.



class RedisPool:
    _pool = None
    _client = None

    @classmethod
    def create_pool(cls):
        """Create a connection pool if it doesn’t exist yet."""
        if cls._pool is None:
            cls._pool = redis.ConnectionPool(
                host=Environment.REDIS_HOST,
                port=Environment.REDIS_PORT,
                db=0,
                password=getattr(Environment, "REDIS_PASSWORD", None),
                decode_responses=True
            )
        return cls._pool

    @classmethod
    def get_connection(cls):
        """Return a Redis client using the pool."""
        if cls._client is None:
            cls._client = redis.Redis(connection_pool=cls.create_pool())
        return cls._client
