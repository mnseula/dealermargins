# Session Summary - 2026-02-10
## Window Sticker CPQ Integration & Table Routing Fixes

---

## Context: What We Were Doing

Continuing from previous session where we had fixed CPQ window sticker functionality. User wanted to test importing a pre-2015 boat (ETWINVTEST01) to verify the system handles old boats correctly.

---

## Major Discoveries

### 1. Serial Suffix Routing is Fundamentally Broken

**Problem:** The import script routes boats by **serial suffix** (last 2 digits), not actual model year.

**Impact:** 76,000+ modern boats are in the WRONG tables:
```
Serial Ends    Model Year    Where It Goes       Correct?
──────────────────────────────────────────────────────────
00-04          2016-2025     BoatOptions99_04    ❌ WRONG
99             2022          BoatOptions99_04    ❌ WRONG
15-26          2015-2026     BoatOptions15-26    ✅ CORRECT
```

**Example from BoatOptions99_04:**
- 10,860 boats with model year 22 (2022) but serial ending in "01"
- 18,409 boats with model year 20 (2020) but serial ending in "02"
- ZERO actual 2001 model boats

**Root Cause:** Serial numbering doesn't use year as suffix. The last 2 digits are something else (sequential? plant code?).

### 2. The >= 15 Filter Makes Sense Now

**Original import filter:**
```python
AND TRY_CAST(RIGHT(ser.ser_num, 2) AS INT) >= 15
```

**Why it exists:** Not to filter old boats, but to **avoid the broken routing**.
- Serials ending 15-99 → Route correctly to BoatOptions15-26
- Serials ending 00-14, 99 → Route incorrectly to old tables → fail to load

**Decision:** Restored the >= 15 filter to avoid misrouted boats.

### 3. BoatOptions26 is CPQ Catchall

**ALL CPQ boats go to BoatOptions26** regardless of model year.

**Why:** CPQ boats use **floorplan codes** not year codes:
- Traditional: 25QXFBWA-DE (ends with "DE" = year 2025)
- CPQ: 23ML (ends with "ML" = Malibu floorplan)

**Routing Logic:**
```javascript
// packagePricing.js lines ~189-271
lasttwoletters = realmodel.substring(realmodel.length - 2);

if (lasttwoletters === 'DR') { two = '14'; }
else if (lasttwoletters === 'DE') { two = '15'; }
// ... standard year codes ...

// CPQ Catchall:
if (two === '0') {  // No year code matched
    window.isCPQBoat = true;
    // Load from BoatOptions26
}
```

CPQ boats with floorplan codes (ML, QB, SS, etc.) don't match year patterns → detected as CPQ → route to BoatOptions26.

---

## Data Architecture (Complete Picture)

### Two Separate Data Pipelines

#### 1. Transaction/Order Data (ERP → MySQL)
**Script:** `import_boatoptions_production.py`
```
Source: ERP MSSQL database
  - coitem_mst (line items)
  - CFG table (CPQ configuration attributes)
  - serial_mst (serial numbers)
  - co_mst (orders)
    ↓
Import script extracts:
  - Part 1: Regular line items
  - Part 2: CPQ config attributes (UNION)
    ↓
Destination: warrantyparts.BoatOptions15-26
  - Line items, prices, serial numbers
  - Configuration attributes (CfgName, CfgValue, ConfigID)
  - CPQ boats → BoatOptions26 (catchall)
```

#### 2. Master/Reference Data (CPQ APIs → MySQL)
**Script:** `load_cpq_data.py`
```
Source: Infor CPQ APIs
  - Model prices API (Production)
  - Performance data API (Training)
  - Standard features API (Training)
  - Dealer margins API (Training)
    ↓
Import script populates:
    ↓
Destination: warrantyparts_test database
  - Models (specs, dimensions)
  - ModelPerformance (by performance package)
  - StandardFeatures (feature lists)
  - PerformancePackages (package definitions)
  - Dealers, DealerMargins
```

### How They Work Together

**Window Sticker Generation:**
1. **Load transaction data** (from ERP import)
   - `loadByListName('BoatOptions26')` for CPQ boats
   - Gets: Serial, line items, ConfigID, performance package selection

2. **Load master data** (from CPQ API import via sStatements)
   - `GET_CPQ_LHS_DATA(model, year, hull)` → Model specs for selected package
   - `GET_CPQ_STANDARD_FEATURES(model, year)` → Standard features list

3. **Combine** to create complete window sticker

---

## What We Fixed

### 1. Restored Import Filter
**File:** `import_boatoptions_production.py`
```python
# Restored filter to avoid broken routing:
AND TRY_CAST(RIGHT(ser.ser_num, 2) AS INT) >= 15
```

### 2. Fixed CPQ Year Calculation
**File:** `getunregisteredboats.js` line ~219
```javascript
// Before (WRONG):
var cpqYear = 2025;  // Hardcoded!

// After (CORRECT):
var cpqYear = 2000 + parseInt(serialYear);  // Calculated from serial
```

Now correctly passes year 2022 for 22SFC boats, not hardcoded 2025.

### 3. Updated CPQ LHS Query
**File:** `CONFIGURE_CPQ_SSTATEMENTS.md`

**Query for GET_CPQ_LHS_DATA:**
```sql
-- Search BoatOptions26 only (CPQ catchall)
LEFT JOIN (
    SELECT CfgValue AS perf_package_id
    FROM warrantyparts.BoatOptions26
    WHERE BoatSerialNo = @PARAM3
      AND CfgName = 'perfPack'
    LIMIT 1
) boat_perf ON 1=1
```

No need to UNION multiple tables - all CPQ boats are in BoatOptions26.

