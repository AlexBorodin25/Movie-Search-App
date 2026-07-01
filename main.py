import sqlite3
import os
from typing import Optional

import requests
from fastapi import FastAPI, Form, Request,
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import  Jinja2Templates

OMDB_API_KEY = os.getenv("OMDB_API_KEY")
OMDB_URL = "https://www.omdbapi.com/"
DB_NAME = "movies.db"

app = FastAPI(title="Movie Search App")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request
        "movies": None,
        "favorites": get_favorites(),
        "error": None,
        "search_title": "",
         },
    )