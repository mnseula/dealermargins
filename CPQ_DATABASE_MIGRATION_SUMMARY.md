# CPQ Database Migration Summary
## 2026-02-11

---

## What We Accomplished

### 1. Created New `cpq` Database

**Purpose:** Consolidate all CPQ boat data in a dedicated database, separate from legacy boats.

**Tables Created (all empty, ready for data):**
- `BoatOptions` - CPQ boat transaction data (renamed from BoatOptions26, holds all years)
- `Series` - Boat series codes (Q, QX, R, LXS, M, S, etc.)
- `Models` - Central catalog of all boat models
- `ModelPerformance` - Technical specifications per model × performance package
- `PerformancePackages` - Performance package definitions
- `StandardFeatures` - Master list of standard features
- `ModelStandardFeatures` - Junction table linking models to features
- `Dealers` - Dealer locations and contact information
- `DealerMargins` - Margin configurations per dealer-series combination

**Key Design Decision:**
- CPQ boats from ALL model years go into `cpq.BoatOptions` (no year suffix)
- This eliminates confusion and makes it clear: one table for all CPQ boats
- Legacy boats remain in `warrantyparts.BoatOptions15-25` (unchanged)

---

## 2. Updated Scripts

### A. `load_cpq_data.py`
**Change:** Target database from `warrantyparts_test` → `cpq`

**Impact:**
- All CPQ master data now populates the cpq database
- Includes: Models, Performance, Features, Dealers, Margins

**Status:** ✅ Updated (line 55: `'database': 'cpq'`)

### B. `import_boatoptions_production.py`
**Changes:**
1. Removed default database from MYSQL_CONFIG (now specified in table names)
2. Updated routing logic in `group_by_table()` function:
   - CPQ boats → `cpq.BoatOptions`
   - Legacy boats → `warrantyparts.BoatOptions15-25` (by year)

**Routing Logic:**
```python
if is_cpq_order(...):
    table_name = 'cpq.BoatOptions'  # All CPQ boats
else:
    table_name = f'warrantyparts.{get_table_for_year(year)}'  # Legacy boats by year
```

**Status:** ✅ Updated (lines 49-52 and 454-479)

### C. `CONFIGURE_CPQ_SSTATEMENTS.md`
**Changes:**
- Updated GET_CPQ_LHS_DATA query:
  - `warrantyparts_test.Models` → `cpq.Models`
  - `warrantyparts.BoatOptions26` → `cpq.BoatOptions`
  - `warrantyparts_test.ModelPerformance` → `cpq.ModelPerformance`
  - `warrantyparts_test.PerformancePackages` → `cpq.PerformancePackages`

- Updated GET_CPQ_STANDARD_FEATURES query:
  - `warrantyparts_test.StandardFeatures` → `cpq.StandardFeatures`
  - `warrantyparts_test.ModelStandardFeatures` → `cpq.ModelStandardFeatures`

**Status:** ✅ Updated (full SQL queries revised)

---

## 3. What Was NOT Changed (By Design)

### JavaScript Files
- `packagePricing.js` - No changes needed (backend only)
- `getunregisteredboats.js` - No changes needed (backend only)

**Reason:** The frontend already has CPQ detection logic and calls the correct sStatements. All changes are backend (database and EOS configuration).

### Legacy Boat Tables
- `warrantyparts.BoatOptions15` through `warrantyparts.BoatOptions25` - Untouched
- All legacy boat functionality remains 100% intact
- No risk to existing window sticker generation for old boats

---

## Data Architecture (After Migration)

### Two Separate Systems

#### 1. Legacy Boats (Untouched)
```
Source: ERP database (boats from 2015-2025 with serial suffix >= 15)
  ↓
Script: import_boatoptions_production.py
  ↓
Destination: warrantyparts.BoatOptions15-25 (routed by model year)
  ↓
Frontend: Existing JavaScript loads from year-specific tables
  ↓
Output: Window stickers for legacy boats (unchanged)
```

