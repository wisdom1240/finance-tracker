"""
app.py

The entry point for the Finance Tracker web application.
Run with:   python app.py
Then open:  http://127.0.0.1:5000
"""

from flask import Flask, render_template

from config import Config
from db import init_app as init_db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)