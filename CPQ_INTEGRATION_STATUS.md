# CPQ Integration Status - 2026-02-07

## 🔥 CRITICAL FIX - 2026-02-07

**Issue:** Yesterday's CPQ integration broke old/legacy boats. Dealers couldn't print window stickers for non-CPQ boats.

**Root Cause:** CPQ fallback logic was triggering for ALL boats when Boats_ListOrder query failed, not just CPQ boats. Since Boats_ListOrder tables don't exist for older model years, the fallback ran for old boats too but with incompatible data structures.

**Fix Applied:** Added `isCPQBoat` flag that only triggers CPQ fallback when:
1. Year code detection failed (two === '0') AND
2. Boats_ListOrder query failed

**Status:** ✅ FIXED (commit 90fdce8)
- Old boats: Use original error handling when Boats_ListOrder missing
- CPQ boats: Use new fallback to extract SERIES from boatoptions
- Both boat types now work correctly

---

## Summary
Successfully integrated CPQ boats (using floorplan codes like ML, QB) into the window sticker system. Window stickers now load and display pricing correctly for CPQ boats. Both legacy boats and CPQ boats now work correctly. Print functionality for CPQ boats has a remaining issue that needs to be addressed.

---

## ✅ What's Working

### 1. CPQ Boat Detection and Year Calculation
**File:** `packagePricing.js` (lines 177-204)

CPQ boats use floorplan codes (ML, QB, etc.) instead of year codes (DR=14, DE=15, etc.). Added catchall logic that:
- Detects when no year code matches (two = '0')
- Uses serialYear to determine correct model year
- Sets `two = '25'` for serialYear 26 (2026 boats use 2025 model year lists)

**Test Case:**
- Boat: ETWTEST26
- Model: 23ML
- serialYear: 26
- Result: two = '25' ✅

### 2. Price Mapping: ExtSalesAmount → MSRP
**File:** `packagePricing.js` (lines 41-48)

Window sticker expects `MSRP` field but BoatOptions26 has `ExtSalesAmount`. Added mapping:
```javascript
if (window.boatoptions && window.boatoptions.length > 0) {
    for (var i = 0; i < window.boatoptions.length; i++) {
        window.boatoptions[i].MSRP = window.boatoptions[i].ExtSalesAmount || 0;
    }
}
```

**Result:** All 63 items for ETWTEST26 now have MSRP values ✅

### 3. CPQ Fallback: Extract SERIES from BoatOptions
**File:** `packagePricing.js` (lines 215-234)

The Boats_ListOrder_2025 table query returns 500 error through CPQ platform. Added fallback:
- If `blo` is empty/invalid → Extract SERIES from existing boatoptions data
- Filter for boat record (ItemMasterMCT = 'BOA' or 'BOI')
- Extract Series field from that record
- Set boatpricingtype = 'reg' for CPQ boats

**Result:** SERIES = 'M' correctly set, allowing margin calculations to work ✅

### 4. Database Tables for CPQ Data
**Database:** `warrantyparts`

Created three tables populated from `warrantyparts_test.Models`:

1. **Boats_ListOrder_2025** - 283 models
   - REALMODELNAME (Primary Key)
   - SERIES
   - PRICING
   - model_name, length_feet, seats

2. **options_matrix_2025** - 1,073 performance configs
   - MODEL, package_name, perf_package_id
   - max_hp, no_of_tubes, person_capacity
   - hull_weight, pontoon_gauge, transom, tube_height

3. **standards_matrix_2025** - 15,365 standard features
   - MODEL, feature_code, area, description, sort_order

**23ML Data:**
- ✅ 1 boat record in Boats_ListOrder_2025
- ✅ 7 performance configurations
- ✅ 48 standard features

### 5. Test Boat Data
**Serial:** ETWTEST26
**Database:** `warrantyparts.BoatOptions26`

- 63 line items totaling $109,250
- Base boat (23ML): $41,131
- Engine (VF150LB): $15,420
- Various accessories with prices
- Series: M
- Model description: "23 M CRUISE"

---

## ❌ What's Not Working Yet

### Print Window Sticker Functionality

**Error:** `ReferenceError: prfPkgs is not defined`

