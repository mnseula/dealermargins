# BoatOptions Import Project - Session Context
**Date:** 2026-02-03
**Status:** In Progress - Debugging CPQ Configured Items

---

## Project Goal

Import boat order data from MSSQL (CSI/ERP) to MySQL (warrantyparts database) with:
- Support for ALL model years (1999-2030)
- Automatic year detection from serial numbers
- CPQ order detection and routing
- Complete field mapping including MCTDesc, ItemMasterMCT, ConfigID
- CFG table scraping for CPQ configured items

---

## What We've Accomplished

### ✅ Completed Tasks

1. **Created complete import infrastructure**
   - `import_boatoptions_test.py` - Main import script with all features
   - `create_test_database.py` - Sets up test database with all year tables
   - `verify_import.py` - Data quality verification script
   - `check_boatoptions_tables.py` - Production table inspection

2. **Comprehensive year detection**
   - Detects model year from serial number suffix (last 2 digits)
   - Maps to correct table based on year:
     - BoatOptionsBefore_05 (before 2005)
     - BoatOptions99_04 (1999-2004)
     - BoatOptions05_07, 08_10, 11_14 (multi-year ranges)
     - BoatOptions15-30 (individual year tables)

3. **CPQ order detection**
   - Identifies CPQ orders by:
     - `order_date >= '2024-12-14'` (CPQ go-live)
     - `co_num LIKE 'SO%'`
     - `external_confirmation_ref LIKE 'SO%'`
   - Routes by model year (not hardcoded to 2026)

4. **Successful test import**
   - ✅ Extracted 75,517 rows from MSSQL
   - ✅ Imported to test database (warrantyparts_boatoptions_test)
   - ✅ All year tables populated correctly
   - ✅ 96 CPQ orders detected
   - ✅ Zero duplicate key errors (ON DUPLICATE KEY UPDATE)

---

## Current Status

### 🟡 Issues Identified

#### 1. **MCTDesc Population Low** ⚠️
- BoatOptions24: Only 38.8% have MCTDesc
- BoatOptions25: Only 34.6% have MCTDesc
- BoatOptions26: Only 8.5% have MCTDesc

**Expected:** 90%+ populated from prodcode_mst join

**Root Cause:** Many ItemMasterMCT codes don't have matching entries in prodcode_mst table

**Impact:** Medium - MCTDesc is used for filtering, but ItemMasterMCT works as fallback

#### 2. **CPQ Configured Items Missing** 🔴 CRITICAL
- Detected 96 CPQ orders during import
- Only found 2 configured line items with ConfigID (0.0%)
- Expected hundreds of CPQ configured items

**Root Cause:** Query Part 2 (cfg_attr_mst UNION) not returning data

**Attempted Fix:**
- Changed `ser.site_ref = 'BENN'` to `coi.site_ref = 'BENN'` in WHERE clause
- Did NOT fix the issue - still only 2 items

**Hypothesis:** Wrong table or wrong join conditions
- Current query uses: `cfg_attr_mst` table
- Original C# code used: `Uf_BENN_ComponentAttributesJL` table
- Need to verify which table has the CPQ configured data

---

## Database Structure

### Test Database: `warrantyparts_boatoptions_test`
21 tables matching production structure:
- BoatOptionsBefore_05
- BoatOptions99_04
- BoatOptions05_07, 08_10, 11_14
- BoatOptions15 through BoatOptions30

### Production Database: `warrantyparts`
18 tables with historical data:
- BoatOptions05_07 through BoatOptions26
- Same structure, but with millions of rows

---

## Key Files

### Import Scripts
- **`import_boatoptions_test.py`** (423 lines)
  - Main import script
  - Two-part UNION query:
    - Part 1: Regular order lines
    - Part 2: CPQ configured items (cfg_attr_mst) ← CURRENTLY NOT WORKING
  - Date filter: order_date >= '2024-12-14'
  - Invoiced only filter
  - Complete field mapping (23 fields)

### Database Setup
- **`create_test_database.py`**
  - Creates warrantyparts_boatoptions_test
  - Creates all 21 year tables
  - Matches production schema exactly

### Verification
- **`verify_import.py`**
  - Checks MCTDesc/ItemMasterMCT population
  - Checks ConfigID for CPQ items
  - Shows MCT code distribution
  - Displays sample data

