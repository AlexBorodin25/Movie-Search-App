import sqlite3

import pytest
from fastapi.testclient import TestClient

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

def test_home_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Movie Search" in response.text
    assert "Search by movie title" in response.text
    assert "Favorites" in response.text
    assert "No favorites yet." in response.text