**What's Happening:**
1. Window sticker loads correctly with pricing ✅
2. User clicks PRINT button
3. Print script runs and queries:
   ```
   boat_specs WHERE MODEL = 'Base Boat'
   ```
   (Should be `MODEL = '23ML'`)

4. Script looks for `prfPkgs` variable at line 100
5. Variable doesn't exist → Error

**Console Output:**
```
Print boatPricing: reg
boat_specs WHERE MODEL = 'Base Boat'
Base Boat 25
Product List LIST/PRODUCT_NAME[="Model Selection"]&LIST/MODEL_YEAR[="2025"]
perfpkgid false
CodeExec error ReferenceError: prfPkgs is not defined
```

**CPQ Variables Set Incorrectly:**
```
BOAT_INFO/BOAT_MODEL = Base Bo        (truncated, should be "23ML")
BOAT_INFO/BOAT_REAL_MODEL = Base Boat (should be "23ML")
```

**Root Cause:**
The print window sticker script (likely "unregistered boats.js" or similar) is:
1. Not accessible in this git repository (part of CPQ platform)
2. Using incorrect model name when querying boat_specs
3. Missing the `prfPkgs` variable definition
4. Not handling CPQ boats correctly

---

## 🔧 Files Modified

### 1. packagePricing.js
**Commits:**
- `c70b9ac` - Original backup before modifications
- `0346ffc` - Added CPQ catchall logic for floorplan codes
- `3080e7e` - Added price mapping (ExtSalesAmount → MSRP)
- `ac424b4` - Changed Boats_ListOrder query to standard WHERE syntax
- `0a40390` - Added CPQ fallback to extract SERIES from boatoptions
- `2fae170` - Fixed fallback condition to handle empty Object

**Key Changes:**
- Lines 41-48: Price mapping
- Lines 177-204: CPQ year calculation catchall
- Lines 215-234: SERIES extraction fallback

---

## 📋 Next Steps

### Tomorrow's Tasks

1. **Locate the Print Script**
   - File name: Possibly "unregistered boats.js" or print window sticker action
   - Location: CPQ platform admin interface (not in git repo)
   - Need to: Export/access this file to modify it

2. **Fix Print Script Issues**
   - Update to use correct MODEL ('23ML' instead of 'Base Boat')
   - Define or load the `prfPkgs` variable
   - Add CPQ boat handling similar to packagePricing.js
   - Ensure BOAT_INFO variables are set correctly

3. **Test End-to-End**
   - Load window sticker for ETWTEST26 ✅ (already working)
   - Verify pricing displays correctly ✅ (already working)
   - Click PRINT button ❌ (needs fixing)
   - Verify PDF generates with correct model name and specs

---

## 🗂️ Key Database Tables

### Production Database: `warrantyparts`

**CPQ Data (Read/Write):**
- `Boats_ListOrder_2025` - Boat metadata
- `options_matrix_2025` - Performance configurations
- `standards_matrix_2025` - Standard features

**Sales Data (Read Only):**
- `BoatOptions26` - 2026 model year boat line items with pricing
- `SerialNumberMaster` - Boat master records
- `SerialNumberRegistrationStatus` - Registration status

### Test Database: `warrantyparts_test`

**CPQ Source Tables:**
- `Models` - All boat models
- `ModelPerformance` - Performance specs
- `ModelStandardFeatures` - Standard features junction table
- `StandardFeatures` - Feature definitions
- `PerformancePackages` - Performance package definitions

---

## 🔑 Key Variables and Mappings

### JavaScript Variables (packagePricing.js)

```javascript
window.serialYear = 26              // Model year (2026)
window.boatYear = '26'              // Last 2 digits of serial
window.two = '25'                   // Year for table lookups (2026 uses 2025 tables)
window.currentmodelyear = '2025'    // Calculated: '20' + two

window.model = '23ML'               // From BoatOptions26.ItemNo
window.realmodel = '23ML'           // From BoatOptions26.BoatModelNo
window.fullmodel = '23 M CRUISE'    // From BoatOptions26.ItemDesc1

window.series = 'M'                 // From BoatOptions26.Series (via CPQ fallback)
window.boatpricingtype = 'reg'      // Set by CPQ fallback
```

### Database Field Mappings

