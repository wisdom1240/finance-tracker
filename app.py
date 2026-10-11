"""
app.py
Entry point for the Finance Tracker web application.
"""

import re
from functools import wraps
from datetime import date, timedelta
from calendar import monthrange

import psycopg2.extras

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, g, abort
)
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from db import init_app as init_db, get_db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MONTH_NAMES = [
    (1, "January"), (2, "February"), (3, "March"), (4, "April"),
    (5, "May"), (6, "June"), (7, "July"), (8, "August"),
    (9, "September"), (10, "October"), (11, "November"), (12, "December"),
]
MONTH_LOOKUP = dict(MONTH_NAMES)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def _date_range(preset, custom_from, custom_to):
    today = date.today()
    if preset == "last_month":
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        start = last_prev.replace(day=1)
        end = last_prev
    elif preset == "this_year":
        start = date(today.year, 1, 1)
        end = date(today.year, 12, 31)
    elif preset == "all_time":
        start = date(1970, 1, 1)
        end = today
    elif preset == "custom":
        try:
            start = date.fromisoformat(custom_from)
        except (TypeError, ValueError):
            start = today.replace(day=1)
        try:
            end = date.fromisoformat(custom_to)
        except (TypeError, ValueError):
            end = today
    else:
        start = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        end = today.replace(day=last_day)
    return start, end


