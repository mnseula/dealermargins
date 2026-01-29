# Import Diagnostic Results - Only 21 Rows Found

**Date:** 2026-01-29
**Issue:** Import script only found 21 rows (expected hundreds of thousands)

---

## What Happened

Dry-run of `import_boatoptions26.py` completed successfully but only found:
- **21 rows total**
- **14 unique boats**
- **2 product codes** (ENA: 17 rows, ENG: 4 rows)

Expected: 500,000+ rows with 15,000+ boats

---

## Possible Causes

### 1. Serial Number Field Not Populated (Most Likely)

The import requires `Uf_BENN_BoatSerialNumber` to be populated:
```sql
WHERE coi.Uf_BENN_BoatSerialNumber IS NOT NULL
  AND coi.Uf_BENN_BoatSerialNumber != ''
```

**If most boats don't have this field filled in, we'll only get a tiny fraction of the data.**

### 2. Product Code Mismatch

Maybe the product codes in item_mst don't match our filter list exactly:
- We're filtering for BS1, EN7, ENG, ACC, etc.
- But maybe MSSQL uses different codes?
- Or codes are stored differently (e.g., with spaces, different case)?

### 3. Data Location

Maybe the boat data is in a different table or uses different fields:
- Perhaps `Uf_BENN_BoatModel` instead of `Uf_BENN_BoatSerialNumber`?
- Or boat data is stored without the Uf_BENN_ prefix fields?

---

## Diagnostic Tools Created

### 1. SQL Diagnostic Script
**File:** `diagnose_mssql_data.sql`

Run this on MSSQL to investigate:
```bash
# Connect to MSSQL and run
sqlcmd -S MPL1STGSQL086.POLARISSTAGE.COM -d CSISTG -U svccsimarine -P CNKmoFxEsXs0D9egZQXH -i diagnose_mssql_data.sql
```

**This will show:**
- Total rows in coitem_mst for BENN site
- How many have serial numbers vs don't
- What product codes actually exist
- Sample of boats with serial numbers
- Date range of orders

### 2. Python Test Script (No Serial Requirement)
**File:** `test_import_no_serial_filter.py`

```bash
python3 test_import_no_serial_filter.py
```

**This will show:**
- Row count WITH serial number requirement (21 rows)
- Row count WITHOUT serial number requirement (could be much higher)
- Product code distribution
- How many orders have serials vs don't

---

## Next Steps

### Step 1: Run Diagnostics

```bash
# Run Python diagnostic
python3 test_import_no_serial_filter.py

# Run SQL diagnostic
sqlcmd -S MPL1STGSQL086.POLARISSTAGE.COM -d CSISTG \
       -U svccsimarine -P CNKmoFxEsXs0D9egZQXH \
       -i diagnose_mssql_data.sql
```

### Step 2: Analyze Results

Look for:
1. **Serial number population**: What % of rows have Uf_BENN_BoatSerialNumber?
2. **Product codes**: What codes actually exist in the data?
3. **Alternative identifiers**: Can we use Uf_BENN_BoatModel or co_num instead?

### Step 3: Adjust Import Strategy

Based on findings, we may need to:

#### Option A: Remove Serial Number Requirement
If most boats don't have serials, use order number instead:
```python
WHERE coi.site_ref = 'BENN'
    AND coi.co_num IS NOT NULL  # Use order number instead
    AND im.product_code IN (...)
```

#### Option B: Use Different Identifier
If BoatModelNo is more reliable:
```python
WHERE coi.site_ref = 'BENN'
    AND coi.Uf_BENN_BoatModel IS NOT NULL  # Use model instead
    AND coi.Uf_BENN_BoatModel != ''
    AND im.product_code IN (...)
```

#### Option C: Adjust Product Codes
If product codes don't match, update the filter list based on what actually exists.

---

## Comparison: Expected vs Actual

### What We Expected (Based on BoatOptions25_test)

| Metric | Expected |
|--------|----------|
| Total rows | 500,000 - 1,000,000 |
| Unique boats | 15,000 - 20,000 |
| Product codes | 37 |
| BS1 (base boat) | 15,000+ boats |
| Engine codes | 15,000+ boats |

### What We Got (Actual Results)

| Metric | Actual |
|--------|--------|
| Total rows | **21** ❌ |
| Unique boats | **14** ❌ |
| Product codes | **2** (ENA, ENG only) ❌ |
| BS1 (base boat) | **0 boats** ❌ |
| Engine codes | **14 boats** (ENA/ENG only) ✓ |

**Difference: 99.998% fewer rows than expected!**

---

## Questions to Answer

1. **Is Uf_BENN_BoatSerialNumber the right field?**
   - Maybe it's only populated for warranty/service orders?
   - Maybe it's populated after delivery, not at sale?

2. **Should we use a different identifier?**
   - co_num (order number)?
   - Uf_BENN_BoatModel (model number)?
   - Some other field?

3. **Are product codes correct?**
   - Do we need different codes?
   - Are codes case-sensitive?
   - Are there spaces or special characters?

4. **Is the data in a different table?**
   - Maybe boat sales are in a different table?
   - Maybe we need to join to serial_mst?

---

## How BoatOptions25_test Works

Looking at the C# DataSync script, it may NOT filter by serial number:
```csharp
// Line 753 in DataSync_Function.cs
--WHERE
```

The WHERE clause is **commented out**, meaning it pulls ALL data!

**This explains why BoatOptions25_test has 323,272 rows but we only got 21.**

The C# script likely:
- Pulls ALL coitem_mst rows for BENN site
- Doesn't filter by serial number
- Doesn't filter by product code
- Gets everything including warranty parts, returns, etc.

---

## Recommended Action

### Immediate: Run Diagnostics
```bash
# See what's in MSSQL
python3 test_import_no_serial_filter.py
```

### Based on Results:

**If serial numbers are rare (<5% populated):**
- Remove serial number requirement
- Use order number (co_num) as identifier
- Group by order in window sticker generator

**If product codes don't match:**
- Update filter list based on actual codes
- Or remove product code filter entirely (like C# script)

**If data is elsewhere:**
- Investigate other tables
- Check if serial_mst has the boat data
- Maybe need different joins

---

## Files Created for Diagnosis

1. **diagnose_mssql_data.sql** - SQL queries to run on MSSQL
2. **test_import_no_serial_filter.py** - Python test without serial requirement
3. **IMPORT_DIAGNOSTIC_RESULTS.md** - This document

---

## Current Import Filter

```sql
WHERE coi.site_ref = 'BENN'
    AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL  ← VERY RESTRICTIVE
    AND coi.Uf_BENN_BoatSerialNumber != ''
    AND im.product_code IN (
        'BS1', 'EN7', 'ENG', 'ENI', ... 37 codes total
    )
```

**Hypothesis:** The serial number requirement is eliminating 99.99% of the data.

**Test:** Run `test_import_no_serial_filter.py` to confirm.

---

## Status

✅ Import script works correctly
⚠️ Filter is too restrictive (only 21 rows)
❓ Need to investigate MSSQL data structure
🔧 May need to adjust filter criteria

**Next: Run diagnostics and report findings**
