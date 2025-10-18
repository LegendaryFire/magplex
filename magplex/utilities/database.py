import logging

import psycopg
import psycopg_pool
import redis

from magplex.utilities.environment import Variables

logging.getLogger('psycopg.pool').setLevel(logging.DEBUG)

class LazyPostgresConnection:
    def __init__(self):
        self._conn = None

    def get_connection(self):
        """Lazily get a live connection from the pool."""
        if self._conn is None or self._conn.closed:
            self._conn = PostgresPool.get_connection()
        else:
            # Ping the connection and make sure it's alive and well.
            try:
                with self._conn.cursor() as cur:
                    cur.execute("SELECT 1")
            except psycopg.OperationalError:
                try:
                    self._conn.close()
                except (psycopg.OperationalError, psycopg.InterfaceError):
                    pass
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
        logging.info("Connection returned through Postgres lazy context manager.")


class PostgresPool:
    _pool = None

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
                f"postgresql://{Variables.POSTGRES_USER}:"
                f"{Variables.POSTGRES_PASSWORD}@"
                f"{Variables.POSTGRES_HOST}:"
                f"{Variables.POSTGRES_PORT}/"
                f"{Variables.POSTGRES_DB}"
            )
            cls._pool = psycopg_pool.ConnectionPool(
                conninfo=conninfo,
                open=False,
                min_size=0,
                max_size=25,
                max_lifetime=900,
                max_idle=60
            )

    @classmethod
    def close_pool(cls):
        if cls._pool:
            cls._pool.close()
            cls._pool = None


class RedisPool:
    _pool = None
    _client = None

    @classmethod
    def create_pool(cls):
        """Create a connection pool if it doesn’t exist yet."""
        if cls._pool is None:
            cls._pool = redis.ConnectionPool(
                host=Variables.REDIS_HOST,
                port=Variables.REDIS_PORT,
                db=0,
                password=getattr(Variables, "REDIS_PASSWORD", None),
                decode_responses=True
            )
        return cls._pool

    @classmethod
    def get_connection(cls):
        """Return a Redis client using the pool."""
        if cls._client is None:
            cls._client = redis.Redis(connection_pool=cls.create_pool())
        return cls._client
