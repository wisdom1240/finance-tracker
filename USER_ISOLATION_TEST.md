# User Isolation Test Report — Finance Tracker

**Date:** 14 October 2026
**Tester:** Wisdom Obinna
**Stage:** 37 (formal verification)
**Reference:** Project Brief Section 6, item 7

## Objective

Formally verify that a logged-in user cannot see, edit, or delete another user's data — even by directly constructing URLs with another user's resource ID.

## Test Accounts

| User | Email | Password |
|---|---|---|
| Alice | alice@isolate.test | Alice1234 |
| Bob | bob@isolate.test | Bob12345 |

## Test Data

**Alice's data:**
- INCOME: Salary ₦200,000 ("Alice salary")
- EXPENSE: Transport ₦1,500 ("Alice taxi")
- Budget: Transport ₦30,000 (current month)
- Savings goal: "Alice goal" ₦100,000

**Bob's data:**
- INCOME: Salary ₦100,000 ("Bob salary")
- EXPENSE: Food ₦500 ("Bob lunch")
- Budget: Food ₦20,000 (current month)
- Savings goal: "Bob goal" ₦50,000

## Results

### Alice's View (Logged in as alice@isolate.test)

| Check | Expected | Actual | Result |
|---|---|---|---|
| Dashboard total income | ₦200,000 (Alice only) | ₦200,000 | PASS |
| Dashboard total expenses | ₦1,500 (Alice only) | ₦1,500 | PASS |
| Transactions visible | Only Alice's 2 | Only Alice's 2 | PASS |
| "Bob salary" visible | NO | NO | PASS |
| "Bob lunch" visible | NO | NO | PASS |
| Budgets visible | Only Alice's Transport budget | Only Alice's Transport budget | PASS |
| Savings visible | Only "Alice goal" | Only "Alice goal" | PASS |

### Cross-User Access Attempts (Alice → Bob's data)

| Attempt | URL | Expected | Actual | Result |
|---|---|---|---|---|
| Edit Bob's transaction | `/transactions/<bob_tx_id>/edit` | 404 | 404 | PASS |
| Edit Bob's budget | `/budgets/<bob_budget_id>/edit` | 404 | 404 | PASS |
| Edit nonexistent transaction | `/transactions/99999/edit` | 404 | 404 | PASS |
| Edit nonexistent budget | `/budgets/99999/edit` | 404 | 404 | PASS |

**Note:** Alice receives the *identical* 404 for "Bob's transaction" and "a made-up ID." She cannot determine whether Bob's resources exist. This is the correct security behaviour — existence is not leaked.

### Bob's View (Logged in as bob@isolate.test)

| Check | Expected | Actual | Result |
|---|---|---|---|
| Dashboard total income | ₦100,000 (Bob only) | ₦100,000 | PASS |
| Dashboard total expenses | ₦500 (Bob only) | ₦500 | PASS |
| Transactions visible | Only Bob's 2 | Only Bob's 2 | PASS |
| "Alice salary" visible | NO | NO | PASS |
| "Alice taxi" visible | NO | NO | PASS |
| Savings visible | Only "Bob goal" | Only "Bob goal" | PASS |

## Implementation Reference

Every user-scoped query in `app.py` includes `WHERE user_id = %s` with the session user's ID.

Example from `edit_transaction`:

```python
cur.execute(
    "SELECT id, type, category_id, amount, description, transaction_date "
    "FROM transactions "
    "WHERE id = %s AND user_id = %s",
    (transaction_id, user_id),
)
transaction = cur.fetchone()
if transaction is None:
    abort(404)