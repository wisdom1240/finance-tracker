"""
app.py
Entry point for the Finance Tracker web application.
"""

import re

from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash

from config import Config
from db import init_app as init_db, get_db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)

    @app.route("/")
    def index():
        return render_template("index.html")

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

                flash("Account created successfully. Please login.", "success")
                return redirect(url_for("index"))

        return render_template("register.html", form_data=form_data)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)