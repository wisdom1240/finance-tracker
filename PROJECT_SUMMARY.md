# Project Summary — Personal Finance Tracker V1

**Status:** ✅ Complete and deployed
**Started:** October 2026
**Completed:** October 2026

---

## What was built

A full-stack, mobile-friendly web application to track personal income, expenses, budgets, and savings goals — with live charts, secure authentication, and strict user data isolation.

**Live URL:** https://finance-tracker-1196.onrender.com
**Source:** https://github.com/wisdom1240/finance-tracker

---

## Features

- User registration, login, logout with secure sessions
- Income and expense tracking with categories
- Full CRUD on transactions
- Search and filters
- Monthly budgets with live "spent" calculation
- Savings goals with circular progress rings
- Date-range reports with category breakdowns
- Live charts (doughnut, bar, line)
- Responsive design (desktop, tablet, mobile)

---

## Tech Stack

- **Backend:** Python 3.12, Flask 3.x
- **Database:** PostgreSQL on Neon
- **Driver:** psycopg2-binary (raw parameterized SQL)
- **Server:** Gunicorn (production), Flask dev (local)
- **Auth:** Werkzeug scrypt hashing, Flask sessions
- **CSRF:** Flask-WTF
- **Frontend:** HTML5, custom CSS, vanilla JavaScript
- **Charts:** Chart.js
- **Deployment:** Render + Neon
- **Testing:** pytest (38 tests)

---

## Security

- 12-point security audit passed
- Passwords hashed with scrypt + salt
- Generic login errors (no email enumeration)
- CSRF protection on every POST form
- Session cookies hardened (HttpOnly, SameSite, Secure)
- User isolation: 22 user-scoped queries, all return 404 for cross-user access
- 100% parameterized SQL
- SSL-enforced database connection

---

## Testing

- 38 automated tests (auth, transactions, budgets, savings, isolation)
- Manual test report (36 items)
- User isolation formal report
- Live testing report (desktop + phone)

---

## Documentation

- README with badges, features, setup, security table
- MANUAL_TESTS.md — manual testing checklist
- USER_ISOLATION_TEST.md — formal isolation proof
- LIVE_TEST_REPORT.md — production verification
- V2_FEEDBACK.md — pending real-world feedback
- V2_ROADMAP.md — placeholder for Version 2 plan

---

## Timeline

- **Stages 1–13:** Environment setup, project structure, design system
- **Stages 14–16:** Authentication (register, login, logout)
- **Stages 17–27:** Four complete features (transactions, budgets, savings, reports)
- **Stage 28:** Chart.js integration
- **Stages 29–33:** Polish (mobile, UX, error pages, responsive, micro-interactions)
- **Stages 34–37:** Security, database, and manual testing verification
- **Stage 38:** Automated tests (38 pytest tests)
- **Stages 39–40:** README + GitHub
- **Stages 41–42:** Local end-to-end test + deployment prep
- **Stage 43:** Deployed to Render
- **Stage 44:** Live testing on desktop + phone
- **Stage 45:** V2 feedback (pending)
- **Stage 46:** V2 roadmap (placeholder)
- **Stage 47:** Final wrap-up

---

## What's next

**Version 2** — Will be planned after real-world use and feedback.

Candidates already discussed:
- Recurring transactions
- CSV / Excel / PDF export
- Dark mode
- Email notifications for budget warnings
- Spending insights
- Mobile-friendly table redesign

**Version 3** — JSON API + Android app.

---

## Author

**Wisdom Obinna**
- GitHub: [@wisdom1240](https://github.com/wisdom1240)
- Email: wobinna761@gmail.com