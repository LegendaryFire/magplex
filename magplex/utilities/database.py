import psycopg


class DBConnectionPool:
    def __init__(self, host, port, username, password, database):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self._conn = None

    def ping_conn(self):
        with psycopg.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            dbname=self.database,
            connect_timeout=5
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()

    def get_conn(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                dbname=self.database
            )
        return self._conn

    def get_cursor(self):
        return self.get_conn().cursor()

    def close_conn(self):
        if self._conn is not None:
            try:
                self._conn.commit()
            except psycopg.Error:
                self._conn.rollback()
            finally:
                self._conn.close()
                self._conn = None
