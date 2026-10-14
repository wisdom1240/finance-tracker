# Live Testing Report — Finance Tracker

**Date:** 14 October 2026
**Tester:** Wisdom Obinna
**URL:** https://finance-tracker-1196.onrender.com

## Summary

All live tests passed on desktop and mobile. The app works on any device with an internet connection, at any location.

## Desktop Tests

| Test | Result |
|---|---|
| Cold load (after spin-down) | PASS |
| Register new user | PASS |
| Login | PASS |
| Add transactions | PASS |
| Create budget | PASS |
| Create savings goal + add funds | PASS |
| Reports render correctly | PASS |
| 404 page branded correctly | PASS |

## Phone Tests (mobile data, no WiFi)

| Test | Result |
|---|---|
| URL loads on mobile data | PASS |
| Login (sees desktop data) | PASS |
| Hamburger menu opens/closes | PASS |
| Table scrolls horizontally | PASS |
| Add transaction from phone | PASS |
| Desktop sees phone-added data | PASS |
| Charts render on phone | PASS |

## Cross-Device Verification

- Data flows from phone → desktop ✅
- Full user isolation per account ✅
- Works on any device, any location ✅

**Status: PASS**