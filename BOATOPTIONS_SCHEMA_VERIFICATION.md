# BoatOptions Table Schema Verification

**Date:** 2026-02-10  
**Purpose:** Verify all BoatOptions tables can handle CPQ data imports

---

## Required Columns (31 total)

The import script (`import_boatoptions_production.py`) inserts these 31 columns:

### Core Fields (21 columns)
1. `ERP_OrderNo` VARCHAR(30)
2. `BoatSerialNo` VARCHAR(15)
3. `BoatModelNo` VARCHAR(14)
4. `LineNo` INT
5. `ItemNo` VARCHAR(30)
6. `ItemDesc1` VARCHAR(50)
7. `ExtSalesAmount` DECIMAL(10,2)
8. `QuantitySold` DECIMAL(18,8)
9. `Series` VARCHAR(5)
10. `WebOrderNo` VARCHAR(30)
11. `Orig_Ord_Type` VARCHAR(1)
12. `ApplyToNo` VARCHAR(30)
13. `InvoiceNo` VARCHAR(30)
14. `InvoiceDate` INT
15. `ItemMasterProdCat` VARCHAR(3)
16. `ItemMasterProdCatDesc` VARCHAR(100)
17. `ItemMasterMCT` VARCHAR(10)
18. `MCTDesc` VARCHAR(50)
19. `LineSeqNo` INT
20. `ConfigID` VARCHAR(30)
21. `ValueText` VARCHAR(100)
22. `OptionSerialNo` VARCHAR(12)
23. `C_Series` VARCHAR(5)

### CPQ-Specific Fields (8 columns) - NEW
24. `order_date` DATE
25. `external_confirmation_ref` VARCHAR(30)
26. `MSRP` DECIMAL(10,2)
27. `CfgName` VARCHAR(100)
28. `CfgPage` VARCHAR(50)
29. `CfgScreen` VARCHAR(50)
30. `CfgValue` VARCHAR(100)
31. `CfgAttrType` VARCHAR(20)

---

## Table Status

### ✅ Production Tables (warrantyparts database)

| Table | Status | CPQ Columns | Notes |
|-------|--------|-------------|-------|
| BoatOptions26 | ✅ Ready | ✅ All 8 CPQ columns present | Latest table, has all columns |
| BoatOptions25 | ✅ Ready | ✅ All 8 CPQ columns added | Fixed via fix_boatoptions_schema.sql |
| BoatOptions24 | ✅ Ready | ✅ All 8 CPQ columns added | Fixed via fix_boatoptions_schema.sql |
| BoatOptions23 | ✅ Ready | ✅ All 8 CPQ columns added | Fixed via fix_boatoptions_schema.sql |
| BoatOptions22 | ✅ Ready | ✅ All 8 CPQ columns added | Fixed via fix_boatoptions_schema.sql |
| BoatOptions21 | ✅ Ready | ✅ All 8 CPQ columns added | Fixed via fix_boatoptions_schema.sql |
| BoatOptions20 | ✅ Ready | ✅ All 8 CPQ columns added | Fixed via fix_boatoptions_schema.sql |
| BoatOptions19 | ✅ Ready | ✅ All 8 CPQ columns added | Fixed via fix_boatoptions_schema.sql |
| BoatOptions18 | ✅ Ready | ✅ All 8 CPQ columns added | Fixed via fix_boatoptions_schema.sql |
| BoatOptions17 | ✅ Ready | ✅ All 8 CPQ columns added | Fixed via fix_boatoptions_schema.sql |
| BoatOptions16 | ✅ Ready | ✅ All 8 CPQ columns added | Fixed via fix_boatoptions_schema.sql |
| BoatOptions15 | ✅ Ready | ✅ All 8 CPQ columns added | Fixed via fix_boatoptions_schema.sql |
| BoatOptions14 and earlier | ⚠️ Excluded | N/A | Import script filters out pre-2015 boats |

### ⚠️ Pre-2015 Tables (BoatOptions99_04, BoatOptions05_07, BoatOptions08_10, BoatOptions11_14)

**Status:** NOT COMPATIBLE with CPQ imports