### Utilities
- **`check_boatoptions_tables.py`**
  - Lists all BoatOptions tables in production
  - Shows row counts and sample serials

---

## SQL Query Structure

### Part 1: Regular Order Lines (WORKING ✅)
```sql
SELECT
    -- Order/boat info
    LEFT(coi.co_num, 30) AS [ERP_OrderNo],
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14) AS [BoatModelNo],

    -- Item details
    LEFT(coi.item, 30) AS [ItemNo],
    LEFT(coi.description, 30) AS [ItemDesc1],

    -- Critical fields
    LEFT(im.Uf_BENN_MaterialCostType, 10) AS [ItemMasterMCT],
    pcm.description AS [MCTDesc],  -- From prodcode_mst join

    -- Pricing
    CAST((coi.price * coi.qty_invoiced) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    coi.qty_invoiced AS [QuantitySold],

    -- CPQ detection
    co.order_date,
    co.external_confirmation_ref
FROM coitem_mst coi
LEFT JOIN item_mst im ON ...
LEFT JOIN prodcode_mst pcm ON im.Uf_BENN_MaterialCostType = pcm.product_code
LEFT JOIN inv_item_mst iim ON ...
WHERE coi.site_ref = 'BENN'
  AND iim.inv_num IS NOT NULL  -- Invoiced only
  AND co.order_date >= '2024-12-14'  -- Recent orders only
```

### Part 2: CPQ Configured Items (NOT WORKING 🔴)
```sql
SELECT
    -- Same order/boat info
    LEFT(coi.co_num, 30) AS [ERP_OrderNo],
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS [BoatSerialNo],

    -- Configured item details
    LEFT(ISNULL(ccm.comp_name, attr_detail.comp_id), 15) AS [ItemNo],
    LEFT(attr_detail.attr_value, 30) AS [ItemDesc1],

    -- Configuration tracking
    LEFT(coi.config_id, 30) AS [ConfigID],
    LEFT(attr_detail.attr_value, 100) AS [ValueText]
FROM coitem_mst coi
INNER JOIN cfg_attr_mst attr_detail  -- ← PROBLEM: No matches?
    ON coi.config_id = attr_detail.config_id
    AND coi.site_ref = attr_detail.site_ref
    AND attr_detail.attr_name = 'Description'
    AND attr_detail.sl_field = 'jobmatl.description'
    AND attr_detail.attr_type = 'Schema'
WHERE coi.config_id IS NOT NULL
  AND coi.qty_invoiced = coi.qty_ordered
  AND coi.qty_invoiced > 0
  AND coi.site_ref = 'BENN'  -- Fixed from ser.site_ref
  AND co.order_date >= '2024-12-14'
```

**Issue:** INNER JOIN on cfg_attr_mst returns 0 rows (or only 2)

---

## Next Steps

### Immediate: Debug CPQ Configured Items Query

**Need to determine which table has the CPQ configured data:**

Option A: `cfg_attr_mst` (current query)
```sql
SELECT COUNT(*)
FROM cfg_attr_mst attr
INNER JOIN coitem_mst coi ON coi.config_id = attr.config_id
WHERE coi.site_ref = 'BENN'
  AND attr.attr_name = 'Description';
```

