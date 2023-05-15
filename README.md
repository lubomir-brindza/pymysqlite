# pymysqlite

`pymysqlite` acts as a simple compatibility layer that translates `pymysql` calls to `sqlite3` calls, allowing you to test MySQL code without having a running MySQL server on hand. Hopefully.

## Come again?

Ever had the bright idea to add tests to your database-adjacent Python scripts only to find out that, despite having superficially similar API, you can't just use Sqlite as a drop-in replacement fixture in your tests? No? Well, pretend with me for a while.

## Should I use this in my project?

Probably not. This only makes sense for simple projects that don't use an abstraction layer like SQLAlchemy already.

# Key differences in `pymysql` and `sqlite3`

The first and most glaring difference is in how each library treats its SQL placeholders - where `pymysql` uses `%s` and `%(name)s` for SQL arguments, `sqlite3` uses `?` and `:name` instead. You **do** use placeholders, _right?_

```python
sqlite_cursor.execute("SELECT * FROM users where id=?", (1, ))  # sqlite3
pymysql_cursor.execute("SELECT * FROM users where id=%d", (1, ))  # pymysql
```

Another difference is that while `pymysql` allows instantiating a cursor via a context manager, `sqlite3` does not:
```python
# pymysql
conn = pymysql.connect(**config)
with conn.cursor() as cursor:
    cursor.execute("SELECT * FROM users")

# sqlite3
conn = sqlite3.connect(":memory:")
with conn.cursor() as cursor:  # fails
    ...

cursor = conn.cursor()  # works ok
cursor.execute("SELECT * FROM users")
```

How many rows?
--------------
A common usage pattern in `pymysql` is as follows:

```python
# pymysql
num_rows = cursor.execute("SELECT * FROM users WHERE id=%s", (id,))
if num_rows:
    user = cursor.fetchone()
```
Unfortunately, `sqlite3` has a... difficult relationship when it comes to knowing how many rows a cursor returns. For one, the `.execute()` method does not return the number of rows affected, instead returning the cursor instance:

```python
# sqlite3
res = cursor.execute("SELECT * FROM users")
res is cursor  # True
res.rowcount == -1  # True
```
Furthermore, the `.rowcount` attribute only returns correct values for `INSERT`, `UPDATE`, `DELETE`, and `REPLACE` statements ([docs](https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.rowcount)). This means that `if num_rows: ...` in the example above would not work as expected.

One possible workaround would be to `fetchall()` results a variable and return its `__len__`, however this would require us to run the SELECT query twice, and modify the behavior of `fetch*` methods. This is a TODO. For now, try to avoid this usage pattern.

```python
# sqlite3
cursor.execute("SELECT * FROM users WHERE id=1")
if row := cursor.fetchone():  # this works fine
    ...
```

# Example use with `pytest`

```python
import pytest
import pymysqlite

@pytest.fixture
def mymodule():  # import tested module as a fixture
    import mymodule
    return mymodule

@pytest.fixture
def fake_db():
    connection = pymysqlite.connect(":memory:")
    return connection

@pytest.fixture
def load_test_data(fake_db)
    fake_db.executescript("import_test_data.sql")
    fake_db.commit()
    return fake_db

def test_my_method(mymodule, fake_db, load_test_data):
    """testing a method using dependency injection"""
    mymodule._my_method(conn=fake_db)

@pytest.fixture
def patch_conn(monkeypatch, mymodule)
    monkeypatch.setattr(mymodule, "connect", return_value=fake_db)

def test_without_di(mymodule, patch_conn):
    """testing a method without dependency injection"""
    mymodule.my_method()
```
