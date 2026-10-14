"""
test_transactions.py — Transaction CRUD tests for Finance Tracker.

Covers: add income, add expense, validation, edit, delete,
        search/filter, and user isolation.

Note: The TestUserIsolation class is marked `serial` because its tests
depend on specific data ordering and cannot safely run in parallel.
"""
import pytest
import os
import psycopg2


def _login(client, email, password):
    return client.post(
        "/login", data={"email": email, "password": password},
        follow_redirects=True,
    )


def _get_category_id(category_name, category_type):
    """Look up a category ID from the test database."""
    conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM categories WHERE name = %s AND type = %s",
        (category_name, category_type),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0]


def _add_transaction(client, t_type="EXPENSE", category_name="Food",
                     amount="5000", description="Test transaction"):
    """Look up a category by name, then POST a transaction."""
    category_id = _get_category_id(category_name, t_type)
    return client.post(
        "/transactions/add",
        data={
            "type": t_type,
            "category_id": str(category_id),
            "amount": amount,
            "description": description,
            "transaction_date": "2026-10-15",
        },
        follow_redirects=True,
    )


class TestAddTransaction:

    def test_add_expense(self, client, register_user, login_user):
        """A valid expense is saved and appears on the dashboard."""
        register_user(email="add@test.com", password="Secure123")
        login_user(email="add@test.com", password="Secure123")
        response = _add_transaction(client, "EXPENSE", "Food", "5000", "Lunch")
        assert response.status_code == 200
        assert b"Lunch" in response.data

    def test_add_income(self, client, register_user, login_user):
        """A valid income is saved and appears on the dashboard."""
        register_user(email="inc@test.com", password="Secure123")
        login_user(email="inc@test.com", password="Secure123")
        response = _add_transaction(client, "INCOME", "Salary", "200000", "October salary")
        assert b"October salary" in response.data

    def test_amount_must_be_positive(self, client, register_user, login_user):
        """Amount of 0 is rejected."""
        register_user(email="neg@test.com", password="Secure123")
        login_user(email="neg@test.com", password="Secure123")
        response = _add_transaction(client, "EXPENSE", "Food", "0", "Zero")
        assert b"greater than zero" in response.data

    def test_amount_cannot_be_negative(self, client, register_user, login_user):
        """Negative amount is rejected."""
        register_user(email="neg2@test.com", password="Secure123")
        login_user(email="neg2@test.com", password="Secure123")
        response = _add_transaction(client, "EXPENSE", "Food", "-500", "Bad")
        assert b"greater than zero" in response.data


class TestTransactionList:

    def test_list_shows_only_own_transactions(self, client, register_user, login_user):
        """A logged-in user sees only their own transactions."""
        register_user(email="usera@test.com", password="Secure123")
        login_user(email="usera@test.com", password="Secure123")
        _add_transaction(client, "EXPENSE", "Food", "1000", "User A lunch")

        client.get("/logout")
        register_user(email="userb@test.com", password="Secure123")
        login_user(email="userb@test.com", password="Secure123")
        _add_transaction(client, "EXPENSE", "Transport", "2000", "User B bus")

        response = client.get("/transactions")
        assert b"User B bus" in response.data
        assert b"User A lunch" not in response.data


class TestEditDelete:

    def test_edit_transaction(self, client, register_user, login_user):
        """Editing a transaction updates the value."""
        register_user(email="edit@test.com", password="Secure123")
        login_user(email="edit@test.com", password="Secure123")
        _add_transaction(client, "EXPENSE", "Food", "5000", "Original")

        conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
        cur = conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE description = 'Original'")
        row = cur.fetchone()
        cur.close()
        conn.close()
        assert row is not None, "The test transaction was not found in the database"
        tx_id = row[0]

        cat_id = _get_category_id("Transport", "EXPENSE")

        response = client.post(
            f"/transactions/{tx_id}/edit",
            data={
                "type": "EXPENSE",
                "category_id": str(cat_id),
                "amount": "9999",
                "description": "Updated",
                "transaction_date": "2026-10-15",
            },
            follow_redirects=True,
        )
        assert b"Updated" in response.data

    def test_delete_transaction(self, client, register_user, login_user):
        """Deleting a transaction removes it from the list."""
        register_user(email="del@test.com", password="Secure123")
        login_user(email="del@test.com", password="Secure123")
        _add_transaction(client, "EXPENSE", "Food", "5000", "ToDelete")

        conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
        cur = conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE description = 'ToDelete'")
        row = cur.fetchone()
        cur.close()
        conn.close()
        assert row is not None, "The test transaction was not found in the database"
        tx_id = row[0]

        client.post(f"/transactions/{tx_id}/delete", follow_redirects=True)

        conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM transactions WHERE id = %s", (tx_id,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        assert count == 0


@pytest.mark.serial
class TestUserIsolation:
    """The formal isolation tests. Marked 'serial' because they
    depend on specific data ordering and cannot run in parallel."""

    def test_cannot_edit_other_users_transaction(self, client, register_user, login_user):
        """User A cannot edit User B's transaction (404)."""
        register_user(email="bob@test.com", password="Secure123")
        login_user(email="bob@test.com", password="Secure123")
        _add_transaction(client, "EXPENSE", "Food", "3000", "Bob lunch")

        conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
        cur = conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE description = 'Bob lunch'")
        row = cur.fetchone()
        cur.close()
        conn.close()
        assert row is not None, "Bob's transaction was not found"
        bob_tx_id = row[0]

        client.get("/logout")
        register_user(email="alice@test.com", password="Secure123")
        login_user(email="alice@test.com", password="Secure123")

        response = client.get(f"/transactions/{bob_tx_id}/edit")
        assert response.status_code == 404

    def test_cannot_delete_other_users_transaction(self, client, register_user, login_user):
        """User A cannot delete User B's transaction (404)."""
        register_user(email="bob2@test.com", password="Secure123")
        login_user(email="bob2@test.com", password="Secure123")
        _add_transaction(client, "EXPENSE", "Food", "3000", "Bob2 lunch")

        conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
        cur = conn.cursor()
        cur.execute("SELECT id FROM transactions WHERE description = 'Bob2 lunch'")
        row = cur.fetchone()
        cur.close()
        conn.close()
        assert row is not None, "Bob's transaction was not found"
        bob_tx_id = row[0]

        client.get("/logout")
        register_user(email="alice2@test.com", password="Secure123")
        login_user(email="alice2@test.com", password="Secure123")

        response = client.post(f"/transactions/{bob_tx_id}/delete")
        assert response.status_code == 404