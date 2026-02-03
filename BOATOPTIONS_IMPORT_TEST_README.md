# BoatOptions Import Testing - Step by Step Guide

## Overview

This is the **TEST PHASE** for the new BoatOptions import script. We're validating that the MSSQL scraping logic works correctly before running on production.

## What This Does

1. Creates a **test database** (`warrantyparts_boatoptions_test`)
2. Imports **INVOICED orders only** from **12/14/2024 onwards**
3. Scrapes from MSSQL:
   - Regular order lines (boat, engine, accessories)
   - CPQ configured items (from `cfg_attr_mst` and `cfg_comp_mst` tables)
4. Detects **CPQ orders** and routes to `BoatOptions26_test`
5. Routes non-CPQ orders by serial number year

## Expected Results

Based on your CPQ order query:
- **≤ 112 CPQ orders** (only invoiced ones)
- All CPQ orders → `BoatOptions26_test`
- Could also have non-CPQ orders from same timeframe → `BoatOptions24` or `BoatOptions25_test`

## Step-by-Step Instructions

### Step 1: Create Test Database

```bash
# Connect to MySQL
mysql -h ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com -u awsmaster -p

# Run the setup script
source setup_test_database.sql
```

This creates:
- Database: `warrantyparts_boatoptions_test`
- Tables: `BoatOptions24`, `BoatOptions25_test`, `BoatOptions26_test`

### Step 2: Run Import Script

```bash
python3 import_boatoptions_test.py
```

The script will:
- Connect to MSSQL and extract invoiced orders from 12/14/2024 onwards
- Show progress and counts
- Import to test database
- Display summary

### Step 3: Verify Data

```sql
USE warrantyparts_boatoptions_test;

-- Check row counts
SELECT 'BoatOptions24' as table_name, COUNT(*) as row_count FROM BoatOptions24
UNION ALL
SELECT 'BoatOptions25_test', COUNT(*) FROM BoatOptions25_test
UNION ALL
SELECT 'BoatOptions26_test', COUNT(*) FROM BoatOptions26_test;

-- Check CPQ orders in BoatOptions26_test
SELECT
    ERP_OrderNo,
    BoatSerialNo,
    BoatModelNo,
    COUNT(*) as line_items
FROM BoatOptions26_test
GROUP BY ERP_OrderNo, BoatSerialNo, BoatModelNo
ORDER BY ERP_OrderNo;

-- Verify MCTDesc and ItemMasterMCT are populated
SELECT
    ItemMasterMCT,
    MCTDesc,
    COUNT(*) as count
FROM BoatOptions26_test
WHERE ItemMasterMCT IS NOT NULL
GROUP BY ItemMasterMCT, MCTDesc
ORDER BY count DESC;

-- Check for CPQ configured items (should have ConfigID)
SELECT
    ERP_OrderNo,
    ItemNo,
    ItemDesc1,
    ConfigID,
    ValueText
FROM BoatOptions26_test
WHERE ConfigID IS NOT NULL AND ConfigID != ''
LIMIT 10;
```

### Step 4: Validate Data Quality

Check these critical fields are populated:
- ✅ `MCTDesc` - Should have values like "ACCESSORIES", "ENGINES", etc.
- ✅ `ItemMasterMCT` - Should have codes like "ACC", "ENI", etc.
- ✅ `ConfigID` - Should be populated for CPQ configured items
- ✅ `ValueText` - Should have attribute values for configured items
- ✅ `InvoiceNo` - All records should have invoice numbers (invoiced only)

### Step 5: Test Window Sticker Query

Run your existing window sticker queries against the test database:

```sql
-- Test with a CPQ boat serial number
SELECT
    ItemNo,
    ItemDesc1,
    MCTDesc,
    ItemMasterMCT,
    ExtSalesAmount,
    QuantitySold,
    COALESCE(NULLIF(ItemNo, ''), ItemDesc1) as DisplayItemNo,
    ItemDesc1 as DisplayDescription
FROM warrantyparts_boatoptions_test.BoatOptions26_test
WHERE BoatSerialNo = 'YOUR_CPQ_SERIAL_HERE'
  AND ItemMasterMCT NOT IN ('DIC','DIF','DIP','DIR','DIA','DIW','LOY','PRD','VOD','DIV','SHO','GRO','ZZZ','FRE','WAR','DLR','FRT','A0','A0C','A0G','A0I','A0P','A0T','A0V','A1','A6','FUR')
  AND (ItemMasterMCT <> 'DIS' OR (ItemMasterMCT = 'DIS' AND ItemNo = 'NPPNPRICE16S'))
  AND (ItemMasterMCT <> 'ENZ' OR (ItemMasterMCT = 'ENZ' AND ItemDesc1 LIKE '%VALUE%'))
  AND ItemMasterProdCat <> '111'
  AND NOT (ItemMasterMCT = 'ACY' AND COALESCE(ExtSalesAmount, 0) = 0)
ORDER BY LineNo;
```

## What Success Looks Like

✅ **All CPQ orders appear in BoatOptions26_test**
✅ **MCTDesc and ItemMasterMCT fields are populated**
✅ **CPQ configured items have ConfigID and ValueText**
✅ **Window sticker query returns correct items**
✅ **Configuration items (colors, vinyl) are filterable by MCTDesc**
✅ **All records have InvoiceNo (invoiced only)**

## If Test Succeeds

Once validated, we can:
1. Create production version of import script
2. Target `warrantyparts.BoatOptions_` tables
3. Use staging tables approach for zero-downtime deployment

## If Test Fails

Common issues to check:
- MSSQL connection errors → Check network/VPN
- No data imported → Check if orders have been invoiced
- Missing MCTDesc → Check prodcode_mst table join
- Missing ConfigID → Check cfg_attr_mst table join
- Wrong table routing → Check CPQ detection logic

## Files Created

- `setup_test_database.sql` - Creates test database and tables
- `import_boatoptions_test.py` - Import script for testing
- `BOATOPTIONS_IMPORT_TEST_README.md` - This file

## Next Steps After Testing

If test succeeds:
1. Update script to target production database
2. Add staging tables logic for zero downtime
3. Schedule regular imports (nightly?)
4. Update applications to use new data source
