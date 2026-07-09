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
    with app_module.get_db() as conn:
        assert isinstance(conn, sqlite3.Connection)
        assert conn.row_factory == sqlite3.Row


def test_home_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Movie Search" in response.text
    assert "Search by movie title" in response.text
    assert "Favorites" in response.text
    assert "No favorites yet." in response.text


def test_search_without_APIkey(client, monkeypatch):
    monkeypatch.delenv("OMDB_API_KEY", raising=False)

    response = client.get("/search", params={"title": "Inception"})

    assert response.status_code == 500
    assert response.json()["detail"] == "OMDB_API_KEY not set."


def test_search(client, monkeypatch):
    class FakeResponse:
        def json(self):
            return {
                "Response": "True",
                "Search": [
                    {
                        "Title": "Inception",
                        "Year": "2010",
                        "imbdID": "tt1375666",
                        "Poster": "poster.jpg",
                    }
                ],
            }

    def fake_get(url, params, timeout):
        assert url == app_module.OMDB_URL
        assert params["apikey"] == "fake_key"
        assert params["s"] == "Inception"
        assert timeout == 10
        return FakeResponse()

    monkeypatch.setenv("OMDB_API_KEY", "fake_key")
    monkeypatch.setattr(app_module.requests, "get", fake_get)

    response = client.get("/search", params={"title": "Inception"})

    assert response.status_code == 200
    assert "Inception" in response.text
    assert "2010" in response.text
    assert "Save to Favorites" in response.text


def test_search_no_results(client, monkeypatch):
    class FakeResponse:
        def json(self):
            return {
                "Response": "False",
                "Error": "Movie not found!",
            }

    monkeypatch.setenv("OMDB_API_KEY", "fake_key")
    monkeypatch.setattr(
        app_module.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(),
    )

    response = client.get("/search", params={"title": "WrongTitle"})

    assert response.status_code == 200
    assert "Movie not found!" in response.text


def test_add_fav(client):
    response = client.post(
        "/favorites",
        data={
            "imdb_id": "tt1375666",
            "title": "Inception",
            "year": "2010",
            "poster": "poster.jpg",
            "rating": 5,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"

    favorites = app_module.get_favorites()

    assert len(favorites) == 1
    assert favorites[0]["title"] == "Inception"
    assert favorites[0]["rating"] == 5


def test_delete_fav(client):
    client.post(
        "/favorites",
        data={
            "imdb_id": "tt1375666",
            "title": "Inception",
            "year": "2010",
            "poster": "poster.jpg",
            "rating": 5,
        },
    )

    response = client.post(
        "/favorites/tt1375666/delete",
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"

    favorites = app_module.get_favorites()

    assert len(favorites) == 0


def test_init_db_creates_fav_table(test_db):
    with app_module.get_db() as conn:
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='favorites'"
        ).fetchone()

    assert result is not None
    assert result["name"] == "favorites"


def test_favorites_list_empty(test_db):
    favorites = app_module.get_favorites()

    assert favorites == []


def test_favorites_list(test_db):
    with app_module.get_db() as conn:
        conn.execute(
            """
            INSERT INTO favorites 
            (imdb_id, title, year, poster, rating)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("tt1375666", "Inception", "2010", "poster.jpg", 5),
        )

    favorites = app_module.get_favorites()

    assert len(favorites) == 1
    assert favorites[0]["imdb_id"] == "tt1375666"
    assert favorites[0]["title"] == "Inception"
    assert favorites[0]["rating"] == 5
