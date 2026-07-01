import sqlite3
import os
from pathlib import Path
from typing import Optional

import requests
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

OMDB_URL = "https://www.omdbapi.com/"
BASE_DIR = Path(__file__).resolve().parent
DB_NAME = BASE_DIR / "movies.db"
app = FastAPI(title="Movie Search App")

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

templates = Jinja2Templates(
    directory=BASE_DIR / "templates")


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                imdb_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                year TEXT,
                poster TEXT,
                rating INTEGER CHECK (rating BETWEEN 1 AND 5))
            '''
        )

init_db()

def get_favorites():
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM favorites ORDER BY title"
        ).fetchall()

@app.get("/")
def home(request: Request):
    print("HOME ROUTE WORKS")

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "movies": None,
            "favorites": get_favorites(),
            "error": None,
            "search_title": "",
        },
    )

@app.get("/search")
def search(request: Request, title: str):
    OMDB_API_KEY = os.getenv("OMDB_API_KEY")

    if not OMDB_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OMDB_API_KEY not set.",
        )

    response = requests.get(
        OMDB_URL,
        params={
            "apikey": OMDB_API_KEY,
            "s": title,
            "type": "movie",
        },
        timeout=10,
    )

    data = response.json()

    movies = []
    error = None

    if data.get("Response") == "False":
        error = data.get("Error", "No movies found.")
    else:
        movies = data.get("Search", [])

    return templates.TemplateResponse(
        request,
        "index.html",
            {"request": request,
            "movies": movies,
            "favorites": get_favorites(),
            "error": error,
            "search_title": title,
        },
    )

@app.post("/favorites")
def add_fav(
    imdb_id: str = Form(...),
    title: str = Form(...),
    year: Optional[str] = Form(None),
    poster: Optional[str] = Form(None),
    rating: Optional[int] = Form(None),
):
    with get_db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO favorites 
            (imdb_id, title, year, poster, rating)
            VALUES (?, ?, ?, ?, ?)
            """,
            (imdb_id, title, year, poster, rating),
        )

    return RedirectResponse("/", status_code=303)

@app.post("/favorites/{imdb_id}/delete")
def delete_fav(imdb_id: str):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM favorites WHERE imdb_id = ?",
            (imdb_id,),
        )

    return RedirectResponse("/", status_code=303)

