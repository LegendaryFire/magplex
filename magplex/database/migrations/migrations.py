import logging
import os

from magplex.database.database import PostgresConnection

migrations_folder = os.path.dirname(__file__)

def create_database():
    conn = PostgresConnection()

    # Check to see if the database already exists.
    query = """
        select 1 from information_schema.tables
        where table_schema = 'public'
        limit 1
    """
    with conn.cursor() as cursor:
        cursor.execute(query)
        database_exists = cursor.fetchone() is not None

    # No need to run the database script if it already exists.
    if database_exists:
        return

    logging.info("Creating Postgres database.")
    # Run the create database script.
    path = os.path.join(migrations_folder, 'create-database.sql')
    with open(path, 'r', encoding='utf-8') as f:
        query = f.read()

    with conn.cursor() as cursor:
        cursor.execute(query)

    # Add migration records so they are skipped, the changes are included in the create database script.
    migration_names = sorted(os.listdir(migrations_folder))
    for migration_name in migration_names:
        migration_path = os.path.join(migrations_folder, migration_name)
        if not migration_path.endswith(".sql") or not os.path.isfile(migration_path):
            continue
        _insert_migration_record(conn, migration_name)

    conn.commit()
    conn.close()


def run_missing_migrations():
    conn = PostgresConnection()
    migration_names = sorted(os.listdir(migrations_folder))

    for migration_name in migration_names:
        migration_path = os.path.join(migrations_folder, migration_name)
        if not migration_path.endswith(".sql") or not os.path.isfile(migration_path):
            continue

        if not _migration_record_exists(conn, migration_name):
            _run_migration(conn, migration_name)
    conn.commit()
    conn.close()



def _run_migration(conn, migration_name):
    path = os.path.join(migrations_folder, migration_name)
    with open(path, 'r', encoding='utf-8') as f:
        query = f.read()
    with conn.cursor() as cursor:
        cursor.execute(query)

    query = """
        insert into migrations (migration_name)
        values (%(migration_name)s)
    """
    with conn.cursor() as cursor:
        cursor.execute(query, locals())


def _insert_migration_record(conn, migration_name):
    query = """
        insert into migrations (migration_name)
            values (%(migration_name)s)
    """
    with conn.cursor() as cursor:
        cursor.execute(query, locals())

def _migration_record_exists(conn, migration_name):
    query = """
        select migration_name from migrations
        where migration_name = %(migration_name)s
    """

    with conn.cursor() as cursor:
        cursor.execute(query, locals())
        return cursor.fetchone() is not None
