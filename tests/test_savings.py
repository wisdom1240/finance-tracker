"""
test_savings.py — Savings goal tests for Finance Tracker.

Covers: create, add funds, delete, isolation.
"""
import os
import psycopg2


def _add_goal(client, name="New Laptop", target="500000",
              current="0", target_date=""):
    return client.post(
        "/savings/add",
        data={
            "name": name,
            "target_amount": target,
            "current_amount": current,
            "target_date": target_date,
        },
        follow_redirects=True,
    )


class TestSavingsGoal:

    def test_create_goal(self, client, register_user, login_user):
        """Creating a valid savings goal succeeds."""
        register_user(email="s1@test.com", password="Secure123")
        login_user(email="s1@test.com", password="Secure123")
        response = _add_goal(client, "New Laptop", "500000", "0")
        assert b"New Laptop" in response.data

    def test_add_funds(self, client, register_user, login_user):
        """Adding funds increases the current amount."""
        register_user(email="s2@test.com", password="Secure123")
        login_user(email="s2@test.com", password="Secure123")
        _add_goal(client, "Emergency Fund", "100000", "0")

        conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
        cur = conn.cursor()
        cur.execute("SELECT id FROM savings_goals WHERE name = 'Emergency Fund'")
        goal_id = cur.fetchone()[0]
        cur.close()
        conn.close()

        client.post(
            f"/savings/{goal_id}/add-funds",
            data={"amount": "25000"},
            follow_redirects=True,
        )

        conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
        cur = conn.cursor()
        cur.execute("SELECT current_amount FROM savings_goals WHERE id = %s", (goal_id,))
        current = cur.fetchone()[0]
        cur.close()
        conn.close()
        assert float(current) == 25000.0

    def test_delete_goal(self, client, register_user, login_user):
        """Deleting a goal removes it."""
        register_user(email="s3@test.com", password="Secure123")
        login_user(email="s3@test.com", password="Secure123")
        _add_goal(client, "DeleteMe", "50000", "0")

        conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
        cur = conn.cursor()
        cur.execute("SELECT id FROM savings_goals WHERE name = 'DeleteMe'")
        goal_id = cur.fetchone()[0]
        cur.close()
        conn.close()

        client.post(f"/savings/{goal_id}/delete", follow_redirects=True)

        conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM savings_goals WHERE id = %s", (goal_id,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        assert count == 0


class TestSavingsIsolation:

    def test_cannot_see_other_users_goal(self, client, register_user, login_user):
        """User A cannot see User B's savings goal."""
        register_user(email="bob@test.com", password="Secure123")
        login_user(email="bob@test.com", password="Secure123")
        _add_goal(client, "Bob's secret goal", "100000", "0")

        client.get("/logout")
        register_user(email="alice@test.com", password="Secure123")
        login_user(email="alice@test.com", password="Secure123")

        response = client.get("/savings")
        assert b"Bob's secret goal" not in response.data

    def test_cannot_delete_other_users_goal(self, client, register_user, login_user):
        """User A gets 404 deleting User B's goal."""
        register_user(email="bob2@test.com", password="Secure123")
        login_user(email="bob2@test.com", password="Secure123")
        _add_goal(client, "Bob2 goal", "100000", "0")

        conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
        cur = conn.cursor()
        cur.execute("SELECT id FROM savings_goals WHERE name = 'Bob2 goal'")
        bob_goal_id = cur.fetchone()[0]
        cur.close()
        conn.close()

        client.get("/logout")
        register_user(email="alice2@test.com", password="Secure123")
        login_user(email="alice2@test.com", password="Secure123")

        response = client.post(f"/savings/{bob_goal_id}/delete")
        assert response.status_code == 404