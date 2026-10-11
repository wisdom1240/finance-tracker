# Manual Testing Report — Finance Tracker

**Date:** 11 October 2026
**Version:** 1.0 (pre-deployment)
**Tester:** Wisdom Obinna

## Summary

All features tested manually. **All passed.**

| Category | Tests | Passed | Failed |
|---|---|---|---|
| Authentication | 10 | 10 | 0 |
| Transactions | 10 | 10 | 0 |
| Budgets | 5 | 5 | 0 |
| Savings Goals | 3 | 3 | 0 |
| Reports | 2 | 2 | 0 |
| Errors & Security | 3 | 3 | 0 |
| Mobile / Responsive | 3 | 3 | 0 |
| **Total** | **36** | **36** | **0** |

## What was tested

### Authentication
- Registration with valid input
- Duplicate email rejection
- Password rules (length, letter, number)
- Mismatched password rejection
- Login with correct/wrong credentials
- Generic error for nonexistent email
- Logout

### Transactions
- Add income and expense
- Amount validation (rejects 0 and negative)
- Category validation
- Filter by type
- Search by description
- SQL injection attempt fails safely
- Edit amount (dashboard recalculates)
- Delete with confirmation
- Cross-user access returns 404

### Budgets
- Create with category/month/year
- Live "spent" calculation from transactions
- Duplicate budget rejection
- Edit amount
- Delete

### Savings Goals
- Create with target and starting amount
- Add funds (ring updates)
- Delete

### Reports
- Range presets (this month, last month, this year, all time)
- Custom date range
- Empty state for no data

### Errors & Security
- Branded 404 page
- Auth protection (logged-out redirect)
- 404 for nonexistent or cross-user resources

### Mobile / Responsive
- Hamburger menu works
- Tables scroll horizontally
- Charts fit on narrow screens

## Conclusion

The application is functionally complete and ready for automated testing (Stage 38) and deployment (Stage 43).