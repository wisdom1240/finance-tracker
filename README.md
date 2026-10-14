# Personal Finance Tracker

A full-stack, mobile-friendly web application to track personal income, expenses, budgets, and savings goals — with live charts, secure authentication, and strict user data isolation.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791)
![Tests](https://img.shields.io/badge/tests-38%20passing-brightgreen)

---

## About

I built this app to solve a personal problem: I had no idea where my money was going each month. Existing apps were either too complex, too expensive, or locked behind a subscription. So I built my own.

The app tracks income and expenses across categories, sets monthly budgets with live progress bars, tracks savings goals with circular progress rings, and shows everything on a dashboard with live Chart.js visualizations. Every user's data is completely isolated.

**Built with:** Python 3.12, Flask, PostgreSQL (Neon), vanilla JavaScript, Chart.js.

---

## Features

### Authentication
- Register, log in, log out with secure sessions
- Passwords hashed with Werkzeug (scrypt + salt)
- Server-side validation: min 8 characters, one letter, one number
- Generic login errors (prevents email enumeration)
- CSRF protection on every form (Flask-WTF)
- Session cookies hardened (HttpOnly, SameSite=Lax)

### Transactions
- Record income and expenses with category, amount, description, date
- Full CRUD: create, read, update, delete
- Search by description (case-insensitive)
- Filter by type, category, and date range

### Budgets
- Set monthly spending limits per category
- Live "spent" calculation
- Progress bars with color-coded thresholds
- Text status badges (On track, Warning, Exceeded)
- Full accessibility (role="progressbar", aria-label)

### Savings Goals
- Create goals with target amount and optional deadline
- Add funds to increment progress
- Circular SVG progress rings showing percentage saved

### Reports and Charts
- Date-range reports: this month, last month, this year, all time, custom
- Category breakdowns with percentage bars
- Dashboard charts: doughnut, bar
- Reports charts: doughnut, line

### Security
- User isolation verified (WHERE user_id = %s on 22 queries)
- Parameterized SQL everywhere
- Cross-user access returns 404
- Jinja auto-escaping
- SSL-enforced database connection
- Secrets in .env (never committed)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask 3.x |
| Database | PostgreSQL on Neon |
| Driver | psycopg2-binary |
| Auth | Werkzeug, Flask sessions |
| CSRF | Flask-WTF CSRFProtect |
| Frontend | HTML5, custom CSS, vanilla JS |
| Charts | Chart.js (CDN) |
| Deployment | Render + Neon |
| Testing | pytest (38 tests) |

---

## Screenshots

Screenshots coming soon.

---

## Getting Started

### Prerequisites

- Python 3.12 (via Anaconda or Miniconda)
- Git
- A PostgreSQL database (Neon free tier works)

### 1. Clone

git clone https://github.com/wisdom1240/finance-tracker.git
cd finance-tracker

### 2. Create conda env

conda create -n finance-tracker python=3.12 -y
conda activate finance-tracker

### 3. Install dependencies

pip install -r requirements.txt

### 4. Set up the database

Create a Neon project, copy the connection string, then load the schema into it.

### 5. Configure environment

Create a .env file in the project root with:
- DATABASE_URL (your Neon connection string)
- SECRET_KEY (a random 64-character hex string)

See .env.example for the template.

### 6. Run

python app.py

Open http://127.0.0.1:5000 in your browser.

---

## Running Tests

38 automated tests covering auth, transactions, budgets, savings, and isolation.

Add TEST_DATABASE_URL to your .env file pointing at a separate test database.

Run all tests with: pytest tests/ -v

Expected: 38 passed.

---

## Project Structure

FinanceTracker/
- app.py (Flask app - routes and business logic)
- config.py (Configuration)
- db.py (Database connection helper)
- requirements.txt (Python dependencies)
- pytest.ini (pytest configuration)
- .env (Secrets - never committed)
- .env.example (Template)
- README.md
- MANUAL_TESTS.md
- USER_ISOLATION_TEST.md
- database/schema.sql
- templates/ (Jinja HTML templates)
- static/ (CSS, JS, images)
- tests/ (pytest test suite)

---

## Database Schema

Five tables:

- users - Account info
- categories - Shared income/expense categories
- transactions - Every income/expense record
- budgets - Monthly limits
- savings_goals - Targets and progress

Key design decisions:

- NUMERIC(12,2) for money, never FLOAT
- Composite index on (user_id, transaction_date DESC)
- Foreign keys with CASCADE and RESTRICT
- CHECK constraints for business rules
- UNIQUE constraint on budgets (user + category + month + year)

---

## Security

| Requirement | Implementation |
|---|---|
| Password hashing | Werkzeug scrypt |
| Password rules | Min 8, letter + number |
| Generic login errors | Same for wrong email or password |
| CSRF protection | Flask-WTF on every POST |
| Session cookies | HttpOnly, SameSite=Lax |
| Route protection | login_required decorator |
| User isolation | WHERE user_id = %s on 22 queries |
| Cross-user access | Returns 404 |
| SQL injection | 100% parameterized |
| XSS protection | Jinja auto-escape |
| Secrets | .env git-ignored |
| Database SSL | sslmode=require |

---

## Roadmap

Version 1 (current): Complete

Version 2 (planned): Recurring transactions, exports, dark mode, notifications, insights

Version 3 (planned): JSON API, Android app

---

## Author

Wisdom Obinna

- GitHub: https://github.com/wisdom1240
- Email: wobinna761@gmail.com

---

## License

MIT License
