import os
import time

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values


def connect(retries=30, delay=2):
    last_error = None
    for _ in range(retries):
        try:
            return psycopg2.connect(
                host=os.environ.get("POSTGRES_HOST", "127.0.0.1"),
                port=int(os.environ.get("POSTGRES_PORT", "5432")),
                user=os.environ.get("POSTGRES_USER", "ligre"),
                password=os.environ.get("POSTGRES_PASSWORD", "ligre"),
                dbname=os.environ.get("POSTGRES_DATABASE", "ligre_db"),
            )
        except psycopg2.OperationalError as error:
            last_error = error
            time.sleep(delay)
    raise last_error


def truncate_tables(cursor, tables):
    statement = sql.SQL("TRUNCATE TABLE {}").format(
        sql.SQL(", ").join(map(sql.Identifier, tables))
    )
    cursor.execute(statement)


def insert_rows(cursor, table, columns, rows):
    if not rows:
        return
    statement = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
        sql.Identifier(table),
        sql.SQL(", ").join(map(sql.Identifier, columns)),
    )
    execute_values(cursor, statement, rows, page_size=1000)
