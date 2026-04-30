# Jira Story: Convert Dealer Planner from Quarterly to Monthly Forecasting

---

## Title
**Investigate Dealer Planner & Estimate Effort for Monthly Forecasting (vs. Quarterly)**

---

## User Story

**As a** Bennington Sales Operations Manager  
**I want** dealers to plan boat orders by month instead of quarter  
**So that** we have more granular forecasting data for production planning

---

## Background

The Dealer Planner tool currently exists in Verenia/EOS. Dealers are requesting the ability to submit forecasts on a **monthly basis** rather than entering all 12 months at once. Investigation is needed to understand the current implementation and estimate effort to support monthly scheduling.

---

## Investigation Required

### 1. Current State Analysis

| Question | Status |
|----------|--------|
| How does the planner currently work? | ✅ Investigated |
| What is the data model? | ✅ Monthly columns exist (`period_1_fc` through `period_12_fc`) |
| Is there a lock mechanism? | ✅ Yes, manual lock/unlock by rep |
| What users/roles exist? | ✅ DEALER, SALESREP, SUPERUSER, INSIDESALESMGR, ADMIN |

### 2. Gap Analysis

| Gap | Description | Risk |
|-----|-------------|------|
| **Year Inconsistency Bug** | Different JS files hardcode different years (2023, 2024, 2025) causing data to save to wrong rows | **HIGH** - Must fix first |
| **No Date-Awareness** | App doesn't know current fiscal month; all periods treated equally | Medium |
| **No Monthly Open/Close Logic** | No mechanism to auto-open/close periods by month | Medium |
| **Rep vs Dealer Saves Independent** | Separate save actions could get out of sync | Low |

---

## Current Implementation Findings

### Data Model
- **Already supports monthly** - Table `dealer_forecast_new` has 12 period columns
- **No schema changes required**

### Lock Mechanism
- Manual rep lock/unlock exists
- Can be extended for monthly locking

### Fiscal Calendar
- Already defined: AUG (period 1) → JUL (period 12)
- Model year starts August 1

---

## Effort Estimate

### Phase 1: Fix Year Bug (Prerequisite)
**Effort: 2-4 hours**

| File | Change |
|------|--------|
| `startup_action.js` | Uncomment dynamic year loading |
| `update_records.js` | Uncomment dynamic year loading |
| `update_rep_forecast.js` | Fix hardcoded 2024 → dynamic |
| `signature_actions.js` | Fix hardcoded 2024 → dynamic |
| `rep_forecast_print.js` | Fix hardcoded 2024 → dynamic |
| `signature_clear.js` | Fix hardcoded 2023 → dynamic |

**Code pattern to restore:**
```js
// Replace: var year = '2025';
// With: var year = loadByListName('Current_Model_Year')[0].MODEL_YEAR;
```

---

### Phase 2: Implement Monthly Scheduling
**Effort: 8-16 hours**

| Task | Hours | Description |
|------|-------|-------------|
| Add fiscal period calculation | 2-4 | Calculate current fiscal month from system date |
| Implement auto-readonly for past periods | 3-4 | Set prior months to readonly on page load |
| Add business rule configuration | 2-4 | Define how far ahead dealers can forecast |
| Testing across roles | 2-4 | Test DEALER, SALESREP, ADMIN scenarios |

**Fiscal period calculation logic:**
```
If calendar month >= August → fiscal period = calendar month - 7
If calendar month < August  → fiscal period = calendar month + 5
```

---

## Implementation Options

| Option | Approach | Effort | Pros | Cons |
|--------|----------|--------|------|------|
| **A. Date-Driven (Recommended)** | Auto-calculate current period from date | 8-12 hrs | No new tables, no scheduled jobs, fully automatic | Year rollover needs careful handling |
| **B. JAMS Config Table** | Scheduled job writes open period to config table | 12-16 hrs | Admin control, audit trail | Requires new table + scheduled job |
| **C. Admin UI Control** | Admin screen to manually open/close periods | 20-30 hrs | Maximum flexibility | Requires new UI development |

---

## Business Rules Needed from Stakeholders

Before development, the following decisions are required:

1. **How far ahead can dealers forecast?**
   - Only current month?
   - Current month + future months?

2. **Can dealers revise the current month?**
   - Single entry only?
   - Multiple revisions allowed while period is open?

3. **What happens at fiscal year rollover (August 1)?**
   - Auto-open new model year?
   - Prior year remains readable?

4. **Can reps override monthly windows?**
   - Rep can re-open a closed period for a dealer?

5. **Does rep forecast follow same monthly restrictions?**
   - Or does rep always have full-year access?

---

## Tasks

