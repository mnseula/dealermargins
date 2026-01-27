# Session Summary: Stored Procedure Implementation & Cross-Database Architecture

**Date:** 2026-01-27
**Focus:** GetWindowStickerData stored procedure with dynamic year support and cross-database queries

---

## What We Accomplished Today

### 1. Deployed GetWindowStickerData Stored Procedure
**Location:** `warrantyparts_test` database
**Purpose:** Generate window stickers and retrieve boat configuration data

**Procedure Signature:**
```sql
CALL GetWindowStickerData(
    p_model_id VARCHAR(20),      -- e.g., '23SSSE' or '25QXFBWA'
    p_dealer_id VARCHAR(20),     -- e.g., '00333834'
    p_year INT,                  -- e.g., 2025 or 2026
    p_identifier VARCHAR(30)     -- HIN or Order Number (NULL for all boats)
);
```

**Returns 4 Result Sets:**
1. Model Information (from CPQ catalog)
2. Performance Specifications (from CPQ catalog)
3. Standard Features (from CPQ catalog)
4. **Included Options/Accessories (from PRODUCTION sales data)** ✅

### 2. Implemented Cross-Database Architecture (Option B)

**Design Decision:** Keep CPQ catalog separate from production sales data until full migration.

**Database Layout:**
- **CPQ Catalog Data:** `warrantyparts_test`
  - Tables: Models, ModelPricing, Series, ModelPerformance, StandardFeatures, etc.
  - Source: Infor CPQ APIs
  - Purpose: Future boat configurations

- **Production Sales Data:** `warrantyparts`
  - Tables: BoatOptions24, BoatOptions25, BoatOptions26, etc.
  - Source: Historical ERP/sales system
  - Purpose: Actual boats manufactured and sold

**The stored procedure queries BOTH databases:**
```sql
-- CPQ data from warrantyparts_test
SELECT ... FROM Models m JOIN Series s ...

-- Production data from warrantyparts (dynamic table selection)
SELECT ... FROM warrantyparts.BoatOptions{year} ...
```

### 3. Added Dynamic Year Support

**Problem Solved:** Hardcoded `BoatOptions25` wouldn't work for 2026 boats.

**Solution:** Dynamic SQL based on year parameter
```sql
SET @year_suffix = RIGHT(CAST(p_year AS CHAR), 2);  -- 2025 → '25'
SET @table_name = CONCAT('warrantyparts.BoatOptions', @year_suffix);
-- Results in: warrantyparts.BoatOptions25 or BoatOptions26, etc.
```

**Now supports:**
- Year 2024 → `warrantyparts.BoatOptions24`
- Year 2025 → `warrantyparts.BoatOptions25`
- Year 2026 → `warrantyparts.BoatOptions26`

### 4. Verified Model Year Suffix System

**Discovered Pattern:**
- **SE suffix** = 2025 model year (dominant in BoatOptions25: 181,256 records)
- **SF suffix** = 2026 model year (dominant in BoatOptions26: 86,205 records)
- Model years start **August 1** of the previous calendar year

**Examples:**
- Model `22SSRSE` = 22' S Series Stern Radius, **2025** model year
- Model `22SSRSF` = 22' S Series Stern Radius, **2026** model year

### 5. Identified The Two Model Numbering Systems

**Old Production Format (in BoatOptions tables):**
- Examples: `23SSSE`, `22SSRSE`, `20SLSE`
- First 2 digits = **boat length in feet**
- Last 2 letters = **model year** (SE=2025, SF=2026)
- Used in actual manufactured boats

**New CPQ Format (in Models table from API):**
- Examples: `25QXFBWA`, `168SF`, `26LXSFBWA`
- First 2-3 digits = **boat length in feet**
- Suffix may include year indicator
- Used for future configurations

**Current Mismatch:**
- CPQ API models: 214 models loaded from Infor CPQ
- Production models: Thousands of actual boats with old numbering
- **NO OVERLAP** between the two systems currently

---

## Current Status: Working & Tested

