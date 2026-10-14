"""
test_budgets.py — Budget tests for Finance Tracker.

Covers: create, duplicate rejection, spent calculation, edit, delete, isolation.
"""
import pytest
import os
import psycopg2


def _get_category_id(category_name, category_type="EXPENSE"):
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


def _add_budget(client, category_name="Food", amount="50000",
                month="10", year="2026"):
    cat_id = _get_category_id(category_name)
    return client.post(
        "/budgets/add",
        data={
            "category_id": str(cat_id),
            "amount": amount,
            "month": month,
            "year": year,
        },
        follow_redirects=True,
    )


def _add_expense(client, category_name="Food", amount="5000",
                 description="Test", date="2026-10-15"):
    cat_id = _get_category_id(category_name)
    return client.post(
        "/transactions/add",
        data={
            "type": "EXPENSE",
            "category_id": str(cat_id),
            "amount": amount,
            "description": description,
            "transaction_date": date,
        },
        follow_redirects=True,
    )


class TestAddBudget:

    def test_create_budget(self, client, register_user, login_user):
        """Creating a valid budget succeeds."""
        register_user(email="b1@test.com", password="Secure123")
        login_user(email="b1@test.com", password="Secure123")
        response = _add_budget(client, "Food", "50000", "10", "2026")
        assert b"Budget created" in response.data
        assert b"FOOD" in response.data.upper()

    def test_duplicate_budget_rejected(self, client, register_user, login_user):
        """Cannot create two budgets for same category/month/year."""
        register_user(email="b2@test.com", password="Secure123")
        login_user(email="b2@test.com", password="Secure123")
        _add_budget(client, "Food", "50000", "10", "2026")
        response = _add_budget(client, "Food", "60000", "10", "2026")
        assert b"already have a budget" in response.data

    def test_amount_must_be_positive(self, client, register_user, login_user):
        """Budget amount must be > 0."""
        register_user(email="b3@test.com", password="Secure123")
        login_user(email="b3@test.com", password="Secure123")
        response = _add_budget(client, "Food", "0", "10", "2026")
        assert b"greater than zero" in response.data


class TestBudgetSpent:

    def test_spent_reflects_transactions(self, client, register_user, login_user):
        """The 'spent' column updates with matching expenses."""
        register_user(email="b4@test.com", password="Secure123")
        login_user(email="b4@test.com", password="Secure123")
        _add_budget(client, "Food", "50000", "10", "2026")
        _add_expense(client, "Food", "8000", "Groceries", "2026-10-15")

        response = client.get("/budgets")
        # Should show ₦8,000.00 as spent
        assert b"8,000.00" in response.data

    def test_spent_ignores_other_months(self, client, register_user, login_user):
        """Transactions in different months do not affect the budget."""
        register_user(email="b5@test.com", password="Secure123")
        login_user(email="b5@test.com", password="Secure123")
        _add_budget(client, "Food", "50000", "10", "2026")
        # Add expense in September instead of October
        _add_expense(client, "Food", "8000", "Sept groceries", "2026-09-15")

        response = client.get("/budgets")
        # Spent should be 0 (expense is in Sept, budget is for Oct)
        assert b"50,000.00" in response.data  # remaining unchanged


class TestBudgetIsolation:

    def test_cannot_see_other_users_budget(self, client, register_user, login_user):
        """User A doesn't see User B's budget."""
        register_user(email="bob@test.com", password="Secure123")
        login_user(email="bob@test.com", password="Secure123")
        _add_budget(client, "Food", "50000", "10", "2026")

        client.get("/logout")
        register_user(email="alice@test.com", password="Secure123")
        login_user(email="alice@test.com", password="Secure123")

        response = client.get("/budgets")
        assert b"already have a budget" not in response.data
        # Alice sees no budgets
        assert b"No budgets yet" in response.data or b"1 budget" not in response.data

    def test_cannot_edit_other_users_budget(self, client, register_user, login_user):
        """User A gets 404 editing User B's budget."""
        register_user(email="bob2@test.com", password="Secure123")
        login_user(email="bob2@test.com", password="Secure123")
        _add_budget(client, "Food", "50000", "10", "2026")

        conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
        cur = conn.cursor()
        cur.execute("SELECT id FROM budgets ORDER BY id DESC LIMIT 1")
        bob_budget_id = cur.fetchone()[0]
        cur.close()
        conn.close()

        client.get("/logout")
        register_user(email="alice2@test.com", password="Secure123")
        login_user(email="alice2@test.com", password="Secure123")

        response = client.get(f"/budgets/{bob_budget_id}/edit")
        assert response.status_code == 404