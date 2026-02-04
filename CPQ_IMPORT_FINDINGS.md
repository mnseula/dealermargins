# CPQ Import Investigation - Findings & Questions

**Date:** 2026-02-04
**Database:** warrantyparts_boatoptions_test (TEST)
**Script:** import_boatoptions_test.py
**Source:** MSSQL CSI/ERP (CSISTG database)

---

## Executive Summary

Successfully replicated the C# MSSQL-to-MySQL import process in Python and discovered a critical bug that affects both implementations. The bug caused 94 out of 96 configured CPQ items to be lost during import due to primary key collisions. The issue has been fixed in the Python version using `ROW_NUMBER()`.

---

## Critical Issue Discovered

### Problem: Primary Key Collision on Configured Items

**Symptom:**
- Import reported processing 96 rows from MSSQL
- Only 2 rows actually inserted into MySQL
- 94 rows silently lost due to duplicate key overwrites

**Root Cause:**
- All configured items (from `cfg_attr_mst` table in Part 2 of UNION query) have the same `co_line` value (typically 1)
- Table uses composite primary key: `(ERP_OrderNo, LineSeqNo)`
- Multiple components with same `(ERP_OrderNo, 1)` caused collisions
- `ON DUPLICATE KEY UPDATE` kept overwriting the same row

**Example:**
- Order SO00936047 has 46 configured components
- All had `LineSeqNo = 1`
- Only the last component (168SLJ_RAIL) was retained
- Lost 45 components worth ~$920,000

### Solution Implemented

Modified the MSSQL query to wrap the UNION in a CTE and use `ROW_NUMBER()`:

```sql
WITH OrderedRows AS (
    -- Original UNION query here
)
SELECT
    ROW_NUMBER() OVER (PARTITION BY [ERP_OrderNo] ORDER BY [LineSeqNo], [ItemNo]) AS [LineSeqNo],
    -- other columns...
FROM OrderedRows
```

**Result:**
- Each row now gets a unique sequential `LineSeqNo` (1, 2, 3, 4...)
- All 96 rows successfully imported
- No data loss

---

## Import Test Results

### Data Extracted from MSSQL (since 12/14/2025)

**Total:** 96 rows from 2 CPQ orders

| Order | Lines | Has Serial | Has ConfigID | Order Date | External Ref |
|-------|-------|------------|--------------|------------|--------------|
| SO00936047 | 46 | 0 | 46 | 2026-01-16 | SOBHO00675 |
| SO00936067 | 50 | 0 | 50 | 2026-02-02 | SOBHO00709 |

### Data Imported to MySQL

**After fix:** All 96 rows successfully imported to `BoatOptions26`

| Order | Line Items | Total Amount | Item Type |
|-------|------------|--------------|-----------|
| SO00936047 | 46 | $943,276.00 | All Configured (CFG) |
| SO00936067 | 50 | $1,637,850.00 | All Configured (CFG) |
| **Total** | **96** | **$2,581,126.00** | **100% CPQ** |

---

## Key Observations & Concerns

### 1. Empty BoatSerialNo for CPQ Orders

**Finding:** All CPQ orders have empty/NULL `BoatSerialNo`

**Sample Data:**
```
ERP Order: SO00936067
BoatSerialNo: [EMPTY]
WebOrderNo: SOBHO00709
ConfigID: BENN00000000000000000000000052
```

**Questions:**
- ❓ Is this expected for CPQ orders that haven't been manufactured yet?
- ❓ When does BoatSerialNo get assigned in the CPQ workflow?
- ❓ How do we link CPQ orders to physical boats after manufacturing?
- ❓ Should we use WebOrderNo as the primary identifier for CPQ orders?

### 2. Uniform Pricing on Configured Items

**Finding:** All components within a configuration show the same `ExtSalesAmount`

**Example - Order SO00936067:**
- Every component shows: `$32,757.00`
- 50 components × $32,757 = $1,637,850 (matches order total)

**Questions:**
- ❓ Is this expected? Does the ERP assign the total configuration price to each component?
- ❓ Should individual components have their own pricing?
- ❓ Is this causing the inflated total amounts ($2.5M for 2 boats)?
- ❓ Should we aggregate/deduplicate pricing for reporting purposes?

### 3. ConfigID Consistency

**Finding:** All items within an order share the same `ConfigID`

**Example:**
- SO00936067: All 50 items have `ConfigID = BENN00000000000000000000000052`
- SO00936047: All 46 items have `ConfigID = BENN00000000000000000000000043`

**Questions:**
- ❓ Is this correct? Should all components of a configuration share one ID?
- ❓ How does this relate to the boat configuration in CPQ?

### 4. Year Detection Logic

**Finding:** Script detects model year from serial number suffix

**Current logic:**
```python
# Serial: ETWC4149F425 → ends with 25 → 2025
# All CPQ orders detected as 2026 → routed to BoatOptions26
```

**But:** CPQ orders have empty serial numbers!

**Questions:**
- ❓ How should we determine model year for CPQ orders without serial numbers?
- ❓ Should we use a different field (BoatModelNo, order_date, etc.)?
- ❓ Is it correct to default to 2026 for orders with no serial?

### 5. C# Code Has Same Bug

**Finding:** The original C# code has the same `LineSeqNo` collision bug

**Impact:**
- ❓ Has the C# code been run in production?
- ❓ If so, how much CPQ data has been lost?
- ❓ Need to audit production data for missing configured items

---

## Data Flow Comparison: C# vs Python

