# Personal Finance Tracker

A full-stack, mobile-friendly web application to track personal income, expenses, budgets, and savings goals — with live charts, secure authentication, and strict user data isolation.

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?logo=postgresql)](https://neon.tech/)
[![Tests](https://img.shields.io/badge/tests-38%20passing-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## About

I built this app to solve a personal problem: I had no idea where my money was going each month. Existing apps were either too complex, too expensive, or locked behind a subscription. So I built my own.

The app tracks income and expenses across categories, sets monthly budgets with live progress bars, tracks savings goals with circular progress rings, and shows everything on a dashboard with live Chart.js visualizations. Every user's data is completely isolated — you can only see your own transactions, budgets, and goals.

**Built with:** Python 3.12, Flask, PostgreSQL (Neon), vanilla JavaScript, Chart.js.

---

## Features

### 🔐 Authentication
- Register, log in, log out with secure sessions
- Passwords hashed with Werkzeug (scrypt + salt)
- Server-side validation: minimum 8 characters with at least one letter and one number
- Generic login errors (prevents email enumeration attacks)
- CSRF protection on every form (Flask-WTF)
- Session cookies hardened (`HttpOnly`, `SameSite=Lax`)

### 💰 Transactions
- Record income and expenses with category, amount, description, and date
- Full CRUD: create, read, update, delete
- Search by description (case-insensitive)
- Filter by type, category, and date range
- Combined filters with shareable URLs

### 📊 Budgets
- Set monthly spending limits per category
- Live "spent" calculation — automatically updates when you add transactions
- Progress bars with color-coded thresholds (green / amber / red)
- Text status badges ("On track", "Warning", "Exceeded") — not colour-only
- Full accessibility (`role="progressbar"`, `aria-label`)

### 🎯 Savings Goals
- Create savings goals with target amount and optional deadline
- Add funds to increment progress
- Circular SVG progress rings showing percentage saved
- Progress updates in real-time

### 📈 Reports & Charts
- Date-range reports: this month, last month, this year, all time, custom range
- Category breakdowns with percentage bars
- **Dashboard charts:** doughnut (spending by category), bar (income vs expenses over 6 months)
- **Reports charts:** doughnut (category breakdown), line (daily expense trend)

### 📱 Design & Responsiveness
- Custom CSS design system with variables and components
- Premium typography (Inter + Plus Jakarta Sans)
- Fully responsive: desktop, tablet, mobile
- Mobile hamburger menu with smooth animation
- Page fade-in and staggered card animations

### 🛡️ Security
- **User isolation verified** — `WHERE user_id = %s` on every user-scoped query (22 instances)
- Parameterized SQL everywhere (prevents SQL injection)
- Accessing another user's resource returns `404` (existence is never leaked)
- Jinja auto-escaping — no XSS via user input
- SSL-enforced database connection
- Secrets in `.env` (never committed)

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, Flask 3.x |
| **Database** | PostgreSQL on Neon (cloud-hosted) |
| **Driver** | `psycopg2-binary` (raw parameterized SQL) |
| **Auth** | Werkzeug password hashing, Flask sessions |
| **CSRF** | Flask-WTF `CSRFProtect` |
| **Frontend** | HTML5, custom CSS, vanilla JavaScript |
| **Charts** | Chart.js (loaded via CDN) |
| **Deployment** | Render (backend) + Neon (database) |
| **Testing** | pytest (38 automated tests) |

---

## Screenshots

### Dashboard — metrics + doughnut chart + bar chart
![Dashboard](static/images/screenshots/dashboard.png)

### Transactions — table with search and filters
![Transactions](static/images/screenshots/transactions.png)

### Budgets — progress bars with status labels
![Budgets](static/images/screenshots/budgets.png)

### Savings Goals — circular progress rings
![Savings](static/images/screenshots/savings.png)

> Screenshots coming soon — will be added after deployment.

---

## Getting Started

### Prerequisites

- **Python 3.12** (via [Anaconda or Miniconda](https://docs.conda.io/en/latest/miniconda.html))
- **Git** ([download](https://git-scm.com/))
- A **PostgreSQL database** — free tier at [Neon](https://neon.tech/) works perfectly

### 1. Clone the repository

```bash
git clone https://github.com/wisdom1240/finance-tracker.git
cd finance-tracker