### 4. Removed Pre-2005 Handler
**File:** `packagePricing.js`

Removed code for `serialYear < 5` since the import filter blocks those boats anyway.

### 5. Cleaned Up Test Boat
- Removed ETWINVTEST0122 from SerialNumberMaster/RegistrationStatus
- No longer appears in dealer's unregistered boats list

---

## What's Still Needed

### Configure 2 sStatements in EOS

**Reference:** `CONFIGURE_CPQ_SSTATEMENTS.md`

#### 1. GET_CPQ_LHS_DATA
- **Parameters:** model_id, year, hull_no
- **Returns:** Length, Beam, Weight, HP, Capacity, Tubes, etc.
- **Purpose:** Populate LHS (specs) section of window sticker

#### 2. GET_CPQ_STANDARD_FEATURES
- **Parameters:** model_id, year
- **Returns:** Feature list grouped by area (Interior, Exterior, Console, Warranty)
- **Purpose:** Populate standard features section of window sticker

**Testing after configuration:**
1. Hard refresh browser
2. Load any CPQ boat from BoatOptions26
3. Check console for success messages
4. Verify LHS data and standard features display

---

## Key Files Modified This Session

| File | Change | Purpose |
|------|--------|---------|
| `import_boatoptions_production.py` | Restored >= 15 filter | Avoid broken table routing |
| `packagePricing.js` | Removed pre-2005 handler | Not needed with filter |
| `getunregisteredboats.js` | Dynamic year calculation | Fix hardcoded 2025 |
| `CONFIGURE_CPQ_SSTATEMENTS.md` | Created with corrected queries | EOS configuration guide |

---

## Scripts Created This Session

| Script | Purpose | Status |
|--------|---------|--------|
| `fix_etwinvtest01_serial.py` | Update test boat serial | Used & discarded |
| `verify_etwinvtest0122.py` | Verify boat in correct table | Used for testing |
| `manual_insert_test_boat.py` | Manual copy to BoatOptions22 | Used & discarded |
| `move_test_boat_to_26.py` | Move to BoatOptions26 catchall | Used & complete |
| `update_erp_serial.py` | Update ERP serial (failed auth) | Not used |

---

## Important Insights

### Serial Suffix ≠ Model Year
- Serial endings (00-14, 15-26, 99) are NOT year indicators
- They're something else (sequential counter? plant code?)
- Can't rely on serial suffix for year-based routing
- Modern boats with certain serial patterns end up in wrong tables

### CPQ Detection Logic
- CPQ boats use floorplan codes (ML, QB, SS, etc.)
- Don't match standard year codes (DR, DE, DF, SE, SF, etc.)
- System detects "no year code match" → CPQ boat → BoatOptions26
- This works for both import and browser loading

### Two-Tier Data Model
- **Transaction data** (what was ordered) from ERP
- **Master data** (what's available) from CPQ APIs
- sStatements JOIN them together for complete info

---

## Boat Counts by Table

```
BoatOptions05_07:      217,842 rows
BoatOptions08_10:      186,717 rows
BoatOptions11_14:      819,560 rows
BoatOptions15:         252,147 rows
BoatOptions16:         276,118 rows
BoatOptions17:         268,093 rows
BoatOptions18:         368,407 rows
BoatOptions19:         353,550 rows
BoatOptions20:         291,393 rows
BoatOptions21:         473,224 rows
BoatOptions22:         339,183 rows (test boat removed)
BoatOptions23:         373,522 rows
BoatOptions24:         200,459 rows
BoatOptions25:         209,143 rows
BoatOptions26:         103,041 rows (CPQ catchall)
```

---

## Next Steps (For Next Session)

1. **Configure sStatements in EOS**
   - Use `CONFIGURE_CPQ_SSTATEMENTS.md` as guide
   - Test with real CPQ boat from BoatOptions26

2. **Consider Future Fixes** (Optional)
   - Fix routing to use model year from BoatModelNo instead of serial suffix
   - Would require re-importing 76,000+ misrouted boats
   - Only pursue if >= 15 filter becomes insufficient

3. **Document CPQ Boat Import Process**
   - When/how CPQ data flows from EQ → ERP → MySQL
   - Frequency of master data updates from CPQ APIs

---

## Git Commits This Session

```
272ce2f - Fix pre-2005 boat loading in packagePricing.js
0f84e98 - Fix list name for pre-2005 boats to use CamelCase
bfc5e2d - Add script to fix ETWINVTEST01 serial number mismatch
1f18c8d - Add script to update serial in ERP database
0de4df9 - Add manual workaround for test boat without ERP write access
5cb3e7a - Restore >= 15 serial filter to avoid broken table routing
2c2acfe - Fix CPQ year calculation and add sStatement configuration guide
580e7f3 - Extend UNION to include BoatOptions15-21 in CPQ LHS query
e41ad21 - Revert to BoatOptions26-only query for CPQ LHS data
e67400d - Add script to move test boat to BoatOptions26 catchall table
```

---

## Current System State

✅ **Working:**
- Import filter blocks misrouted boats (>= 15)
- CPQ boats correctly detected and routed to BoatOptions26
- JavaScript calculates correct year from serialYear
- Pre-2005 handler removed (not needed)

⏳ **Pending:**
- sStatements configuration in EOS (GET_CPQ_LHS_DATA, GET_CPQ_STANDARD_FEATURES)

❌ **Known Issues:**
- 76,000+ boats in wrong tables (00-14, 99 serial endings)
- These boats are excluded by >= 15 filter (won't import)
- Proper fix requires routing by model year (major refactor)

---

**Session ended:** 2026-02-10
**Next session:** Continue with sStatements configuration and testing
