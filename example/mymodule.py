import pymysql


def connect():
    conn = pymysql.connect(host=..., port=..., user=..., db=...)  # type:ignore
    return conn


def get_user_id(user: str) -> int | None:
    connection = connect()
    return _get_user_id(connection, user)


def _get_user_id(conn, user) -> int | None:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE name=%s", (user,))
        if row := cur.fetchone():
            return row[0]
    return None
