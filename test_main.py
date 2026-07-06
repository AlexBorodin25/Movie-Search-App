import sqlite3

import pytest
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

import main as app_module

@pytest.fixture
def test_db(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_movies.db"

    monkeypatch.setattr(app_module, "DB_NAME", test_db_path)
    app_module.init_db()

    return test_db_path

@pytest.fixture
def client(test_db):
    return TestClient(app_module.app)

def test_get_db_connection(test_db):
    conn = app_module.get_db()

    assert isinstance(conn, sqlite3.Connection)
    assert conn.row_factory == sqlite3.Row

    conn.close()

def test_favorites_table(test_db):
    conn = app_module.get_db()