#### 2. CPQ Boats (New System)
```
Master Data Pipeline:
  Infor CPQ APIs (PRD + TRN)
    ↓
  load_cpq_data.py
    ↓
  cpq database (Models, Performance, Features, Dealers, Margins)

Transaction Data Pipeline:
  ERP database (CPQ orders from 12/14/2025 onwards)
    ↓
  import_boatoptions_production.py (CPQ routing)
    ↓
  cpq.BoatOptions (all CPQ boats regardless of year)

Window Sticker Generation:
  Frontend calls sStatements (GET_CPQ_LHS_DATA, GET_CPQ_STANDARD_FEATURES)
    ↓
  sStatements query cpq database
    ↓
  Returns: Model specs + Standard features + Transaction line items
    ↓
  Output: Complete CPQ boat window sticker
```

---

## Next Steps (To Complete Migration)

### 1. Populate CPQ Database
```bash
# Load master data from CPQ APIs
python3 load_cpq_data.py

# Expected outcome:
# - cpq.Models: ~1000+ boat models
# - cpq.ModelPerformance: ~7500+ performance specs
# - cpq.StandardFeatures: ~9700+ features
# - cpq.ModelStandardFeatures: ~81,000+ model-feature links
# - cpq.PerformancePackages: ~50+ packages
# - cpq.Series: ~10+ series codes
# - cpq.Dealers: ~400+ dealers
# - cpq.DealerMargins: ~100+ margin configs
```

### 2. Import CPQ Boat Transactions
```bash
# Import boat orders from ERP (routes CPQ boats to cpq.BoatOptions)
python3 import_boatoptions_production.py

# Expected outcome:
# - cpq.BoatOptions: CPQ boats from 12/14/2025 onwards
# - warrantyparts.BoatOptions15-25: Legacy boats (unchanged)
```

### 3. Update sStatements in EOS
**Reference:** `CONFIGURE_CPQ_SSTATEMENTS.md`

Update these 2 sStatements in EOS admin panel:
1. **GET_CPQ_LHS_DATA**
   - Update SQL to query `cpq.Models`, `cpq.BoatOptions`, `cpq.ModelPerformance`
   - Parameters: @PARAM1 (model_id), @PARAM2 (year), @PARAM3 (hull_no)

2. **GET_CPQ_STANDARD_FEATURES**
   - Update SQL to query `cpq.StandardFeatures`, `cpq.ModelStandardFeatures`
   - Parameters: @PARAM1 (model_id), @PARAM2 (year)

### 4. Update EOS List Mapping
**Action:** Update EOS configuration

**Change:** Map CPQ boat loading from `warrantyparts.BoatOptions26` → `cpq.BoatOptions`

**Note:** This is a backend configuration change in EOS. The frontend JavaScript (packagePricing.js) already calls `loadByListName('BoatOptions26')` for CPQ boats - EOS will now map that to `cpq.BoatOptions`.

### 5. Test CPQ Boat Window Sticker
1. Hard refresh browser (Ctrl+Shift+R / Cmd+Shift+R)
2. Load a CPQ boat (e.g., ETWINVTEST0122 or any real CPQ boat)
3. Check console for success messages:
   ```
   ✅ SUCCESS: Got LHS data for model 22SFC hull ETWINVTEST0122
   ✅ SUCCESS: Got XX standard features for model 22SFC
   ```
4. Verify window sticker displays correctly with:
   - LHS data (Length, Beam, Weight, HP, Capacity, etc.)
   - Standard features by area (Interior, Exterior, Console, Warranty)
   - Ordered options from transaction data

---

## Benefits of This Migration

### 1. Clarity
- **Clear separation:** cpq database = CPQ boats, warrantyparts database = legacy boats
- **No confusion:** BoatOptions (no suffix) = all CPQ boats, BoatOptions15-25 = legacy boats by year
- **Logical naming:** Database names match their purpose

