# Dealer Planner Monthly Forecast Scheduling
## Technical Analysis & Implementation Recommendation

**Prepared for:** Management Review
**Date:** April 21, 2026
**Scope:** Dealer Business Planner — EOS Platform

---

## Executive Summary

Dealers are requesting the ability to submit and update forecasts on a **monthly basis** rather than
entering all 12 months at once at the start of the year. This is technically feasible. The database
already stores data in monthly columns, and a partial locking mechanism already exists. However,
before monthly scheduling can be implemented reliably, a pre-existing year inconsistency bug must
be resolved first — it is actively causing some saves and reads to operate on different model year
rows in production today.

The recommended approach is a low-risk, date-driven implementation that requires no database schema
changes and minimal changes to the existing save/load logic.

---

## What Dealers Are Asking For

Currently, the planner opens once per year. Dealers fill in all 12 monthly forecast values
(August through July) at once and submit. The rep can then lock/unlock the dealer's submission
manually.

What dealers want:
- The planner opens **each month**
- They can enter or revise **that month's forecast** (and optionally upcoming months)
- Past months are **read-only** — they cannot go back and change history
- The process repeats automatically every month throughout the fiscal year (AUG → JUL)

This is a significant usability improvement and a reasonable business request. The system is
structurally closer to supporting this than it might appear.

---

## What Already Exists (Assets)

### 1. Monthly Data Model — Already Correct
The `dealer_forecast_new` table already stores 12 individual period columns:
```
period_1_fc (AUG) through period_12_fc (JUL)
```
No schema changes are required. The data structure was built for monthly forecasting from the start.

### 2. A Lock Mechanism Already Exists
`dealer_lock.js` and `dealer_unlock.js` already set a `locked` flag per dealer per year.
`startup_action.js` reads this flag and hides the Save button and sets fields to readonly.
This is the **same mechanism monthly scheduling would extend** — instead of one annual lock,
it becomes a monthly lock on past periods.

### 3. Read-Only Field Logic Already Exists
`startup_action.js` already contains jQuery logic that sets form inputs to `readonly`. The
pattern is established — it just needs to be driven by the current date rather than only the
manual lock flag.

### 4. Fiscal Year Structure Is Already Correct
The month array `['AUG', 'SEP', 'OCT', 'NOV', 'DEC', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL']`
maps to periods 1–12. The fiscal year already starts in August, which aligns exactly with
what a monthly rollout would need.

---

## What Does NOT Currently Exist (Gaps)

### Gap 1: Critical — Year Inconsistency Bug (Must Fix First)

This is a **live production bug** that must be resolved before any new feature work. Across the
14 JavaScript files reviewed, the model year is hardcoded differently in each file:

| File | Hardcoded Year | Impact |
|---|---|---|
| `startup_action.js` | 2025 | Loads 2025 forecast data on page load |
| `update_records.js` | 2025 | Dealer saves write to 2025 row |
| `update_rep_forecast.js` | **2024** | Rep saves write to 2024 row — different row than dealer |
| `signature_actions.js` | **2024** | Signature saves to 2024 record |
| `rep_forecast_print.js` | **2024** | Print report pulls from 2024 |
| `signature_clear.js` | **2023** | Clears signatures for model year 2023 |

Every file has this line commented out that was the original design intent:
```js
// var year = loadByListName('Current_Model_Year')[0].MODEL_YEAR;
```

This means right now in production: a dealer submits their forecast (saved to 2025), the rep
opens the rep tools and saves their rep forecast (saved to 2024), and the print report shows
2024 data. They are operating on different database rows simultaneously. This needs to be
corrected as standalone work regardless of the monthly scheduling feature.

### Gap 2: No Date-Awareness
The app has no logic to determine "what fiscal month is it right now." Everything is loaded on
page open and all 12 months are treated identically. To support monthly scheduling, the startup
script needs to compute the current fiscal period from the system date.

### Gap 3: No Monthly Open/Close Configuration
There is no table or configuration that defines "which month is currently open for editing."
This needs to be established — either as a calculated value from the date, or as an
admin-controlled setting in a configuration table.

### Gap 4: Rep Forecast and Dealer Forecast Are Saved Independently
The rep forecast save (`update_rep_forecast.js`) and the dealer forecast save
(`update_records.js`) are separate actions. Monthly scheduling needs to account for both —
a rep should still be able to enter their rep forecast for any month, while dealer edit rights
are restricted by period.

---

## Implementation Options