### C# Approach
1. Export MSSQL query results to CSV file
2. Use `LOAD DATA LOCAL INFILE` for bulk import to MySQL
3. **Faster for large datasets** (bulk loading)
4. Requires temp file storage

### Python Approach (Current)
1. Extract MSSQL query results to memory
2. Use `executemany()` for batch inserts (1000 rows at a time)
3. `ON DUPLICATE KEY UPDATE` for upserts
4. **No temp files needed**
5. Slightly slower but adequate for current volumes

**Both implementations had the same LineSeqNo bug - now fixed in Python.**

---

## Database Architecture Findings

### Table: BoatOptions26 (and all year tables)

**Primary Key:** `(ERP_OrderNo, LineSeqNo)` - Composite key

**Columns Added During Investigation:**
- `ConfigID` - CPQ configuration ID
- `ValueText` - CPQ configuration value/description
- `C_Series` - Series from item master
- `order_date` - Order date (for CPQ detection)
- `external_confirmation_ref` - CPQ order reference

**Note:** Original schema didn't have these CPQ-specific fields. They were added to support the C# import logic.

---

## Critical Questions Requiring Answers

### Business Process Questions

1. **Serial Number Assignment:**
   - When do CPQ orders get assigned BoatSerialNo?
   - Is it during manufacturing, at invoicing, or another stage?
   - How do we track a CPQ order from configuration → manufacturing → delivery?

2. **Pricing Logic:**
   - Why do all configured components show the same price?
   - Is this the total configuration price replicated across all components?
   - Should components have individual pricing or is aggregate pricing correct?
   - How should we calculate boat totals - sum all components or use a master price?

3. **Model Year Determination:**
   - How should model year be determined for CPQ orders without serial numbers?
   - Should we use order_date, BoatModelNo prefix, or another field?
   - What's the business rule for routing CPQ orders to year tables?

4. **Data Validation:**
   - Is empty BoatSerialNo acceptable for invoiced CPQ orders?
   - Should we enforce serial number before allowing invoice?
   - What data quality checks should be in place?

### Technical Questions

5. **Primary Key Design:**
   - Is `(ERP_OrderNo, LineSeqNo)` the correct primary key?
   - Should we add `ConfigID` or `comp_id` to make it more unique?
   - How do we handle line number renumbering without breaking references?

6. **C# Code Deployment Status:**
   - Has the C# code been deployed to production?
   - If yes, how much CPQ data has been lost due to the LineSeqNo bug?
   - Do we need to re-import production data with the fix?

7. **Query Logic Validation:**
   - Is the UNION query correctly capturing all CPQ components?
   - Are we missing any tables or joins for complete CPQ data?
   - Should Part 1 (regular items) also capture CPQ physical items?

---

## Recommendations

### Immediate Actions

1. **Audit Production Data** (if C# code has been deployed):
   - Check for CPQ orders with suspiciously low line item counts
   - Compare order totals between ERP and imported data
   - Identify any data loss from LineSeqNo collisions

2. **Validate Pricing Logic:**
   - Confirm with business team how CPQ component pricing should work
   - Verify if $2.5M total for 2 boats is accurate or inflated due to duplication

3. **Serial Number Workflow:**
   - Document the complete lifecycle of serial number assignment
   - Determine when/how BoatSerialNo gets populated for CPQ orders
   - Update import logic if needed based on workflow

### Process Improvements

4. **Update C# Code:**
   - Apply the same `ROW_NUMBER()` fix to the C# implementation
   - Test thoroughly before production deployment
   - Add validation to verify row counts match MSSQL extraction

5. **Add Data Validation:**
   - Log expected vs actual row counts during import
   - Alert on significant discrepancies
   - Add checks for empty BoatSerialNo on invoiced orders (if that's invalid)

6. **Consider Primary Key Redesign:**
   - Evaluate if `(ERP_OrderNo, LineSeqNo, ConfigID)` would be better
   - Or use auto-increment ID with unique constraint on business keys
   - Prevents future collision issues

---

## Test Results Summary

### Before Fix
- Extracted: 96 rows from MSSQL
- Imported: 2 rows to MySQL (98% data loss!)
- Total Amount: $53,263

### After Fix
- Extracted: 96 rows from MSSQL
- Imported: 96 rows to MySQL ✅
- Total Amount: $2,581,126

**Fix Status:** ✅ Python implementation working correctly
**C# Status:** ⚠️ Same bug exists, needs fix before production use

---

## Next Steps

1. **Get answers** to the Critical Questions above
2. **Validate pricing** - Confirm if $2.5M for 2 boats is correct
3. **Fix C# code** - Apply ROW_NUMBER() solution
4. **Test with more data** - Import older CPQ orders to verify pattern holds
5. **Create production version** - Once validated, deploy to production database
6. **Document CPQ workflow** - Serial number assignment, pricing, lifecycle

---

## Files Modified

- `import_boatoptions_test.py` - Fixed LineSeqNo generation
- `add_cpq_columns.py` - Migration script for CPQ columns
- `verify_cpq_import.py` - Verification queries
- `debug_import.py` - MSSQL extraction debugging

## Commits
- `28294f0` - Fix: Correct CPQ go-live date from 2024 to 2025
- `e9b483d` - Add migration script for CPQ columns
- `fee4d3a` - Add CPQ import verification script
- `08a7b99` - Add debug script to show MSSQL extraction details
- `9360052` - Fix: Generate unique LineSeqNo for configured items using ROW_NUMBER
- `b929ee1` - Fix: Add brackets to column names in outer SELECT