**Why:** These tables lack the 8 CPQ-specific columns:
- `order_date`
- `external_confirmation_ref`
- `MSRP`
- `CfgName`
- `CfgPage`
- `CfgScreen`
- `CfgValue`
- `CfgAttrType`

**Solution:** Import script automatically filters out pre-2015 boats:
```sql
AND TRY_CAST(RIGHT(COALESCE(...BoatSerialNumber), 2) AS INT) >= 15
```

This ensures only 2015+ boats (with CPQ-compatible tables) are imported.

---

## Verification Queries

### 1. Check Column Count Per Table
```sql
SELECT 
    TABLE_NAME,
    COUNT(*) as column_count
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'warrantyparts'
  AND TABLE_NAME REGEXP '^BoatOptions[0-9]{2}$'
GROUP BY TABLE_NAME
ORDER BY TABLE_NAME;

-- Expected: All tables should show 31 columns
```

### 2. Check Specific CPQ Columns Exist
```sql
-- Check if all CPQ columns exist in BoatOptions25
SELECT COLUMN_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'warrantyparts'
  AND TABLE_NAME = 'BoatOptions25'
  AND COLUMN_NAME IN ('order_date', 'external_confirmation_ref', 'MSRP', 
                      'CfgName', 'CfgPage', 'CfgScreen', 'CfgValue', 'CfgAttrType')
ORDER BY COLUMN_NAME;

-- Should return 8 rows
```

### 3. Verify BoatOptions26 Has All Columns
```sql
DESCRIBE warrantyparts.BoatOptions26;

-- Should show 31 columns including all CPQ fields
```

### 4. Test Insert Capability
```sql
-- Test insert into BoatOptions26 (dry run)
INSERT INTO warrantyparts.BoatOptions26 (
    ERP_OrderNo, BoatSerialNo, BoatModelNo, LineNo, ItemNo, ItemDesc1,
    ExtSalesAmount, QuantitySold, Series, WebOrderNo, Orig_Ord_Type,
    ApplyToNo, InvoiceNo, InvoiceDate, ItemMasterProdCat, ItemMasterProdCatDesc,
    ItemMasterMCT, MCTDesc, LineSeqNo, ConfigID, ValueText,
    OptionSerialNo, C_Series, order_date, external_confirmation_ref,
    MSRP, CfgName, CfgPage, CfgScreen, CfgValue, CfgAttrType
) VALUES (
    'TEST001', 'TEST123456789', '22SFC', 1, 'TEST-ITEM', 'Test Description',
    1000.00, 1.0, 'S', 'WEB001', 'O',
    NULL, 'INV001', 20250210, 'ACC', 'Accessory',
    'ACC', 'ACCESSORIES', 1, 'CFG001', 'Test Value',
    NULL, 'S', '2026-02-10', 'SO001',
    1200.00, 'Base Boat', 'Page1', 'Screen1', '22SFC', 'Configurable'
);

-- If this succeeds without error, the table is compatible
ROLLBACK;
```

---

## Action Items

### ✅ Completed
- [x] Added 8 CPQ columns to BoatOptions15 through BoatOptions25
- [x] BoatOptions26 already had all columns
- [x] Import script filters pre-2015 boats automatically
- [x] Test database tables created with all columns

### ⚠️ Reminder
- **Pre-2015 boats cannot be imported** - They go to old tables (BoatOptions99_04, 05_07, 08_10, 11_14) that lack CPQ columns
- **Import script handles this automatically** via year filter
- **No action needed** - This is by design

---

## Summary

**✅ ALL production tables (BoatOptions15-26) are ready for CPQ imports.**

The `fix_boatoptions_schema.sql` script has been run to add missing CPQ columns to all 2015-2025 tables. BoatOptions26 already had all columns.

**Pre-2015 boats are intentionally excluded** from CPQ imports because:
1. They use legacy tables without CPQ columns
2. They're not configured via CPQ system
3. The import script filters them out automatically

**No further schema changes needed.**

---

**Last Updated:** 2026-02-10
**Maintained By:** Bennington Marine IT