def _float_list(decimals):
    """Convert a list of Decimal to a list of floats (for Chart.js)."""
    return [float(d) for d in decimals]


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    csrf = CSRFProtect(app)

    # ----------------------------------------------------------------
    # Error handlers
    # ----------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", code=404), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("error.html", code=500), 500

    @app.before_request
    def load_user():
        g.user_id = session.get("user_id")

    @app.route("/")
    def index():
        return render_template("index.html")

    # ----------------------------------------------------------------
    # Dashboard (with chart data)
    # ----------------------------------------------------------------
    @app.route("/dashboard")
    @login_required
    def dashboard():
        user_id = session["user_id"]

        db = get_db()
        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions "
            "WHERE user_id = %s AND type = 'INCOME'",
            (user_id,),
        )
        total_income = cur.fetchone()["total"]

        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions "
            "WHERE user_id = %s AND type = 'EXPENSE'",
            (user_id,),
        )
        total_expenses = cur.fetchone()["total"]
        balance = total_income - total_expenses

        cur.execute(
            "SELECT t.id, t.type, t.amount, t.description, t.transaction_date, "
            "       c.name AS category_name "
            "FROM transactions t "
            "JOIN categories c ON c.id = t.category_id "
            "WHERE t.user_id = %s "
            "ORDER BY t.transaction_date DESC, t.id DESC "
            "LIMIT 5",
            (user_id,),
        )
        recent_transactions = cur.fetchall()

        today = date.today()
        month_start = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        month_end = today.replace(day=last_day)

        cur.execute(
            "SELECT c.name AS category_name, SUM(t.amount) AS total "
            "FROM transactions t "
            "JOIN categories c ON c.id = t.category_id "
            "WHERE t.user_id = %s AND t.type = 'EXPENSE' "
            "  AND t.transaction_date >= %s AND t.transaction_date <= %s "
            "GROUP BY c.name "
            "ORDER BY total DESC",
            (user_id, month_start, month_end),
        )
        cat_rows = cur.fetchall()
        category_labels = [r["category_name"] for r in cat_rows]
        category_values = _float_list([r["total"] for r in cat_rows])

        monthly_labels = []
        monthly_income = []
        monthly_expense = []

        for i in range(5, -1, -1):
            d = today.replace(day=1)
            month_index = d.month - 1 - i
            year_offset = month_index // 12
            month_of = month_index % 12 + 1
            y = d.year + year_offset
            m = month_of

            first = date(y, m, 1)
            last = date(y, m, monthrange(y, m)[1])

            cur.execute(
                "SELECT "
                "  COALESCE(SUM(CASE WHEN type='INCOME'  THEN amount END), 0) AS income, "
                "  COALESCE(SUM(CASE WHEN type='EXPENSE' THEN amount END), 0) AS expenses "
                "FROM transactions "
                "WHERE user_id = %s AND transaction_date >= %s AND transaction_date <= %s",
                (user_id, first, last),
            )
            r = cur.fetchone()

            label = f"{MONTH_LOOKUP.get(m, str(m))[:3]} {y}"
            monthly_labels.append(label)
            monthly_income.append(float(r["income"]))
            monthly_expense.append(float(r["expenses"]))

        cur.close()

        return render_template(
            "dashboard.html",
            total_income=total_income,
            total_expenses=total_expenses,
            balance=balance,
            recent_transactions=recent_transactions,
            category_labels=category_labels,
            category_values=category_values,
            monthly_labels=monthly_labels,
            monthly_income=monthly_income,
            monthly_expense=monthly_expense,
        )

    # ----------------------------------------------------------------
    # Reports
    # ----------------------------------------------------------------
    @app.route("/reports")
    @login_required
    def reports():
        user_id = session["user_id"]

        preset = request.args.get("range", "this_month").strip()
        if preset not in ("this_month", "last_month", "this_year", "all_time", "custom"):
            preset = "this_month"

        custom_from = request.args.get("from", "").strip()
        custom_to = request.args.get("to", "").strip()
        start, end = _date_range(preset, custom_from, custom_to)

        db = get_db()
        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute(
            "SELECT "
            "  COALESCE(SUM(CASE WHEN type='INCOME'  THEN amount END), 0) AS income, "
            "  COALESCE(SUM(CASE WHEN type='EXPENSE' THEN amount END), 0) AS expenses, "
            "  COUNT(*) AS tx_count "
            "FROM transactions "
            "WHERE user_id = %s AND transaction_date >= %s AND transaction_date <= %s",
            (user_id, start, end),
        )
        row = cur.fetchone()
        total_income = row["income"]
        total_expenses = row["expenses"]
        transaction_count = row["tx_count"]
        net = total_income - total_expenses

        cur.execute(
            "SELECT c.name AS category_name, SUM(t.amount) AS total "
            "FROM transactions t "
            "JOIN categories c ON c.id = t.category_id "
            "WHERE t.user_id = %s AND t.type = 'EXPENSE' "
            "  AND t.transaction_date >= %s AND t.transaction_date <= %s "
            "GROUP BY c.name ORDER BY total DESC",
            (user_id, start, end),
        )
        expense_rows = cur.fetchall()

        cur.execute(
            "SELECT c.name AS category_name, SUM(t.amount) AS total "
            "FROM transactions t "
            "JOIN categories c ON c.id = t.category_id "
            "WHERE t.user_id = %s AND t.type = 'INCOME' "
            "  AND t.transaction_date >= %s AND t.transaction_date <= %s "
            "GROUP BY c.name ORDER BY total DESC",
            (user_id, start, end),
        )
        income_rows = cur.fetchall()

        cur.execute(
            "SELECT transaction_date, SUM(amount) AS total "
            "FROM transactions "
            "WHERE user_id = %s AND type = 'EXPENSE' "
            "  AND transaction_date >= %s AND transaction_date <= %s "
            "GROUP BY transaction_date ORDER BY transaction_date",
            (user_id, start, end),
        )
        trend_rows = cur.fetchall()
        cur.close()

        category_breakdown = []
        if expense_rows and total_expenses > 0:
            for r in expense_rows:
                pct = float(r["total"] / total_expenses * 100)
                category_breakdown.append({
                    "category_name": r["category_name"],
                    "total": r["total"],
                    "percent": pct,
                })

        income_breakdown = []
        if income_rows and total_income > 0:
            for r in income_rows:
                pct = float(r["total"] / total_income * 100)
                income_breakdown.append({
                    "category_name": r["category_name"],
                    "total": r["total"],
                    "percent": pct,
                })

        trend_labels = [r["transaction_date"].strftime("%d %b") for r in trend_rows]
        trend_values = _float_list([r["total"] for r in trend_rows])

        category_labels = [r["category_name"] for r in expense_rows]
        category_values = _float_list([r["total"] for r in expense_rows])

        return render_template(
            "reports.html",
            total_income=total_income,
            total_expenses=total_expenses,
            net=net,
            transaction_count=transaction_count,
            category_breakdown=category_breakdown,
            income_breakdown=income_breakdown,
            date_from=start.strftime("%d %b %Y"),
            date_to=end.strftime("%d %b %Y"),
            filters={
                "range": preset,
                "from": custom_from,
                "to": custom_to,
            },
            category_labels=category_labels,
            category_values=category_values,
            trend_labels=trend_labels,
            trend_values=trend_values,
        )

    # ----------------------------------------------------------------
    # Transactions
    # ----------------------------------------------------------------
    @app.route("/transactions")
    @login_required
    def transactions():
        user_id = session["user_id"]
        f_type = request.args.get("type", "").strip().upper()
        f_category = request.args.get("category_id", "").strip()
        f_from = request.args.get("from", "").strip()
        f_to = request.args.get("to", "").strip()
        f_q = request.args.get("q", "").strip()

        where = ["t.user_id = %s"]
        params = [user_id]

        if f_type in ("INCOME", "EXPENSE"):
            where.append("t.type = %s")
            params.append(f_type)
        if f_category.isdigit():
            where.append("t.category_id = %s")
            params.append(int(f_category))
        if f_from:
            where.append("t.transaction_date >= %s")
            params.append(f_from)
        if f_to:
            where.append("t.transaction_date <= %s")
            params.append(f_to)
        if f_q:
            where.append("t.description ILIKE %s")
            params.append(f"%{f_q}%")

        where_sql = " AND ".join(where)

        db = get_db()
        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            f"SELECT t.id, t.type, t.amount, t.description, t.transaction_date, "
            f"       c.name AS category_name "
            f"FROM transactions t "
            f"JOIN categories c ON c.id = t.category_id "
            f"WHERE {where_sql} "
            f"ORDER BY t.transaction_date DESC, t.id DESC",
            tuple(params),
        )
        transactions = cur.fetchall()
        cur.execute("SELECT id, name, type FROM categories ORDER BY type, name")
        categories = cur.fetchall()
        cur.close()

        return render_template(
            "transactions.html",
            transactions=transactions,
            categories=categories,
            filters={"type": f_type, "category_id": f_category,
                     "from": f_from, "to": f_to, "q": f_q},
        )

    @app.route("/transactions/add", methods=["GET", "POST"])
    @login_required
    def add_transaction():
        user_id = session["user_id"]
        db = get_db()
        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, name, type FROM categories ORDER BY type, name")
        categories = cur.fetchall()
        cur.close()

        form_data = None
        if request.method == "POST":
            t_type = request.form.get("type", "").strip().upper()
            category_id = request.form.get("category_id", "").strip()
            amount = request.form.get("amount", "").strip()
            description = request.form.get("description", "").strip()
            transaction_date = request.form.get("transaction_date", "").strip()

            form_data = {
                "type": t_type,
                "category_id": int(category_id) if category_id.isdigit() else None,
                "amount": amount,
                "description": description,
                "transaction_date": transaction_date,
            }

            errors = []
            if t_type not in ("INCOME", "EXPENSE"):
                errors.append("Please choose a valid type.")
            if not category_id or not category_id.isdigit():
                errors.append("Please choose a category.")
            else:
                cur2 = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur2.execute("SELECT id, type FROM categories WHERE id = %s", (int(category_id),))
                cat = cur2.fetchone()
                cur2.close()
                if cat is None:
                    errors.append("That category does not exist.")
                elif cat["type"] != t_type:
                    errors.append("The category does not match the transaction type.")
            try:
                amount_dec = float(amount)
            except (TypeError, ValueError):
                amount_dec = None
            if amount_dec is None or amount_dec <= 0:
                errors.append("Amount must be greater than zero.")
            try:
                date.fromisoformat(transaction_date)
            except (TypeError, ValueError):
                errors.append("Please enter a valid date.")

            if errors:
                for e in errors:
                    flash(e, "error")
            else:
                cur3 = db.cursor()
                cur3.execute(
                    "INSERT INTO transactions "
                    "(user_id, category_id, type, amount, description, transaction_date) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, int(category_id), t_type, amount_dec,
                     description or None, transaction_date),
                )
                db.commit()
                cur3.close()
                flash("Transaction added successfully.", "success")
                return redirect(url_for("dashboard"))

        return render_template(
            "add_transaction.html",
            categories=categories,
            form_data=form_data,
            today=date.today().isoformat(),
        )

    @app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_transaction(transaction_id):
        user_id = session["user_id"]
        db = get_db()

        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, type, category_id, amount, description, transaction_date "
            "FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id),
        )
        transaction = cur.fetchone()
        cur.close()
        if transaction is None:
            abort(404)

        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, name, type FROM categories ORDER BY type, name")
        categories = cur.fetchall()
        cur.close()

        if request.method == "POST":
            t_type = request.form.get("type", "").strip().upper()
            category_id = request.form.get("category_id", "").strip()
            amount = request.form.get("amount", "").strip()
            description = request.form.get("description", "").strip()
            transaction_date = request.form.get("transaction_date", "").strip()

            errors = []
            if t_type not in ("INCOME", "EXPENSE"):
                errors.append("Please choose a valid type.")
            if not category_id or not category_id.isdigit():
                errors.append("Please choose a category.")
            else:
                cur2 = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur2.execute("SELECT id, type FROM categories WHERE id = %s", (int(category_id),))
                cat = cur2.fetchone()
                cur2.close()
                if cat is None:
                    errors.append("That category does not exist.")
                elif cat["type"] != t_type:
                    errors.append("The category does not match the transaction type.")
            try:
                amount_dec = float(amount)
            except (TypeError, ValueError):
                amount_dec = None
            if amount_dec is None or amount_dec <= 0:
                errors.append("Amount must be greater than zero.")
            try:
                date.fromisoformat(transaction_date)
            except (TypeError, ValueError):
                errors.append("Please enter a valid date.")

            if errors:
                for e in errors:
                    flash(e, "error")
                transaction = {
                    "id": transaction_id, "type": t_type,
                    "category_id": int(category_id) if category_id.isdigit() else None,
                    "amount": amount, "description": description,
                    "transaction_date": transaction_date,
                }
            else:
                cur3 = db.cursor()
                cur3.execute(
                    "UPDATE transactions SET category_id = %s, type = %s, amount = %s, "
                    "    description = %s, transaction_date = %s, updated_at = NOW() "
                    "WHERE id = %s AND user_id = %s",
                    (int(category_id), t_type, amount_dec, description or None,
                     transaction_date, transaction_id, user_id),
                )
                db.commit()
                cur3.close()
                flash("Transaction updated successfully.", "success")
                return redirect(url_for("transactions"))

        return render_template("edit_transaction.html",
                               transaction=transaction, categories=categories)

    @app.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
    @login_required
    def delete_transaction(transaction_id):
        user_id = session["user_id"]
        db = get_db()
        cur = db.cursor()
        cur.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s",
                    (transaction_id, user_id))
        deleted = cur.rowcount
        db.commit()
        cur.close()
        if deleted == 0:
            abort(404)
        flash("Transaction deleted successfully.", "success")
        return redirect(url_for("transactions"))

    # ----------------------------------------------------------------
    # Budgets
    # ----------------------------------------------------------------
    @app.route("/budgets")
    @login_required
    def budgets():
        user_id = session["user_id"]
        db = get_db()
        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT b.id, b.amount, b.month, b.year, c.name AS category_name, "
            "       COALESCE(("
            "           SELECT SUM(t.amount) FROM transactions t "
            "           WHERE t.user_id = b.user_id "
            "             AND t.category_id = b.category_id "
            "             AND t.type = 'EXPENSE' "
            "             AND EXTRACT(MONTH FROM t.transaction_date) = b.month "
            "             AND EXTRACT(YEAR  FROM t.transaction_date) = b.year"
            "       ), 0) AS spent "
            "FROM budgets b "
            "JOIN categories c ON c.id = b.category_id "
            "WHERE b.user_id = %s "
            "ORDER BY b.year DESC, b.month DESC, c.name",
            (user_id,),
        )
        rows = cur.fetchall()
        cur.close()

        budgets_list = []
        for r in rows:
            spent = r["spent"] or 0
            remaining = r["amount"] - spent
            budgets_list.append({
                "id": r["id"],
                "category_name": r["category_name"],
                "amount": r["amount"],
                "spent": spent,
                "remaining": remaining,
                "month": r["month"],
                "year": r["year"],
                "month_name": MONTH_LOOKUP.get(r["month"], str(r["month"])),
            })
        return render_template("budgets.html", budgets=budgets_list)

    @app.route("/budgets/add", methods=["GET", "POST"])
    @login_required
    def add_budget():
        user_id = session["user_id"]
        db = get_db()
        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, name FROM categories WHERE type = 'EXPENSE' ORDER BY name")
        categories = cur.fetchall()
        cur.close()

        form_data = None
        today = date.today()

        if request.method == "POST":
            category_id = request.form.get("category_id", "").strip()
            amount = request.form.get("amount", "").strip()
            month = request.form.get("month", "").strip()
            year = request.form.get("year", "").strip()

            form_data = {
                "category_id": int(category_id) if category_id.isdigit() else None,
                "amount": amount,
                "month": int(month) if month.isdigit() else None,
                "year": int(year) if year.isdigit() else None,
            }

            errors = []
            if not category_id or not category_id.isdigit():
                errors.append("Please choose a category.")
            else:
                cur2 = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur2.execute("SELECT id, type FROM categories WHERE id = %s", (int(category_id),))
                row = cur2.fetchone()
                cur2.close()
                if row is None:
                    errors.append("That category does not exist.")
                elif row["type"] != "EXPENSE":
                    errors.append("Budgets only apply to expense categories.")
            try:
                amount_dec = float(amount)
            except (TypeError, ValueError):
                amount_dec = None
            if amount_dec is None or amount_dec <= 0:
                errors.append("Budget amount must be greater than zero.")
            if not month.isdigit() or not (1 <= int(month) <= 12):
                errors.append("Please choose a valid month.")
            if not year.isdigit() or not (2000 <= int(year) <= 2100):
                errors.append("Please enter a valid year.")

            if not errors:
                cur3 = db.cursor()
                cur3.execute(
                    "SELECT id FROM budgets WHERE user_id = %s AND category_id = %s "
                    "  AND month = %s AND year = %s",
                    (user_id, int(category_id), int(month), int(year)),
                )
                if cur3.fetchone() is not None:
                    errors.append("You already have a budget for that category in that month.")
                cur3.close()

            if errors:
                for e in errors:
                    flash(e, "error")
            else:
                cur4 = db.cursor()
                cur4.execute(
                    "INSERT INTO budgets (user_id, category_id, amount, month, year) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (user_id, int(category_id), amount_dec, int(month), int(year)),
                )
                db.commit()
                cur4.close()
                flash("Budget created successfully.", "success")
                return redirect(url_for("budgets"))

        return render_template(
            "add_budget.html",
            categories=categories,
            form_data=form_data,
            months=MONTH_NAMES,
            current_month=today.month,
            current_year=today.year,
        )

    @app.route("/budgets/<int:budget_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_budget(budget_id):
        user_id = session["user_id"]
        db = get_db()

        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, category_id, amount, month, year FROM budgets "
            "WHERE id = %s AND user_id = %s",
            (budget_id, user_id),
        )
        budget = cur.fetchone()
        cur.close()
        if budget is None:
            abort(404)

        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id, name FROM categories WHERE type = 'EXPENSE' ORDER BY name")
        categories = cur.fetchall()
        cur.close()

        if request.method == "POST":
            category_id = request.form.get("category_id", "").strip()
            amount = request.form.get("amount", "").strip()
            month = request.form.get("month", "").strip()
            year = request.form.get("year", "").strip()

            errors = []
            if not category_id or not category_id.isdigit():
                errors.append("Please choose a category.")
            else:
                cur2 = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur2.execute("SELECT id, type FROM categories WHERE id = %s", (int(category_id),))
                row = cur2.fetchone()
                cur2.close()
                if row is None:
                    errors.append("That category does not exist.")
                elif row["type"] != "EXPENSE":
                    errors.append("Budgets only apply to expense categories.")
            try:
                amount_dec = float(amount)
            except (TypeError, ValueError):
                amount_dec = None
            if amount_dec is None or amount_dec <= 0:
                errors.append("Budget amount must be greater than zero.")
            if not month.isdigit() or not (1 <= int(month) <= 12):
                errors.append("Please choose a valid month.")
            if not year.isdigit() or not (2000 <= int(year) <= 2100):
                errors.append("Please enter a valid year.")

            if not errors:
                cur3 = db.cursor()
                cur3.execute(
                    "SELECT id FROM budgets WHERE user_id = %s AND category_id = %s "
                    "  AND month = %s AND year = %s AND id <> %s",
                    (user_id, int(category_id), int(month), int(year), budget_id),
                )
                if cur3.fetchone() is not None:
                    errors.append("You already have a budget for that category in that month.")
                cur3.close()

            if errors:
                for e in errors:
                    flash(e, "error")
                budget = {
                    "id": budget_id,
                    "category_id": int(category_id) if category_id.isdigit() else None,
                    "amount": amount,
                    "month": int(month) if month.isdigit() else None,
                    "year": int(year) if year.isdigit() else None,
                }
            else:
                cur4 = db.cursor()
                cur4.execute(
                    "UPDATE budgets SET category_id = %s, amount = %s, month = %s, year = %s "
                    "WHERE id = %s AND user_id = %s",
                    (int(category_id), amount_dec, int(month), int(year), budget_id, user_id),
                )
                db.commit()
                cur4.close()
                flash("Budget updated successfully.", "success")
                return redirect(url_for("budgets"))

        return render_template("edit_budget.html",
                               budget=budget, categories=categories, months=MONTH_NAMES)

    @app.route("/budgets/<int:budget_id>/delete", methods=["POST"])
    @login_required
    def delete_budget(budget_id):
        user_id = session["user_id"]
        db = get_db()
        cur = db.cursor()
        cur.execute("DELETE FROM budgets WHERE id = %s AND user_id = %s",
                    (budget_id, user_id))
        deleted = cur.rowcount
        db.commit()
        cur.close()
        if deleted == 0:
            abort(404)
        flash("Budget deleted successfully.", "success")
        return redirect(url_for("budgets"))

    # ----------------------------------------------------------------
    # Savings
    # ----------------------------------------------------------------
    @app.route("/savings")
    @login_required
    def savings():
        user_id = session["user_id"]
        db = get_db()
        cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, name, target_amount, current_amount, target_date "
            "FROM savings_goals WHERE user_id = %s "
            "ORDER BY target_date NULLS LAST, id DESC",
            (user_id,),
        )
        rows = cur.fetchall()
        cur.close()

        goals = []
        for r in rows:
            remaining = r["target_amount"] - r["current_amount"]
            if remaining < 0:
                remaining = 0
            goals.append({
                "id": r["id"],
                "name": r["name"],
                "target_amount": r["target_amount"],
                "current_amount": r["current_amount"],
                "remaining": remaining,
                "target_date": r["target_date"],
            })
        return render_template("savings.html", goals=goals)

    @app.route("/savings/add", methods=["GET", "POST"])
    @login_required
    def add_savings():
        user_id = session["user_id"]
        form_data = None

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            target_amount = request.form.get("target_amount", "").strip()
            current_amount = request.form.get("current_amount", "").strip() or "0"
            target_date = request.form.get("target_date", "").strip()

            form_data = {
                "name": name,
                "target_amount": target_amount,
                "current_amount": current_amount,
                "target_date": target_date,
            }

            errors = []
            if not name:
                errors.append("Goal name is required.")
            elif len(name) > 100:
                errors.append("Goal name must be 100 characters or fewer.")
            try:
                target_dec = float(target_amount)
            except (TypeError, ValueError):
                target_dec = None
            if target_dec is None or target_dec <= 0:
                errors.append("Target amount must be greater than zero.")
            try:
                current_dec = float(current_amount)
            except (TypeError, ValueError):
                current_dec = None
            if current_dec is None or current_dec < 0:
                errors.append("Already-saved amount cannot be negative.")
            if target_date:
                try:
                    date.fromisoformat(target_date)
                except (TypeError, ValueError):
                    errors.append("Please enter a valid target date.")
            else:
                target_date = None

            if errors:
                for e in errors:
                    flash(e, "error")
            else:
                db = get_db()
                cur = db.cursor()
                cur.execute(
                    "INSERT INTO savings_goals "
                    "(user_id, name, target_amount, current_amount, target_date) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (user_id, name, target_dec, current_dec, target_date),
                )
                db.commit()
                cur.close()
                flash("Savings goal created successfully.", "success")
                return redirect(url_for("savings"))

        return render_template("add_savings.html", form_data=form_data)

    @app.route("/savings/<int:goal_id>/add-funds", methods=["POST"])
    @login_required
    def add_savings_funds(goal_id):
        user_id = session["user_id"]
        amount = request.form.get("amount", "").strip()
        try:
            amount_dec = float(amount)
        except (TypeError, ValueError):
            amount_dec = None
        if amount_dec is None or amount_dec <= 0:
            flash("Amount must be greater than zero.", "error")
            return redirect(url_for("savings"))

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "UPDATE savings_goals "
            "SET current_amount = current_amount + %s, updated_at = NOW() "
            "WHERE id = %s AND user_id = %s",
            (amount_dec, goal_id, user_id),
        )
        updated = cur.rowcount
        db.commit()
        cur.close()
        if updated == 0:
            abort(404)
        flash(f"Added ₦{amount_dec:,.2f} to your goal.", "success")
        return redirect(url_for("savings"))

    @app.route("/savings/<int:goal_id>/delete", methods=["POST"])
    @login_required
    def delete_savings(goal_id):
        user_id = session["user_id"]
        db = get_db()
        cur = db.cursor()
        cur.execute("DELETE FROM savings_goals WHERE id = %s AND user_id = %s",
                    (goal_id, user_id))
        deleted = cur.rowcount
        db.commit()
        cur.close()
        if deleted == 0:
            abort(404)
        flash("Savings goal deleted successfully.", "success")
        return redirect(url_for("savings"))

    # ----------------------------------------------------------------
    # Auth
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

            form_data = {"first_name": first_name, "last_name": last_name, "email": email}
            errors = []

            if not first_name: errors.append("First name is required.")
            if not last_name: errors.append("Last name is required.")
            if not email: errors.append("Email is required.")
            elif not EMAIL_RE.match(email): errors.append("Please enter a valid email address.")
            if not password: errors.append("Password is required.")
            elif len(password) < 8: errors.append("Password must be at least 8 characters.")
            elif not re.search(r"[A-Za-z]", password):
                errors.append("Password must contain at least one letter.")
            elif not re.search(r"[0-9]", password):
                errors.append("Password must contain at least one number.")
            if password != confirm: errors.append("Passwords do not match.")

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
                cur = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute(
                    "SELECT id, first_name, password_hash FROM users WHERE email = %s",
                    (email,),
                )
                row = cur.fetchone()
                cur.close()

                if row is None or not check_password_hash(row["password_hash"], password):
                    flash("Invalid email or password.", "error")
                else:
                    session.clear()
                    session["user_id"] = row["id"]
                    session["user_name"] = row["first_name"]
                    flash(f"Welcome back, {row['first_name']}!", "success")
                    return redirect(url_for("dashboard"))

        return render_template("login.html", form_data=form_data)

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)