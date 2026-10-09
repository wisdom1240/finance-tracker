"""
app.py

The entry point for the Finance Tracker web application.
Run with:   python app.py
Then open:  http://127.0.0.1:5000
"""

from flask import Flask

from config import Config
from db import init_app as init_db


def create_app():
    """Create and configure the Flask app instance."""
    app = Flask(__name__)

    # Load settings from Config (DATABASE_URL, SECRET_KEY, cookie flags).
    app.config.from_object(Config)

    # Register the database cleanup helper so connections close after each request.
    init_db(app)

    # ----------------------------------------------------------------
    # Routes
    # ----------------------------------------------------------------

    @app.route("/")
    def index():
        return """
        <!DOCTYPE html>
        <html>
          <head>
            <title>Finance Tracker</title>
          </head>
          <body style="font-family: sans-serif; padding: 40px;">
            <h1>Finance Tracker</h1>
            <p>It works!</p>
            <p>Your Flask app is running at http://127.0.0.1:5000</p>
          </body>
        </html>
        """

    return app


# Create the app instance used by Flask's development server.
app = create_app()


if __name__ == "__main__":
    # debug=True enables auto-reload and detailed error pages.
    # Never use debug=True in production.
    app.run(host="127.0.0.1", port=5000, debug=True)