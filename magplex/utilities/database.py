import psycopg_pool
import redis

from magplex.utilities.environment import Variables


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
            cls._pool = psycopg_pool.ConnectionPool(conninfo=conninfo)


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
    def get_client(cls):
        """Return a Redis client using the pool."""
        if cls._client is None:
            cls._client = redis.Redis(connection_pool=cls.create_pool())
        return cls._client
