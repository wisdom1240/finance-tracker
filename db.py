"""
db.py

Database connection helper for the Finance Tracker app.
One connection per Flask request, opened lazily and closed cleanly.
"""

import psycopg2
from flask import g

from config import Config


def get_db():
    """
    Return a database connection for the current request.
    Reuses the same connection if already opened this request.
    """
    if "db" not in g:
        g.db = psycopg2.connect(Config.DATABASE_URL)
    return g.db


def close_db(exc=None):
    """
    Close the database connection for the current request.
    Called automatically by Flask at the end of each request.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    """
    Register the request cleanup with a Flask app.
    Call this once in app.py after creating the app.
    """
    app.teardown_appcontext(close_db)