| Task | Type | Status |
|------|------|--------|
| Investigate current implementation | Analysis | ✅ Complete |
| Document inputs/outputs/users | Analysis | ✅ Complete |
| Identify year bug | Bug | ✅ Identified |
| Fix year inconsistency bug | Development | 🔲 Pending |
| Gather business rule answers from stakeholders | Requirements | 🔲 Pending |
| Implement fiscal period calculation | Development | 🔲 Pending |
| Add auto-readonly for past periods | Development | 🔲 Pending |
| Test across all user roles | QA | 🔲 Pending |
| Document changes | Documentation | 🔲 Pending |

---

## Acceptance Criteria

- [ ] Year bug fixed across all 6 affected files
- [ ] Business rules documented and approved
- [ ] Current fiscal period auto-calculated from date
- [ ] Past periods automatically set to readonly for dealers
- [ ] Current and future periods remain editable
- [ ] Rep lock/unlock mechanism still works
- [ ] Tested with DEALER, SALESREP, SUPERUSER roles
- [ ] Fiscal year rollover (August 1) tested and verified

---

## Total Effort Estimate

| Phase | Effort |
|-------|--------|
| Phase 1: Fix Year Bug | 2-4 hours |
| Phase 2: Monthly Scheduling | 8-16 hours |
| Testing & QA | 4-8 hours |
| **Total** | **14-28 hours (2-4 days)** |

---

## Dependencies

- [ ] Stakeholder answers to 5 business rule questions
- [ ] Access to Verenia/EOS environment for testing
- [ ] Confirmation of `Current_Model_Year` list existence in EOS

---

## Files to Modify

| File | Location |
|------|----------|
| `startup_action.js` | `dealers/startup_action.js` |
| `update_records.js` | `dealers/update_records.js` |
| `update_rep_forecast.js` | `dealers/update_rep_forecast.js` |
| `signature_actions.js` | `dealers/signature_actions.js` |
| `rep_forecast_print.js` | `dealers/rep_forecast_print.js` |
| `signature_clear.js` | `dealers/signature_clear.js` |

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Year bug causes data loss | High | High | Fix in Phase 1 before any other changes |
| Dealers locked out if calculation wrong | Medium | High | Thorough testing across Aug/Jan boundary |
| Rep forecast gets out of sync | Medium | Medium | Clarify business rules for rep access |
| `startup_action.js` regression | Medium | Medium | Test all role types after changes |

---

## Appendix: Users & Roles

| Role | Permission Level |
|------|------------------|
| DEALER | Edit own forecasts only |
| SALESREP | View/edit all assigned dealers, enter rep forecasts, lock/unlock |
| SUPERUSER | Full access to all dealers |
| INSIDESALESMGR | Full access to all dealers |
| ADMIN/OWNER | Full access to all dealers |

---

## Appendix: Inputs

| Input Type | Data | Source |
|------------|------|--------|
| **System-loaded** | Dealer info (name, contact, address, rep assignment) | `dealers` table |
| **System-loaded** | Actual boat units sold (current year + 3 prior years) | `SerialNumberMaster` via stored procedure |
| **System-loaded** | Open orders count | `BoatOptions` via stored procedure |
| **System-loaded** | Existing forecast data | `dealer_forecast_new` table |
| **System-loaded** | Saved signature image | `Dealer_Planner_Sig_Data` table |
| **User-entered** | 12 monthly forecast values (AUG–JUL) | Dealer |
| **User-entered** | Rep forecast (12 monthly values) | Sales Rep |
| **User-entered** | Terms agreement checkbox | Dealer |
| **User-entered** | Signature (canvas drawing) | Dealer |
| **User-entered** | Signed by name & date | Dealer |
| **User-entered** | Anticipated volume discount | Dealer |
| **User-entered** | Floorplan source | Dealer |
| **User-entered** | Comments | Dealer |
| **User-entered** | Lock/Unlock toggle | Sales Rep |

---

## Appendix: Outputs

| Output | Destination | Owner |
|--------|-------------|-------|
| Monthly forecast values (12 periods) | `dealer_forecast_new` table | Dealer |
| Rep forecast values (12 periods) | `dealer_forecast_new` table | Sales Rep |
| Signature image (PNG) | `Dealer_Planner_Sig_Data` table | Dealer |
| Lock status flag | `dealer_forecast_new.locked` column | Sales Rep |
| Printed forecast report | Browser print dialog | Sales Rep |

---

## Appendix: Fiscal Period Mapping

| Period | Month | Calendar Month |
|--------|-------|----------------|
| 1 | AUG | 8 |
| 2 | SEP | 9 |
| 3 | OCT | 10 |
| 4 | NOV | 11 |
| 5 | DEC | 12 |
| 6 | JAN | 1 |
| 7 | FEB | 2 |
| 8 | MAR | 3 |
| 9 | APR | 4 |
| 10 | MAY | 5 |
| 11 | JUN | 6 |
| 12 | JUL | 7 |
