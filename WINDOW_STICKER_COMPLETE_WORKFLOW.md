# Complete Workflow: From Invoiced Boat to Window Sticker

**Last Updated:** 2026-02-09
**Purpose:** Step-by-step guide to get an invoiced boat from ERP into the window sticker system

---

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Import Boats from ERP](#step-1-import-boats-from-erp)
4. [Step 2: Sync CPQ Data (if needed)](#step-2-sync-cpq-data-if-needed)
5. [Step 3: Add Boats to SerialNumberMaster](#step-3-add-boats-to-serialnumbermaster)
6. [Step 4: Generate Window Sticker](#step-4-generate-window-sticker)
7. [Troubleshooting](#troubleshooting)
8. [Technical Details](#technical-details)

---

## Overview

### The Complete Data Flow
```
ERP (MSSQL)
    ↓ [import_boatoptions_production.py]
BoatOptions26 (MySQL)
    ↓ [add_boat_to_serial_master.py]
SerialNumberMaster + SerialNumberRegistrationStatus
    ↓ [User selects boat in UI]
Window Sticker (queries warrantyparts_test for CPQ data)
```

### Key Databases
- **ERP (MSSQL):** Source of truth for invoiced boats
- **warrantyparts.BoatOptions26:** Imported boat line items
- **warrantyparts.SerialNumberMaster:** Boat master records
- **warrantyparts.SerialNumberRegistrationStatus:** Registration status
- **warrantyparts_test:** CPQ catalog data (models, features, specs)

---

## Prerequisites

### Required Scripts
- `import_boatoptions_production.py` - Import boats from ERP
- `add_boat_to_serial_master.py` - Add boats to SerialNumberMaster
- `load_cpq_data.py` - Load CPQ catalog from APIs (if needed)

### Database Access
- **MySQL RDS:** ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com
  - User: awsmaster
  - Password: VWvHG9vfG23g7gD
  - Databases: warrantyparts, warrantyparts_test

- **MSSQL (ERP):** Your production ERP database

---

## Step 1: Import Boats from ERP

### What This Does
Imports invoiced boats from ERP into `BoatOptions26` table.

### When to Run
- After boats are invoiced in ERP (typically after a certain date)
- For our example: Import boats from December 15, 2025 onwards

### Command
```bash
python import_boatoptions_production.py
```

### What It Does
1. Connects to ERP (MSSQL) and queries invoiced orders
2. Filters boats from 2015+ (year 15+) to avoid old tables without CPQ columns
3. Extracts boat line items + CPQ configuration attributes
4. Routes to correct table based on model year (BoatOptions26 for 2026 boats)
5. Inserts all line items into MySQL

### Configuration in Script
```python
# Date filter (line ~34)
AND co.order_date >= '2025-12-14'

# Year filter (lines 208, 306) - Only 2015+ boats
AND TRY_CAST(RIGHT(COALESCE(...BoatSerialNumber), 2) AS INT) >= 15
```

### Expected Output
```
Extracted: 302 rows from MSSQL
Breakdown by table:
  BoatOptions26: 302 rows

CPQ orders: 182
Non-CPQ orders: 120

✅ PRODUCTION IMPORT COMPLETE
```

### Verification
```sql
-- Check boat was imported
SELECT * FROM warrantyparts.BoatOptions26
WHERE BoatSerialNo = 'ETWINVTEST0126';

-- Should show ~58 rows (boat + engine + accessories + config attributes)
```

---

## Step 2: Sync CPQ Data (if needed)

### What This Does
Loads CPQ catalog data (models, features, specs) from Infor CPQ APIs into `warrantyparts_test`.

### When to Run
- **First time setup:** Yes, run this
- **New model year:** Yes, when new models are released
- **Regular imports:** Usually NOT needed (catalog doesn't change often)
- **New models added to CPQ:** Yes, to get latest catalog

### Command
```bash
python3 load_cpq_data.py
```

### What It Loads
1. **Models** - All boat models (22SFC, 23ML, 25QXFBWA, etc.)
2. **StandardFeatures** - All standard features master list
3. **ModelStandardFeatures** - Which features go with which models (by year)
4. **ModelPerformance** - Performance specs (HP, weight, capacity, etc.)
5. **PerformancePackages** - Performance package definitions
6. **Dealers** - Dealer information
7. **DealerMargins** - Margin percentages

### Expected Output
```
Models: Loaded 283 models
Standard Features: Loaded 2475 features
Model Standard Features: Loaded 15000+ mappings
Performance Data: Loaded 1200+ records
✅ All data loaded successfully
```

### Verification
```sql
-- Check if your models exist
SELECT * FROM warrantyparts_test.Models
WHERE model_id IN ('22SFC', '23ML');

-- Check standard features for a model
SELECT COUNT(*) FROM warrantyparts_test.ModelStandardFeatures
WHERE model_id = '22SFC' AND year = 2025;
-- Should show 51 features for 22SFC
```

### Important Notes
- **CPQ APIs are the source of truth** - All model data comes from APIs
- **warrantyparts_test stores the data** - For fast local queries
- **Window stickers query warrantyparts_test** - Not the APIs directly
- **Eos sync is for legacy boats only** - CPQ boats don't need it

---

## Step 3: Add Boats to SerialNumberMaster

### What This Does
Adds boat records to SerialNumberMaster and SerialNumberRegistrationStatus so they appear in the dealer's boat list.

### When to Run
After Step 1 (import to BoatOptions26) completes.

### Command
```bash
# For each boat, run:
python3 add_boat_to_serial_master.py <hull_number> <erp_order>

# Examples:
python3 add_boat_to_serial_master.py ETWINVTEST0126 SO00936076
python3 add_boat_to_serial_master.py ETWINVTEST0226 SO00936077
```

### What the Script Does
1. Queries BoatOptions26 for the boat's details (model, series, invoice, etc.)
2. Inserts record into **SerialNumberMaster** with:
   - Test dealer 50 (PONTOON BOAT, LLC)
   - Active = 0 (unregistered)
   - InvoiceNo from BoatOptions26
3. Inserts record into **SerialNumberRegistrationStatus** with:
   - Registered = 0 (not sold)
4. Verifies the insertion

### Expected Output
```
================================================================================
✅ BOAT SUCCESSFULLY ADDED
================================================================================
Hull Number:       ETWINVTEST0126
Model:             22SFC (22 S FISH AND CRUISE)
Series:            S
Invoice:           25217359
Dealer:            50 (PONTOON BOAT, LLC)
Active:            0 (0 = unregistered)
Registered:        0 (0 = not sold)

Unregistered Invoiced Boat Status:
  ✅ InvoiceNo IS NOT NULL: 25217359
  ✅ Active = 0: True
  ✅ Registered = 0: True
================================================================================
```

### Verification
```sql
-- Check SerialNumberMaster
SELECT * FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = 'ETWINVTEST0126';

-- Check SerialNumberRegistrationStatus
SELECT * FROM warrantyparts.SerialNumberRegistrationStatus
WHERE Boat_SerialNo = 'ETWINVTEST0126';

-- Query unregistered invoiced boats for dealer 50
SELECT
    sm.Boat_SerialNo,
    sm.BoatItemNo,
    sm.InvoiceNo,
    sm.DealerNumber,
    sm.Active,
    rs.Registered
FROM warrantyparts.SerialNumberMaster sm
LEFT JOIN warrantyparts.SerialNumberRegistrationStatus rs
    ON sm.Boat_SerialNo = rs.Boat_SerialNo
WHERE sm.InvoiceNo IS NOT NULL
  AND sm.Active = 0
  AND rs.Registered = 0
  AND sm.DealerNumber = 50;
```

### Important: Test Dealer 50
All manually added boats use **dealer 50 (PONTOON BOAT, LLC)** to:
- Keep test data isolated from production dealers
- Prevent test boats from showing in customer-facing systems
- Easy to filter/identify test boats

---

## Step 4: Generate Window Sticker

### Access the System
1. Open the window sticker application in your browser
2. Select **Dealer 50** from the dropdown
3. Click **Search** to load boats

### Select Your Boat
You should now see your boat in the list:
- ETWINVTEST0126 (22SFC)
- ETWINVTEST0226 (23ML)

Click **[Select ETWINVTEST0126]**

### What Happens Behind the Scenes

#### 1. JavaScript Loads Boat Data (getunregisteredboats.js)
```javascript
// Detects CPQ boat (has CfgName attributes)
window.isCPQBoat = true

// Sets model year from serial number
window.model_year = '26'  // from ETWINVTEST0126

// Keeps exact model name (22SFC, not transformed to 22SS)
window.realmodel = '22SFC'

// Calls stored procedures
GET_CPQ_LHS_DATA('22SFC', 2025, 'ETWINVTEST0126')
GET_CPQ_STANDARD_FEATURES('22SFC', 2025)

// Stores data for print.js
window.cpqLhsData = { loa, beam, seats, hp, weight, etc. }
window.cpqStandardFeatures = {
    'Interior Features': [...],
    'Exterior Features': [...],
    'Console Features': [...],
    'Warranty': [...]
}
```

#### 2. Stored Procedures Query warrantyparts_test

**GET_CPQ_LHS_DATA:**
```sql
SELECT m.model_id, m.loa_str, m.beam_str, m.seats,
       mp.max_hp, mp.person_capacity, mp.hull_weight, etc.
FROM warrantyparts_test.Models m
LEFT JOIN warrantyparts_test.ModelPerformance mp ON ...
WHERE m.model_id = '22SFC'
```

**GET_CPQ_STANDARD_FEATURES:**
```sql
SELECT sf.area, sf.description
FROM warrantyparts_test.StandardFeatures sf
JOIN warrantyparts_test.ModelStandardFeatures msf ON ...
WHERE msf.model_id = '22SFC' AND msf.year = 2025
```

#### 3. Window Sticker Renders (print.js)
```javascript
// Checks for CPQ data
if (window.cpqLhsData) {
    // Use CPQ LHS data for boat specs
}

if (window.cpqStandardFeatures) {
    // Use CPQ standard features
    // Renders: Interior, Exterior, Console, Warranty sections
}
```

### Print the Window Sticker
Click the **Print** button to generate the PDF.

### What You Should See
✅ **Boat Information:**
- LOA, Beam, Seats
- Performance specs
- Engine configuration

✅ **Standard Features:**
- Interior Features (18 features for 23ML)
- Exterior Features (17 features)
- Console Features (11 features)
- Warranty (2 features)

✅ **Included Options:**
- All accessories and upgrades from BoatOptions26

✅ **Pricing:**
- MSRP and dealer cost (if enabled)

---

## Troubleshooting

### Issue: Boat doesn't appear in dealer list

**Check:**
```sql
-- Is boat in SerialNumberMaster?
SELECT * FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = 'YOURBOAT';

-- Is it marked as unregistered?
SELECT sm.Active, rs.Registered
FROM warrantyparts.SerialNumberMaster sm
LEFT JOIN warrantyparts.SerialNumberRegistrationStatus rs
    ON sm.Boat_SerialNo = rs.Boat_SerialNo
WHERE sm.Boat_SerialNo = 'YOURBOAT';
```

**Expected:**
- Active = 0
- Registered = 0
- InvoiceNo IS NOT NULL

**Fix:** Run `add_boat_to_serial_master.py` again

---

### Issue: Standard features are missing

**Symptoms:**
- Boat info shows up
- Standard features section is empty
- Console shows: "⚠️ No standard features returned"

**Check Browser Console:**
1. Open DevTools (F12)
2. Select the boat
3. Look for these messages:

```
===== CPQ STANDARD FEATURES LOAD =====
Calling GET_CPQ_STANDARD_FEATURES with params:
  @PARAM1 (model_id): 22SFC    ← Should be 22SFC, NOT 22SS
  @PARAM2 (year): 2025
```

**Check Database:**
```sql
-- Do features exist for this model/year?
SELECT COUNT(*) FROM warrantyparts_test.ModelStandardFeatures
WHERE model_id = '22SFC' AND year = 2025;
-- Should return > 0
```

**Common Causes:**

**1. Model name being transformed (22SFC → 22SS)**
- Fixed in packagePricing.js with CPQ detection
- CPQ boats should NOT have model names transformed

**2. Wrong year being queried**
- Check console log - should query year 2025 for most boats
- cpqYear is hardcoded to 2025 in getunregisteredboats.js line 219

**3. Model doesn't exist in warrantyparts_test**
- Run `load_cpq_data.py` to sync from CPQ APIs

**4. BoatModelNo is NULL**
- Should be set during import
- If NULL, update: `UPDATE BoatOptions26 SET BoatModelNo = '22SFC' WHERE BoatSerialNo = 'YOURBOAT'`

---

### Issue: "Unknown column 'ConfigID'" error during import

**Cause:** Trying to import pre-2015 boats into old tables (BoatOptions99_04, etc.) that don't have CPQ columns.

**Fix:** Already fixed in import script with year filter:
```python
AND TRY_CAST(RIGHT(COALESCE(...BoatSerialNumber), 2) AS INT) >= 15
```

**Verify:** Check import script has this filter on BOTH parts of UNION query (lines 208 and 306).

---

### Issue: SerialNumberRegistrationStatus truncating hull numbers

**Symptoms:**
- Hull number ETWINVTEST0126 becomes ETWINVTEST012 (truncated)
- JOIN between tables fails

**Cause:** Column was VARCHAR(13), hull numbers are 14+ characters

**Fix:** Already fixed - column expanded to VARCHAR(20):
```sql
ALTER TABLE SerialNumberRegistrationStatus
MODIFY COLUMN Boat_SerialNo VARCHAR(20);
```

**Verify:**
```sql
DESCRIBE warrantyparts.SerialNumberRegistrationStatus;
-- Boat_SerialNo should be varchar(20)
```

---

## Technical Details

### Unregistered Invoiced Boat Formula

A boat is "unregistered invoiced" when:
```sql
WHERE sm.InvoiceNo IS NOT NULL          -- Has invoice (boat was invoiced)
  AND sm.Active = 0                     -- Not registered in master
  AND rs.Registered = 0                 -- Not sold to customer
```

This identifies boats that are:
- ✅ Invoiced by Bennington
- ❌ Not yet sold/registered to a customer
- 📦 Sitting in dealer inventory or in-transit

---

### CPQ vs Legacy Boats

#### CPQ Boats (New System - 2021+)
- **Detection:** Has CfgName attributes in BoatOptions26
- **Model IDs:** Exact from API (22SFC, 23ML, 25QXFBWA)
- **Data Source:** warrantyparts_test (Models, StandardFeatures, etc.)
- **Stored Procedures:** GET_CPQ_LHS_DATA, GET_CPQ_STANDARD_FEATURES
- **No transformations:** Model names used as-is

#### Legacy Boats (Old System - pre-2021)
- **Detection:** No CfgName attributes
- **Model IDs:** Year codes stripped, transformations applied (22SFC → 22SS)
- **Data Source:** Eos database (boat_specs, standards_matrix, etc.)
- **Queries:** Legacy list queries
- **Transformations:** SFC→SS, MFC→MS, SF→SE, etc.

**Key Rule:** CPQ boats bypass ALL legacy transformations!

---

### Important Files

#### Python Scripts
- `import_boatoptions_production.py` - Import boats from ERP
- `add_boat_to_serial_master.py` - Add to SerialNumberMaster
- `load_cpq_data.py` - Load CPQ catalog from APIs
- `sync_cpq_to_eos.py` - Sync to Eos (legacy only, NOT needed for CPQ)

#### JavaScript Files
- `getunregisteredboats.js` - Loads boat when selected
- `packagePricing.js` - Loads pricing and detects CPQ boats
- `print.js` - Renders window sticker

#### SQL Files
- `GET_CPQ_STANDARD_FEATURES.sql` - Stored procedure for features
- `GET_CPQ_LHS_DATA_v3.sql` - Stored procedure for boat specs

---

### Database Tables Reference

#### warrantyparts (Production Data)
- **BoatOptions26** - Boat line items from ERP (all items for each boat)
- **SerialNumberMaster** - Boat master records (one per boat)
- **SerialNumberRegistrationStatus** - Registration status (one per boat)

#### warrantyparts_test (CPQ Catalog)
- **Models** - All boat models (283 models)
- **StandardFeatures** - All standard features (2475 features)
- **ModelStandardFeatures** - Model × feature mappings (15000+ records)
- **ModelPerformance** - Performance specs by model × package
- **PerformancePackages** - Performance package definitions

#### Eos (Legacy System Only)
- **boat_specs** - Legacy boat dimensions
- **perf_pkg_spec** - Legacy performance specs
- **standards_list** - Legacy features list
- **standards_matrix_2025** - Legacy feature mappings
- **NOT USED for CPQ boats!**

---

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    INFOR CPQ APIs                            │
│  (Source of Truth for Models, Features, Specs)              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ load_cpq_data.py (when catalog changes)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              warrantyparts_test Database                     │
│  • Models                                                    │
│  • StandardFeatures                                          │
│  • ModelStandardFeatures                                     │
│  • ModelPerformance                                          │
│  • PerformancePackages                                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ GET_CPQ_* stored procedures
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                                                              │
│  ERP (MSSQL)        ──import──>    BoatOptions26            │
│  Invoiced Boats                    (warrantyparts)          │
│                                           │                  │
│                                           │ add_boat script  │
│                                           ▼                  │
│                              SerialNumberMaster              │
│                              SerialNumberRegistrationStatus  │
│                                           │                  │
│                                           │ User selects     │
│                                           ▼                  │
│                                    Window Sticker            │
│                                  (queries both DBs)          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

### Key Decisions & Why

#### Why ItemMasterProdCat = 'ACC' instead of ItemNo LIKE '90%'?
- **Problem:** New system won't use "90" prefix for options
- **Solution:** Filter by product category field instead
- **Benefit:** Future-proof against numbering changes

#### Why SQL Stored Procedures instead of API calls?
- **Real-time calculations** - Always uses current data
- **Better performance** - Database does the work locally
- **Easier maintenance** - Business logic in one place
- **Simpler architecture** - Just call procedures

#### Why Test Dealer 50?
- **Data isolation** - Test boats don't mix with real dealers
- **Safety** - Won't show in customer-facing systems
- **Easy filtering** - Can identify all test data quickly

#### Why VARCHAR(20) for hull numbers?
- **Future-proof** - Handles 14+ character hull numbers
- **No truncation** - Preserves full serial numbers
- **Safe expansion** - Doesn't affect existing data

---

## Quick Reference Commands

### Import New Boats
```bash
cd /path/to/scripts
python import_boatoptions_production.py
```

### Add Boat to System
```bash
python3 add_boat_to_serial_master.py <HULL_NUMBER> <ERP_ORDER>
```

### Refresh CPQ Catalog (rare)
```bash
python3 load_cpq_data.py
```

### Check Boat Status
```sql
-- Quick check
SELECT
    sm.Boat_SerialNo,
    sm.BoatItemNo,
    sm.InvoiceNo,
    sm.Active,
    rs.Registered
FROM warrantyparts.SerialNumberMaster sm
LEFT JOIN warrantyparts.SerialNumberRegistrationStatus rs
    ON sm.Boat_SerialNo = rs.Boat_SerialNo
WHERE sm.Boat_SerialNo = 'YOURBOAT';
```

### Count Standard Features
```sql
SELECT COUNT(*)
FROM warrantyparts_test.ModelStandardFeatures
WHERE model_id = '22SFC' AND year = 2025;
```

---

## Summary

**The Complete Process:**
1. ✅ Import boats from ERP → BoatOptions26
2. ✅ Ensure CPQ catalog is loaded → warrantyparts_test
3. ✅ Add boats to SerialNumberMaster (dealer 50, Active=0)
4. ✅ Add boats to SerialNumberRegistrationStatus (Registered=0)
5. ✅ Select dealer 50 in UI
6. ✅ Select boat from list
7. ✅ Print window sticker with all features!

**Remember:**
- CPQ boats use **exact model IDs** from API (don't transform!)
- CPQ data comes from **warrantyparts_test** (not Eos)
- Test boats always use **dealer 50**
- Standard features query **year 2025** for most boats
- Hull numbers need **VARCHAR(20)** minimum

**That's it!** 🎉

---

**Last Updated:** 2026-02-09
**Maintained By:** Bennington Marine IT
**Questions?** Check CLAUDE.md or UNREGISTERED_INVOICED_BOATS_GUIDE.md
