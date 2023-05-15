from __future__ import annotations

import re
import sqlite3
from warnings import warn


def _translate(sql: str) -> str:
    # replace placeholders
    sql = re.sub(r"%[a-z]\b", "?", sql)
    sql = re.sub(r"%\(([a-z]+)\)[a-z]\b", r":\1", sql)
    return sql


class Connection:
    def __init__(self, database: str, *args, **kwargs) -> None:
        self._connection = sqlite3.connect(database, *args, **kwargs)

    def cursor(self):
        _cursor = self._connection.cursor()
        return Cursor(_cursor)

    def close(self) -> None:
        self._connection.close()

    def commit(self) -> None:
        self._connection.commit()

    # While pymysql disallows calling execute* methods from the Connection
    # object directly, these can still be useful in the test set up stage.

    def executescript(self, script: str):
        self._connection.executescript(script)

    def execute(self, sql: str, parameters):  # type:ignore
        warn("pymysql does not allow calling execute() directly from the connection object")
        return self._connection.execute(_translate(sql), parameters)

    def executemany(self, sql: str, parameters):
        warn("pymysql does not allow calling executemany() directly from the connection object")
        return self._connection.executemany(_translate(sql), parameters)


class Cursor:
    def __init__(self, _cursor) -> None:
        self._cursor = _cursor

    def execute(self, sql: str, args=None) -> int:  # type:ignore
        # FIXME: cursor.rowcount for SELECT statements is always -1 (which evals as True)
        sql = _translate(sql)
        self._cursor.execute(sql, args or [])
        if not sql.startswith("SELECT"):
            return self._cursor.rowcount
        warn("SELECT statements always return -1, do not depend on this value in your code")
        return -1

    def executemany(self, sql: str, args) -> int:  # type:ignore
        sql = _translate(sql)
        self._cursor.executemany(sql, args)
        return self._cursor.rowcount

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchmany(self):
        return self._cursor.fetchmany()

    def fetchall(self):
        return self._cursor.fetchall()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        del exc_info
        self._cursor.close()


def connect(database: str) -> Connection:
    return Connection(database)