**BoatOptions26 → JavaScript:**
- `ItemNo` → `window.model`
- `ItemDesc1` → `window.fullmodel`
- `BoatModelNo` → `window.realmodel`
- `Series` → `window.series`
- `ExtSalesAmount` → `item.MSRP` (mapped at runtime)

**Models → Boats_ListOrder_2025:**
- `model_id` → `REALMODELNAME`
- `series_id` → `SERIES`
- `'reg'` → `PRICING` (hardcoded)

---

## 📊 Test Data: ETWTEST26

### Boat Configuration
```
Serial Number:    ETWTEST26
Model:            23ML (M-Series, 23 feet)
Description:      23 M CRUISE
Series:           M
Model Year:       2026 (serialYear = 26)
Invoice:          25217358
Order:            SO00936065
Dealer:           50 (PONTOON BOAT, LLC)
Status:           Test boat (Active = 0)
```

### Pricing Breakdown
```
Base Boat:        $41,131
Engine:           $15,420
Accessories:      $52,699
────────────────────────
Total:            $109,250
Items:            63
```

### Database Presence
- ✅ BoatOptions26 (63 records)
- ✅ SerialNumberMaster (1 record)
- ✅ SerialNumberRegistrationStatus (1 record)
- ✅ Boats_ListOrder_2025 (23ML present)
- ✅ options_matrix_2025 (7 performance configs for 23ML)
- ✅ standards_matrix_2025 (48 standard features for 23ML)

---

## 🐛 Known Issues

1. **Boats_ListOrder_2025 Query Returns 500 Error**
   - Workaround: CPQ fallback extracts SERIES from boatoptions ✅
   - Root cause: Unknown (query works in MySQL but fails through CPQ platform)
   - Impact: Minimal (fallback working perfectly)

2. **Print Window Sticker Fails**
   - Error: `prfPkgs is not defined`
   - Cause: Print script not handling CPQ boats
   - Status: **TO BE FIXED TOMORROW**
   - File needed: "unregistered boats.js" or equivalent print script

---

## 💾 Database Credentials

**MySQL RDS:**
```
Host:     ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com
User:     awsmaster
Password: VWvHG9vfG23g7gD
Database: warrantyparts (production)
          warrantyparts_test (CPQ data source)
```

---

## 📝 Git Commits

### 2026-02-06 (Initial CPQ Integration)
```
c70b9ac - Backup: Original packagePricing.js before modifications
0346ffc - Add CPQ catchall logic for floorplan codes (ML, QB, etc.)
3080e7e - Add price mapping: ExtSalesAmount → MSRP
ac424b4 - Fix: Change Boats_ListOrder query to standard WHERE syntax
0a40390 - Add CPQ fallback: Extract SERIES from boatoptions
2fae170 - Fix: CPQ fallback condition to handle empty Object
cf01e4f - Add comprehensive CPQ integration status document
```

### 2026-02-07 (Critical Fix for Legacy Boats)
```
90fdce8 - Fix: Only use CPQ fallback for actual CPQ boats, not all boats
```

All changes pushed to: `github.com:mnseula/dealermargins.git`

---

## 🎯 Success Metrics

### Today's Accomplishments
- ✅ CPQ boats load in window sticker system
- ✅ Correct model year tables loaded (2026 uses 2025)
- ✅ Pricing displays correctly ($109,250 total)
- ✅ SERIES extracted and margins calculated
- ✅ All database tables populated with CPQ data
- ✅ Fallback system working when primary query fails

### Tomorrow's Goal
- ❌ Fix print functionality so window stickers can be generated as PDFs
- ❌ Identify and update the print script to handle CPQ boats

---

## 📚 Related Documentation

- `CLAUDE.md` - Project overview and credentials
- `JAVASCRIPT_CPQ_INTEGRATION.md` - CPQ JavaScript integration details
- `PRICING_AND_MARGINS_EXPLAINED.md` - How pricing and margins work
- `DATABASE_ARCHITECTURE.md` - Database schema and architecture
- `packagePricing.js` - Main boat data loading script (modified today)
- `Calculate2021.js` - Price calculation script

---

**Last Updated:** 2026-02-06 End of Day
**Status:** Window sticker loading ✅ | Print functionality ❌ (tomorrow's task)
**Next Session:** Fix print script to handle CPQ boats and resolve `prfPkgs` error