### ✅ What's Working

1. **Stored procedure deployed** and verified in `warrantyparts_test`
2. **Cross-database queries** functioning correctly
3. **Dynamic year selection** works (2024, 2025, 2026)
4. **HIN filtering** works correctly
5. **Production accessories** returned successfully

### ✅ Test Results

**Test Boat:** ETWS1509J425 (23SSSE, 2025 model year)
**Dealer:** NICHOLS MARINE SE OK LLC (00333834)

```sql
CALL GetWindowStickerData('23SSSE', '00333834', 2025, 'ETWS1509J425');
```

**Results:**
- Result Set 1 (Model Info): 0 rows - Expected (model not in CPQ)
- Result Set 2 (Performance): 0 rows - Expected (not in CPQ)
- Result Set 3 (Features): 0 rows - Expected (not in CPQ)
- Result Set 4 (Accessories): **1 row** - ✅ **WORKING!**
  - Item: 914249 - CENTER STORAGE SPS S SER ($1,100.00)

**Additional Tests:**
- Verified 2026 year support: ✅ Working (12 accessories returned from BoatOptions26)
- Verified NULL identifier: ✅ Returns all boats of a model (27 total accessories)
- Verified with multiple Nichols Marine boats: ✅ All working

---

## Git Commits Made

### Commit 1: `7c20fab`
**Message:** "Update GetWindowStickerData to query production sales data"
- Changed from `BoatOptions25_test` to `warrantyparts.BoatOptions25`
- Implemented cross-database architecture

### Commit 2: `4af54ab`
**Message:** "Add dynamic year support to GetWindowStickerData procedure"
- Added dynamic table selection based on year parameter
- Uses prepared statements for runtime table name resolution

**Files Updated:**
- `stored_procedures.sql`
- `reload_window_sticker_procedure.sql`

---

## Known Limitations & Issues

### 1. Model Number Mismatch
**Problem:** Production boats use old model numbers (23SSSE) that don't exist in CPQ (25QXFBWA).

**Impact:**
- CPQ data (Models, Performance, Features) returns empty for production boats
- Only accessories/options data returns (which is the most important)

**When This Will Be Fixed:**
- When new CPQ-configured boats start being manufactured
- When model number translation/mapping is implemented

### 2. Dealer Information Not Populating
**Problem:** Dealer fields return NULL even with valid dealer_id.

**Root Cause:**
- Procedure joins to `warrantyparts_test.Dealers` table
- Dealer data exists in `Eos.dealers` table
- No dealer data has been loaded into `warrantyparts_test.Dealers`

**Current Workaround:** Dealer info available from `Eos.dealers` directly

### 3. CPQ Tables Not in Production Database
**Status:** By design (Option B architecture)

**Current State:**
- CPQ tables in `warrantyparts_test`
- Production sales in `warrantyparts`

**Future Migration:**
- Eventually move all tables to `warrantyparts` (production)
- Will require re-deploying stored procedure to production database

---

## Work Still To Do

### High Priority

1. **Load Dealer Data into CPQ Database**
   - Source: `Eos.dealers` table or CPQ API
   - Target: `warrantyparts_test.Dealers`
   - Purpose: Make dealer info populate in window stickers

2. **Model Number Mapping/Translation**
   - Create mapping between old (23SSSE) and new (25QXFBWA) model numbers
   - OR wait for new models to enter production
   - Purpose: Get full CPQ data for production boats

3. **Test with 2026 Model Year Boats**
   - Verify suffix pattern (SF for 2026)
   - Test with actual dealer 2026 inventory
   - Confirm BoatOptions26 queries working in production use

### Medium Priority

4. **Update CLAUDE.md Documentation**
   - Document cross-database architecture
   - Update stored procedure examples
   - Add dynamic year support notes
   - Document model numbering systems

5. **Create Additional Stored Procedures**
   - Procedure for getting window sticker by HIN only (auto-detect model)
   - Procedure for listing all boats for a dealer
   - Procedure for getting available models by year