### Option A — Date-Driven (Recommended)
**How it works:** `startup_action.js` calculates the current fiscal month from `new Date()`.
All months prior to the current fiscal month are automatically set to readonly. The current
month and future months remain editable.

**Fiscal month calculation logic (conceptual):**
```
If calendar month >= August → fiscal period = calendar month - 7
If calendar month < August  → fiscal period = calendar month + 5
```
Example: October (calendar month 10) → fiscal period 3 (period_3 = OCT).
AUG and SEP become readonly automatically.

**Pros:**
- Fully automatic — no admin intervention needed each month
- No new database tables required
- Uses existing readonly pattern already in `startup_action.js`
- No scheduled jobs required

**Cons:**
- Business rules need to be defined (see questions below)
- Year rollover (August = start of new model year) needs careful handling

---

### Option B — JAMS-Driven Config Table
**How it works:** A JAMS job runs on the 1st of each month and writes the "currently open
period" to a configuration table in the database. `startup_action.js` reads this via
`loadByListName` and applies readonly logic accordingly.

**Pros:**
- Business has manual control — if they want to keep a month open longer, they update the
  config table
- Easy to audit (config table shows history of when windows opened/closed)

**Cons:**
- Requires a new database table
- Requires a new JAMS job
- If the JAMS job fails, the planner may not open correctly for that month

---

### Option C — Admin-Controlled Per-Month Window
**How it works:** An admin screen allows someone at Bennington to explicitly mark which months
are open for editing. Dealers only see editable fields for marked months.

**Pros:**
- Maximum flexibility — can open or re-open any month for any reason
- Useful for exceptions (e.g., re-opening October if a dealer had a system issue)

**Cons:**
- Requires the most development effort
- Requires an admin UI that does not currently exist

---

## Recommended Approach

### Phase 1 — Fix Year Bug (Prerequisite)
Restore the commented-out `Current_Model_Year` dynamic year loading in all 6 affected files.
This fixes the live production inconsistency and is required before any new feature is safe
to deploy. This is standalone work that should be done regardless of whether monthly scheduling
is pursued.

**Files requiring year fix:**
- `update_rep_forecast.js` (currently 2024, should match startup)
- `signature_actions.js` (currently 2024)
- `rep_forecast_print.js` (currently 2024)
- `signature_clear.js` (currently 2023 — actively deleting wrong year's records)

### Phase 2 — Monthly Scheduling (Option A + optional admin override)
Implement date-driven fiscal period calculation in `startup_action.js`. Set all months prior
to the current fiscal period to readonly automatically. The existing rep lock/unlock mechanism
remains intact so reps can still manually override per dealer when needed.

This gives dealers automatic monthly access without requiring any scheduled jobs or new
database tables.

---

## Business Rules That Need Answers Before Development

The following decisions need to come from the business before any code is written:

1. **How far ahead can dealers forecast?**
   Can they enter August, September, and October all at once in August?
   Or only the current fiscal month?

2. **Can dealers revise the current month, or only enter it once?**
   Example: can a dealer go back and change their October forecast while it's still October?

3. **What happens at fiscal year rollover (August 1)?**
   Does the new model year's planner auto-open? Does the prior year stay readable?

4. **Can reps override the monthly window?**
   Reps currently can lock/unlock dealers manually. Should they also be able to open a closed
   past month for a dealer who missed their window?

5. **Does the rep forecast follow the same monthly window, or do reps have full-year access
   always?**

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Year bug causes data loss if not fixed first | High | High | Fix year bug in Phase 1 before any other change |
| Dealers locked out of planner if fiscal month calculation is wrong | Medium | High | Thorough testing across Aug/Jan boundary and fiscal year edge cases |
| Rep forecast and dealer forecast get out of sync | Medium | Medium | Clarify in business rules whether rep always has full year access |
| `startup_action.js` regression — it is the largest and most complex file | Medium | Medium | Test all role types after any change: DEALER, SALESREP, ADMIN, SUPERUSER |
| JAMS job failure leaves planner in wrong state (Option B only) | Low | High | Prefer Option A to eliminate this dependency entirely |

---

## Summary

The monthly forecast scheduling feature is **technically feasible** with moderate effort.
The data model is already correct. The main work is:

1. Fix the hardcoded year inconsistency across 6 files (prerequisite, standalone fix, low risk)
2. Answer the 5 business rule questions above
3. Add fiscal-month date logic to `startup_action.js` to automatically set past periods to readonly
4. Test across all user roles and the August fiscal year rollover boundary

No database schema changes are required for the recommended approach. The existing lock/unlock
mechanism for reps remains intact and compatible with monthly scheduling.
