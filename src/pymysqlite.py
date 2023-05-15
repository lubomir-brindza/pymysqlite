from __future__ import annotations

import re
import sqlite3
from warnings import warn


def _translate(sql: str) -> str:
    # replace placeholders
    sql = re.sub(r"\b%[a-z]\b", "?", sql)
    sql = re.sub(r"\b%\(([a-z]+)\)[a-z]\b", r":\1", sql)
    return sql


class Connection(sqlite3.Connection):
    def __init__(self, database: str, *args, **kwargs) -> None:
        self._connection = sqlite3.connect(database, *args, **kwargs)

    def cursor(self):
        return Cursor(self)

    def close(self) -> None:
        return super().close()

    # While pymysql disallows calling execute* methods from the Connection
    # object directly, these can still be useful in the test set up stage.

    def execute(self, sql: str, parameters):  # type:ignore
        warn("pymysql does not allow calling execute() directly from the connection object")
        return super().execute(_translate(sql), parameters)

    def executemany(self, sql: str, parameters):
        warn("pymysql does not allow calling executemany() directly from the connection object")
        return super().executemany(_translate(sql), parameters)


class Cursor(sqlite3.Cursor):
    def __init__(self, conn) -> None:
        self._last_stmt: str | None = None
        super().__init__(conn)

    def execute(self, sql: str, parameters) -> int:  # type:ignore
        # FIXME: cursor.rowcount for SELECT statements is always -1 (which evals as True)
        sql = _translate(sql)
        self._last_stmt = sql
        super().execute(sql, parameters)
        if not sql.startswith("SELECT"):
            return self.rowcount
        warn("SELECT statements always return -1, do not depend on this value in your code")
        return -1

    def executemany(self, sql: str, parameters) -> int:  # type:ignore
        sql = _translate(sql)
        self._last_stmt = sql
        super().executemany(sql, parameters)
        return self.rowcount

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        del exc_info
        self.close()


def connect(database: str) -> Connection:
    return Connection(database)