Option B: `Uf_BENN_ComponentAttributesJL` (original C# code)
```sql
SELECT COUNT(*)
FROM Uf_BENN_ComponentAttributesJL att
INNER JOIN coitem_mst coi ON coi.co_num = att.RefRowPointer
WHERE coi.site_ref = 'BENN'
  AND att.Uf_BENN_AttributeValue IS NOT NULL;
```

**Action:** Run both queries to see which table has data

### Once CPQ Query Fixed:

1. **Re-import to test database**
   - Should see hundreds of ConfigID populated items
   - Verify all 96 CPQ orders have configured items

2. **Final verification**
   - Run verify_import.py
   - Check ConfigID population is 5-10%+
   - Spot check CPQ order data

3. **Create production script**
   - Copy import_boatoptions_test.py
   - Update database name to `warrantyparts`
   - Remove `_test` suffix from table names
   - Add staging table logic for zero-downtime deployment

4. **Production deployment**
   - Import to staging tables first
   - Verify data
   - Atomic swap to production tables
   - Schedule regular imports (nightly?)

---

## Test Data

### CPQ Orders (96 total)
- First detected CPQ order: SO00936047 (2025-12-11)
- Latest CPQ order: SO00936067 (2026-02-02)
- Date range: ~2 months
- Only 2 have ConfigID currently (expected: all 96)

### Import Volume (since 2024-12-14)
- Total rows: 75,517
- CPQ orders: 96
- Non-CPQ orders: 75,421
- Largest table: BoatOptions25 (14,885 rows)
- Oldest data: 1999 (87 rows in BoatOptions99_04)

---

## Configuration Details

### MSSQL (Source)
```
Server:   MPL1STGSQL086.POLARISSTAGE.COM
Database: CSISTG
User:     svccsimarine
Password: CNKmoFxEsXs0D9egZQXH
```

### MySQL (Destination)
```
Host:     ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com
Database: warrantyparts_boatoptions_test (test)
          warrantyparts (production)
User:     awsmaster
Password: VWvHG9vfG23g7gD
```

### CPQ Detection Criteria
```python
CPQ_GO_LIVE_DATE = date(2024, 12, 14)

def is_cpq_order(order_date, external_confirmation_ref, co_num):
    return (
        order_date >= CPQ_GO_LIVE_DATE and
        str(co_num).startswith('SO') and
        str(external_confirmation_ref).startswith('SO')
    )
```

---

## Key Insights

1. **Year detection works perfectly** - All 75,517 rows routed to correct tables
2. **CPQ detection works** - Identified 96 CPQ orders correctly
3. **Invoice filtering works** - 100% of rows have InvoiceNo
4. **ON DUPLICATE KEY UPDATE works** - Can re-run import without errors
5. **prodcode_mst join partial** - Only matches ~35% of items (acceptable)
6. **cfg_attr_mst join failing** - Returns almost no CPQ configured items (CRITICAL)

---

## Questions to Resolve

1. ❓ Which table has CPQ configured item data?
   - cfg_attr_mst (current query)
   - Uf_BENN_ComponentAttributesJL (C# original)
   - Other?

2. ❓ Are the cfg_attr_mst join conditions correct?
   - attr_name = 'Description'
   - sl_field = 'jobmatl.description'
   - attr_type = 'Schema'

3. ❓ Should we use different filters or different table?

4. ❓ Is MCTDesc population of 35% acceptable?
   - ItemMasterMCT is 93-98% populated (good)
   - MCTDesc nice-to-have but not critical

---

## Files Modified This Session

1. `import_boatoptions_test.py` - Created and refined
2. `create_test_database.py` - Created
3. `verify_import.py` - Created
4. `check_boatoptions_tables.py` - Created
5. Multiple commits to git with detailed messages

---

## Git Commits This Session

1. "Add BoatOptions test import infrastructure"
2. "Update import script to support all model years"
3. "Fix CPQ routing and add complete year table support"
4. "Add ON DUPLICATE KEY UPDATE to handle existing records"
5. "Add import verification script"
6. "Fix CPQ configured items query - change ser.site_ref to coi.site_ref"

---

## How to Resume

1. **Pull latest code:**
   ```bash
   git pull
   ```

2. **Run diagnostic queries** (on MSSQL):
   ```sql
   -- Check cfg_attr_mst
   SELECT COUNT(*) FROM cfg_attr_mst attr
   INNER JOIN coitem_mst coi ON coi.config_id = attr.config_id
   WHERE coi.site_ref = 'BENN' AND attr.attr_name = 'Description';

   -- Check Uf_BENN_ComponentAttributesJL
   SELECT COUNT(*) FROM Uf_BENN_ComponentAttributesJL att
   INNER JOIN coitem_mst coi ON coi.co_num = att.RefRowPointer
   WHERE coi.site_ref = 'BENN' AND att.Uf_BENN_AttributeValue IS NOT NULL;
   ```

3. **Based on results:**
   - If cfg_attr_mst has data: Adjust join conditions
   - If Uf_BENN_ComponentAttributesJL has data: Switch to that table
   - Update import_boatoptions_test.py Part 2 query

4. **Re-test import:**
   ```bash
   python import_boatoptions_test.py
   python verify_import.py
   ```

5. **Once ConfigID population > 5%:**
   - Create production version
   - Test on production (staging tables)
   - Deploy to production

---

**End of Session Context**
