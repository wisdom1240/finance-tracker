"""
app.py
Entry point for the Finance Tracker web application.
"""

import re
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, g
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from db import init_app as init_db, get_db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_required(view):
    """Decorator: redirect to /login if no user is in the session."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)

    @app.before_request
    def load_user():
        """Attach the logged-in user's id to g for use in views."""
        g.user_id = session.get("user_id")

    @app.route("/")
    def index():
        return render_template("index.html")

    # ----------------------------------------------------------------
    # Registration
    # ----------------------------------------------------------------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        form_data = None

        if request.method == "POST":
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")

            form_data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
            }

            errors = []

            if not first_name:
                errors.append("First name is required.")
            if not last_name:
                errors.append("Last name is required.")
            if not email:
                errors.append("Email is required.")
            elif not EMAIL_RE.match(email):
                errors.append("Please enter a valid email address.")
            if not password:
                errors.append("Password is required.")
            elif len(password) < 8:
                errors.append("Password must be at least 8 characters.")
            elif not re.search(r"[A-Za-z]", password):
                errors.append("Password must contain at least one letter.")
            elif not re.search(r"[0-9]", password):
                errors.append("Password must contain at least one number.")
            if password != confirm:
                errors.append("Passwords do not match.")

            if not errors:
                db = get_db()
                cur = db.cursor()
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cur.fetchone() is not None:
                    errors.append("An account with that email already exists.")
                cur.close()

            if errors:
                for e in errors:
                    flash(e, "error")
            else:
                password_hash = generate_password_hash(password)
                db = get_db()
                cur = db.cursor()
                cur.execute(
                    "INSERT INTO users (first_name, last_name, email, password_hash) "
                    "VALUES (%s, %s, %s, %s)",
                    (first_name, last_name, email, password_hash),
                )
                db.commit()
                cur.close()

                flash("Account created successfully. Please log in.", "success")
                return redirect(url_for("login"))

        return render_template("register.html", form_data=form_data)

    # ----------------------------------------------------------------
    # Login
    # ----------------------------------------------------------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        form_data = None

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            form_data = {"email": email}

            if not email or not password:
                flash("Email and password are required.", "error")
            else:
                db = get_db()
                cur = db.cursor()
                cur.execute(
                    "SELECT id, first_name, password_hash FROM users WHERE email = %s",
                    (email,),
                )
                row = cur.fetchone()
                cur.close()

                # Generic error message: never reveal which field was wrong.
                if row is None or not check_password_hash(row[2], password):
                    flash("Invalid email or password.", "error")
                else:
                    session.clear()
                    session["user_id"] = row[0]
                    session["user_name"] = row[1]

                    flash(f"Welcome back, {row[1]}!", "success")
                    return redirect(url_for("index"))

        return render_template("login.html", form_data=form_data)

    # ----------------------------------------------------------------
    # Logout
    # ----------------------------------------------------------------
    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)