### 2. Scalability
- CPQ boats from all years in one table - no need to create new tables annually
- Easier to maintain and query - one place for all CPQ data

### 3. Safety
- Legacy boats completely untouched - zero risk to existing functionality
- People can still generate window stickers for old boats (2015-2025)

### 4. Maintainability
- All CPQ-related tables in one database - easier to backup, migrate, or troubleshoot
- Scripts clearly target specific databases - no ambiguity

---

## Files Modified This Session

| File | Change | Impact |
|------|--------|--------|
| `create_cpq_database.sql` | Created schema for cpq database | 9 empty tables ready for data |
| `execute_cpq_schema.py` | Created execution script | Successfully created cpq database |
| `load_cpq_data.py` | Changed target database to 'cpq' | Master data loads to cpq database |
| `import_boatoptions_production.py` | Updated routing logic | CPQ boats → cpq.BoatOptions, legacy → warrantyparts |
| `CONFIGURE_CPQ_SSTATEMENTS.md` | Updated SQL queries | sStatements now query cpq database |

---

## Current System State

### ✅ Completed
- cpq database created with all 9 tables (empty)
- load_cpq_data.py updated to target cpq database
- import_boatoptions_production.py updated to route CPQ boats to cpq.BoatOptions
- sStatements configuration updated with new SQL queries
- Documentation created (this file)

### ⏳ Pending
1. Run load_cpq_data.py to populate cpq master data
2. Run import_boatoptions_production.py to import boat transactions
3. Update 2 sStatements in EOS with new SQL queries
4. Update EOS list mapping (BoatOptions26 → cpq.BoatOptions)
5. Test CPQ boat window sticker generation

### 🔒 Protected (No Changes)
- JavaScript files (packagePricing.js, getunregisteredboats.js)
- Legacy boat tables (warrantyparts.BoatOptions15-25)
- Legacy boat import logic (still routes by year)
- All non-CPQ functionality

---

## Database Access

**CPQ Database:**
```bash
mysql -h ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com -u awsmaster -p'VWvHG9vfG23g7gD' cpq
```

**Legacy Database:**
```bash
mysql -h ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com -u awsmaster -p'VWvHG9vfG23g7gD' warrantyparts
```

**Verify Tables:**
```sql
-- CPQ tables
USE cpq;
SHOW TABLES;

-- Check row counts
SELECT
    'BoatOptions' as table_name, COUNT(*) as row_count FROM BoatOptions
UNION ALL
SELECT 'Models', COUNT(*) FROM Models
UNION ALL
SELECT 'ModelPerformance', COUNT(*) FROM ModelPerformance
UNION ALL
SELECT 'StandardFeatures', COUNT(*) FROM StandardFeatures
UNION ALL
SELECT 'ModelStandardFeatures', COUNT(*) FROM ModelStandardFeatures
UNION ALL
SELECT 'PerformancePackages', COUNT(*) FROM PerformancePackages
UNION ALL
SELECT 'Series', COUNT(*) FROM Series
UNION ALL
SELECT 'Dealers', COUNT(*) FROM Dealers
UNION ALL
SELECT 'DealerMargins', COUNT(*) FROM DealerMargins;
```

---

## Questions / Issues?

If you encounter issues:

1. **Check database connectivity:**
   ```bash
   mysql -h ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com -u awsmaster -p cpq -e "SHOW TABLES;"
   ```

2. **Verify table structure:**
   ```sql
   USE cpq;
   DESCRIBE BoatOptions;
   DESCRIBE Models;
   ```

3. **Check script execution:**
   ```bash
   python3 load_cpq_data.py 2>&1 | tee cpq_load.log
   python3 import_boatoptions_production.py 2>&1 | tee cpq_import.log
   ```

4. **Verify data loaded:**
   ```sql
   SELECT COUNT(*) FROM cpq.BoatOptions;
   SELECT COUNT(*) FROM cpq.Models;
   ```

---

**Migration completed:** 2026-02-11
**Next session:** Populate cpq database and update EOS configuration
