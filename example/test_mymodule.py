import pytest

import pymysqlite


# import tested module as a pytest fixture
@pytest.fixture
def mymodule():
    from . import mymodule
    return mymodule


@pytest.fixture
def fake_conn():
    connection = pymysqlite.connect(":memory:")
    return connection


TEST_SQL = """
CREATE TABLE users (id INTEGER, name TEXT);
INSERT INTO users VALUES (1, "foo"), (2, "bar");
"""


@pytest.fixture
def load_test_data(fake_conn):
    fake_conn.executescript(TEST_SQL)
    fake_conn.commit()
    return fake_conn


# test a method by passing in fake_conn (dependency injection)
@pytest.mark.usefixtures("load_test_data")
def test_my_method(mymodule, fake_conn):
    assert mymodule._get_user_id(fake_conn, "foo") == 1
    assert mymodule._get_user_id(fake_conn, "bar") == 2
    assert mymodule._get_user_id(fake_conn, "nonexist") is None


# test a method by monkeypatching mymodule.connect()
@pytest.fixture
def patch_conn(monkeypatch, mymodule, fake_conn):
    monkeypatch.setattr(mymodule, "connect", lambda: fake_conn)


@pytest.mark.usefixtures("load_test_data", "patch_conn")
def test_monkeypatched_method(mymodule):
    assert mymodule.get_user_id("foo") == 1
    assert mymodule.get_user_id("bar") == 2
    assert mymodule.get_user_id("nonexist") is None
