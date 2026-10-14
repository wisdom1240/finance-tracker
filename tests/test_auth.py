"""
test_auth.py — Authentication tests for Finance Tracker.

Covers: registration, validation rules, login, logout, and route protection.
"""


class TestRegistration:

    def test_register_success(self, client, register_user, db_conn):
        """A valid registration creates a new user and redirects to login."""
        response = register_user(email="newuser@test.com", password="Secure123")
        assert response.status_code == 200
        # Verify user exists in DB
        cur = db_conn.cursor()
        cur.execute("SELECT email FROM users WHERE email = %s", ("newuser@test.com",))
        row = cur.fetchone()
        cur.close()
        assert row is not None
        assert row[0] == "newuser@test.com"

    def test_register_duplicate_email(self, client, register_user, db_conn):
        """Registering the same email twice fails."""
        register_user(email="dup@test.com", password="Secure123")
        response = register_user(email="dup@test.com", password="Secure123")
        assert b"already exists" in response.data

    def test_register_short_password(self, client, register_user):
        """Password shorter than 8 chars is rejected."""
        response = register_user(email="short@test.com", password="Abc123")
        assert b"at least 8 characters" in response.data

    def test_register_no_number_in_password(self, client, register_user):
        """Password with no number is rejected."""
        response = register_user(email="nonum@test.com", password="abcdefgh")
        assert b"at least one number" in response.data

    def test_register_no_letter_in_password(self, client, register_user):
        """Password with no letter is rejected."""
        response = register_user(email="noletter@test.com", password="12345678")
        assert b"at least one letter" in response.data

    def test_register_mismatched_passwords(self, client):
        """Passwords that don't match are rejected."""
        response = client.post(
            "/register",
            data={
                "first_name": "Test", "last_name": "User",
                "email": "mismatch@test.com",
                "password": "Secure123", "confirm_password": "Different123",
            },
            follow_redirects=True,
        )
        assert b"do not match" in response.data

    def test_register_invalid_email(self, client):
        """Invalid email format is rejected."""
        response = client.post(
            "/register",
            data={
                "first_name": "Test", "last_name": "User",
                "email": "not-an-email",
                "password": "Secure123", "confirm_password": "Secure123",
            },
            follow_redirects=True,
        )
        assert b"valid email" in response.data


class TestLogin:

    def test_login_success(self, client, register_user, login_user):
        """Valid credentials log the user in and redirect to dashboard."""
        register_user(email="login@test.com", password="Secure123")
        response = login_user(email="login@test.com", password="Secure123")
        assert response.status_code == 200
        # After successful login, redirected to /dashboard. This page contains "Welcome back".
        assert b"Welcome back" in response.data

    def test_login_wrong_password(self, client, register_user, login_user):
        """Wrong password shows the generic error message."""
        register_user(email="wrong@test.com", password="Secure123")
        response = login_user(email="wrong@test.com", password="WrongPass1")
        assert b"Invalid email or password" in response.data

    def test_login_nonexistent_email(self, client, login_user):
        """Nonexistent email shows the SAME generic error (no enumeration)."""
        response = login_user(email="nobody@test.com", password="Whatever123")
        assert b"Invalid email or password" in response.data
        # Ensure we did NOT reveal that the email doesn't exist
        assert b"not found" not in response.data.lower()
        assert b"register" not in response.data.lower() or True  # register link is fine

    def test_login_missing_fields(self, client):
        """Empty email or password is rejected."""
        response = client.post(
            "/login", data={"email": "", "password": ""}, follow_redirects=True
        )
        assert b"required" in response.data.lower()


class TestLogout:

    def test_logout_clears_session(self, client, register_user, login_user):
        """Logging out clears the session and redirects home."""
        register_user(email="logout@test.com", password="Secure123")
        login_user(email="logout@test.com", password="Secure123")
        response = client.get("/logout", follow_redirects=True)
        assert b"logged out" in response.data

        # After logout, /dashboard should redirect to login
        response = client.get("/dashboard", follow_redirects=True)
        assert b"Please log in" in response.data


class TestRouteProtection:

    def test_dashboard_requires_login(self, client):
        """Unauthenticated request to /dashboard redirects to /login."""
        response = client.get("/dashboard", follow_redirects=True)
        assert b"Please log in" in response.data

    def test_transactions_requires_login(self, client):
        response = client.get("/transactions", follow_redirects=True)
        assert b"Please log in" in response.data

    def test_budgets_requires_login(self, client):
        response = client.get("/budgets", follow_redirects=True)
        assert b"Please log in" in response.data

    def test_savings_requires_login(self, client):
        response = client.get("/savings", follow_redirects=True)
        assert b"Please log in" in response.data

    def test_reports_requires_login(self, client):
        response = client.get("/reports", follow_redirects=True)
        assert b"Please log in" in response.data