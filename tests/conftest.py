"""
conftest.py — shared pytest fixtures for Finance Tracker tests.

Every test runs against the ISOLATED test database (TEST_DATABASE_URL),
never the production one. The database is wiped clean between tests.
"""
import os
import sys
import pytest
import psycopg2
from dotenv import load_dotenv

# Make the project root importable so tests can `from app import create_app`.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()


@pytest.fixture(scope="session", autouse=True)
def _check_test_db():
    """Guard: refuse to run if TEST_DATABASE_URL looks like the production DB."""
    test_url = os.environ.get("TEST_DATABASE_URL", "")
    prod_url = os.environ.get("DATABASE_URL", "")
    assert test_url, "TEST_DATABASE_URL is not set in .env"
    assert test_url != prod_url, "TEST_DATABASE_URL must differ from DATABASE_URL"
    assert "finance_tracker_test" in test_url, (
        "TEST_DATABASE_URL must point at a database named finance_tracker_test"
    )
    yield


@pytest.fixture(autouse=True)
def clean_tables():
    """Wipe users + transactions + budgets + savings_goals before every test.

    Categories are preserved (they are seed data).
    """
    conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
    cur = conn.cursor()
    cur.execute(
        "TRUNCATE TABLE transactions, budgets, savings_goals, users "
        "RESTART IDENTITY CASCADE"
    )
    conn.commit()
    cur.close()
    conn.close()
    yield


@pytest.fixture
def app():
    """Return a Flask app instance wired to the test database."""
    # Point the app at the test database for the duration of the test.
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

    # Reload config so it picks up the swapped DATABASE_URL.
    import importlib
    import config as config_module
    importlib.reload(config_module)

    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False  # disable CSRF in tests
    return application


@pytest.fixture
def client(app):
    """Flask test client for making HTTP requests against the test app."""
    return app.test_client()


@pytest.fixture
def db_conn():
    """Direct database connection for verifying test side effects."""
    conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
    yield conn
    conn.close()


@pytest.fixture
def register_user(client):
    """Helper fixture: registers a user and returns their credentials."""
    def _register(email="test@example.com", password="Secure123",
                  first_name="Test", last_name="User"):
        return client.post(
            "/register",
            data={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": password,
                "confirm_password": password,
            },
            follow_redirects=True,
        )
    return _register


@pytest.fixture
def login_user(client):
    """Helper fixture: logs a user in and returns the response."""
    def _login(email="test@example.com", password="Secure123"):
        return client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )
    return _login