6. **Performance Optimization**
   - Review query performance with large datasets
   - Add indexes if needed
   - Consider caching for frequently accessed data

### Low Priority

7. **Handle Edge Cases**
   - What happens with year 2027, 2028, etc.?
   - Handle boats with no accessories gracefully
   - Better error messages when model not found

8. **Production Migration Planning**
   - Plan to move CPQ tables to `warrantyparts` database
   - Update stored procedure to remove cross-database queries
   - Test thoroughly before migration

---

## Database Credentials & Locations

### RDS MySQL
```
Host:     ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com
User:     awsmaster
Password: VWvHG9vfG23g7gD
```

### Databases
- **warrantyparts_test** - CPQ catalog data (Models, Pricing, Performance, Features)
- **warrantyparts** - Production sales data (BoatOptions tables)
- **Eos** - Dealer and other reference data

---

## Key Files

### Stored Procedures
- `stored_procedures.sql` - Complete stored procedure definitions
- `reload_window_sticker_procedure.sql` - Quick reload script for GetWindowStickerData

### Python Scripts
- `load_cpq_data.py` - Unified loader for all CPQ API data
- `generate_window_sticker.py` - Python wrapper for calling stored procedure

### Database Schemas
- `database_schema.sql` - CPQ catalog tables
- `dealer_margins_schema.sql` - Dealer and margin tables

---

## Example Usage

### Get Window Sticker for Specific Boat
```sql
USE warrantyparts_test;

CALL GetWindowStickerData(
    '23SSSE',           -- Model ID
    '00333834',         -- Dealer ID (NICHOLS MARINE SE OK LLC)
    2025,               -- Year
    'ETWS1509J425'      -- HIN (specific boat)
);
```

### Get All Boats of a Model
```sql
CALL GetWindowStickerData('23SSSE', '00333834', 2025, NULL);
```

### 2026 Model Year
```sql
CALL GetWindowStickerData('22SSRSF', '00333834', 2026, NULL);
```

---

## Dealer Information: NICHOLS MARINE SE OK LLC

**From Eos.dealers table:**
```
DlrNo:          00333834
DealerName:     NICHOLS MARINE SE OK LLC
City:           MCALESTER
State:          OK
Contact:        Gary Nichols, VP / Clint Riddle, GM
Email:          clint@nicholsmarine.com
Status:         Active
Parent:         000000333833
```

**Sample Unregistered Boats:**
- ETWS1509J425 - 23 S STERN FISHING (2025)
- ETWS3377A525 - 22 S 4 PT FISHING (2025)
- ETWS2270K425 - 18 S BOW FISHING NARROW BEAM (2025)

---

## Technical Notes

### HIN Format (Standard post-1984)
- Characters 1-3: Manufacturer code (ETW = Bennington)
- Characters 4-8: Hull serial number
- Characters 9-10: Month code
- **Characters 11-12: Model year (last 2 digits)**

Example: `ETWS1509J425`
- ETW = Bennington
- S1509 = Serial
- J4 = October
- **25 = 2025 model year**

### Why Prepared Statements?
MySQL doesn't allow direct variable substitution in table names, so we use:
```sql
SET @table_name = CONCAT('warrantyparts.BoatOptions', @year_suffix);
PREPARE stmt FROM @query;
EXECUTE stmt USING @params;
DEALLOCATE PREPARE stmt;
```

---

## Next Session Priorities

1. **Load dealer data** into warrantyparts_test.Dealers
2. **Test procedure** with CPQ models that DO exist (if any production boats exist)
3. **Document** the model mapping challenge
4. **Plan** for eventual migration to single database

---

## Questions for Next Session

1. Should we create a model mapping table to link old/new model numbers?
2. When will CPQ-configured boats start entering production?
3. Should we load Eos.dealers into warrantyparts_test.Dealers or keep cross-database join?
4. What's the timeline for moving everything to production database?
5. Do we need additional stored procedures for other use cases?

---

**End of Session Summary**
