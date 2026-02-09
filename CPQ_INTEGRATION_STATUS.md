# CPQ Integration Status - Window Stickers

## ✅ WORKING (as of 2026-02-08)

### Data Loading
- ✅ CPQ API data loads to `warrantyparts_test` database via `load_cpq_data.py`
  - Models (265 CPQ boats)
  - StandardFeatures (2,475 unique features)
  - ModelStandardFeatures (mappings)
  - ModelPerformance (1,073 performance package specs)
  - PerformancePackages
  - ModelPricing
  - Series
  - Dealers
  - DealerMargins

### Data Synchronization to Eos Database
- ✅ **Automated sync script created**: `sync_cpq_to_eos.py`
  - Transforms normalized CPQ data (warrantyparts_test) → flattened tables (Eos)
  - Syncs: Models → boat_specs (89 records for 2025)
  - Syncs: ModelPerformance → perf_pkg_spec (377 packages with sequential PKG_ID)
  - Syncs: StandardFeatures → standards_list (2,475 features)
  - Syncs: ModelStandardFeatures → standards_matrix_2025 (5,029 mappings)
  - Uses INSERT...ON DUPLICATE KEY UPDATE for upserts
  - Run with: `python3 sync_cpq_to_eos.py` or `--dry-run` to preview

### ETL Script Updates
- ✅ **import_boatoptions_test.py** - MSSQL query updated with 6 new fields
  - Added MSRP (retail price) from `Uf_BENN_Cfg_MSRP`
  - Added configuration metadata: CfgName, CfgPage, CfgScreen, CfgValue, CfgAttrType
  - Part 2 (CPQ items): Extracts from cfg_attr_mst table
  - Part 1 (legacy items): Sets as NULL (no CPQ configuration data)
  - Enables complete pricing transparency (dealer cost + MSRP)

- ✅ **import_boatoptions_production.py** - Production ETL script
  - Targets `warrantyparts` database (not test)
  - Added LTRIM(RTRIM()) to InvoiceNo field to fix spacing issues
  - Fixed duplicate data problem from ERP inconsistent invoice number spacing
  - Successfully loads CPQ boat orders with MSRP data to production
  - Commit: 36518b9 (TRIM fix), dc8f242 (initial production script)

### JavaScript Fixes
- ✅ **packagePricing.js** - CPQ boat detection and data loading
  - Filters out "Base Boat" records
  - Detects CPQ boats via year code fallback (two === '0')
  - Sets `window.isCPQBoat = true`
  - CPQ fallback for SERIES extraction
  - **MSRP Fallback Logic**: Uses real MSRP if present, falls back to ExtSalesAmount for legacy boats
    - CPQ boats: Display MSRP (retail price)
    - Legacy boats: Display ExtSalesAmount (dealer cost)
    - Commit: 7d426ac

- ✅ **print.js** - Window sticker generation
  - Uses `window.realmodel` for CPQ boats instead of BOAT_INFO
  - Handles missing boat_specs gracefully
  - Initializes prfPkgs array to prevent errors
  - Uses OPT_NAME for CPQ standard features (when STANDARD lookup fails)
  - Handles missing ENG_CONFIG_ID and FUEL_TYPE_ID

### Window Sticker Display
- ✅ Boat Information section displays:
  - LOA (25'-3" for 23ML)
  - BEAM (8'-6" for 23ML)
  - PONT_DIAM/Tube Height (30.8" for 23ML)
  - FUEL_CAP (25 Gal. - 40 Gal. for 23ML)

- ✅ Standard Features section displays:
  - Console Features (11 for 23ML)
  - Exterior Features (17 for 23ML)
  - Interior Features (18 for 23ML)
  - Warranty (2 for 23ML)
  - Feature descriptions showing correctly

- ✅ No JavaScript errors

### MSRP Data Verification (Test Boat: ETWTEST26)
- ✅ **4 items with MSRP data loaded**:
  - Base Boat - 23ML: MSRP $58,171.00 (dealer cost $41,131.00)
  - Battery Switch: MSRP $747.00 (dealer cost $528.00)
  - Power Hydraulic Steering: MSRP $5,046.00 (dealer cost $3,568.00)
  - Yamaha Mechanical Pre-Rig: MSRP $2,387.00 (dealer cost $1,688.00)
- ✅ Duplicate invoice number issue resolved (cleaned old rows with leading spaces)
- ✅ Production database (warrantyparts.BoatOptions26) now has clean MSRP data

### Calculate2021.js MSRP Fix (2026-02-08)
- ✅ **ROOT CAUSE IDENTIFIED**: Calculate2021.js was calculating MSRP from dealer cost instead of using real MSRP from database
- ✅ **FIXED**: Modified to check `boatoptions[i].MSRP` first
  - If MSRP exists and > 0 (CPQ boat): Use real MSRP directly
  - If not (legacy boat): Fall back to calculating from dealer cost using margins
- ✅ **Applied to all calculation points**:
  - PONTOONS (base boat pricing)
  - Options (accessories, batteries, steering, etc.)
  - Discounts (value series discounts)
  - Engines (engine increments)
  - Pre-rig (pre-rig increments)
  - Tube upgrades (performance packages)
- ✅ **Backup created**: old_calculate.js (original Calculate function preserved)
- ✅ **Commit**: ced0b15

### packagePricing.js Column Swap Fix (2026-02-08) ✅ FIXED
- ✅ **ROOT CAUSE IDENTIFIED**: loadByListName('BoatOptions26') query had only 20 columns
  - Query stopped at ExtSalesAmount, didn't include MSRP or CPQ columns (CfgName, etc.)
  - MSRP column was added to table but not to the SELECT statement in list definition
  - loadByListName returned incomplete data, causing fallback to set MSRP = dealer cost
- ✅ **SOLUTION**: Updated BoatOptions26 list query definition in EOS
  - Added 11 new columns: MSRP, CfgName, CfgPage, CfgScreen, CfgValue, CfgAttrType, order_date, external_confirmation_ref, ConfigID, ValueText, C_Series
  - Query now returns all 31 columns from BoatOptions26 table
  - Created old_loadlistbyname26.sql (backup) and new_loadlistbyname26.sql (updated query)
- ✅ **VERIFIED WORKING**: MSRP now displays correctly on window stickers
  - ETWTEST26: MSRP = $107,562 (retail), Sale Price = $66,831 (dealer cost)
  - Swap logic works correctly - detects CPQ items via CfgName field
- ✅ **Commits**: 096fd9c (swap logic), de0d3ac (debug logging), 4831721 (query files)

## ⚠️ NEEDS PRODUCTION POLISH

### 1. ✅ Automated Data Sync Script ~~(HIGH PRIORITY)~~ COMPLETED
- ✅ **Created**: `sync_cpq_to_eos.py` script (commit: 4eda714)
- ✅ Transforms normalized CPQ data (warrantyparts_test) → flattened tables (Eos)
- ✅ Generates sequential PKG_ID per model using ROW_NUMBER()
- ✅ Supports dry-run mode for testing
- ✅ Data flow: `CPQ API → load_cpq_data.py → warrantyparts_test → sync_cpq_to_eos.py → Eos`

### 2. Performance Package Selection
- Currently using FIRST performance package for boat_specs
- Need to determine which package should be default
- User said "load all performance packages" - need to clarify production logic

### 3. Missing Boat Spec Fields
- PONT_LEN (pontoon length) - not provided by CPQ API
- DECK_LEN (deck length) - not provided by CPQ API
- Currently showing empty on window stickers

### 4. Production Testing
- [ ] Test multiple CPQ boat models (not just 23ML)
- [ ] Test with different performance packages
- [ ] Test legacy boats still work correctly
- [ ] Verify pricing calculations
- [ ] Check PDF formatting

## 📝 Key Files Modified

- **sync_cpq_to_eos.py** (commit: 4eda714) - NEW: Automated CPQ data sync script
- **import_boatoptions_test.py** (commit: 6c7a4f4) - Added 6 MSRP/config fields
- **import_boatoptions_production.py** (commits: 36518b9, dc8f242) - NEW: Production ETL with TRIM fix
- **Calculate2021.js** (commit: ced0b15) - Use real MSRP from CPQ instead of calculating from dealer cost
- **print.js** (commits: f04d90a, 060dd5f) - CPQ boat support
- **packagePricing.js** (commit: 7d426ac) - MSRP fallback logic
- **Emergency rollback**: old_print.js, old_packagePricing.js, old_calculate.js

## 🔄 Next Steps

1. ✅ ~~Create automated sync script (sync_cpq_to_eos.py)~~ COMPLETED
2. ✅ ~~Add MSRP and configuration metadata to BoatOptions ETL~~ COMPLETED
3. ✅ ~~Create production ETL script with TRIM fix~~ COMPLETED
4. ✅ ~~Clean duplicate invoice data from production database~~ COMPLETED
5. ✅ ~~Fix Calculate2021.js to use real MSRP instead of calculating~~ COMPLETED
6. ✅ ~~Fix loadByListName('BoatOptions26') query to include MSRP column~~ COMPLETED
7. ✅ ~~TEST WINDOW STICKER - Verify MSRP displays correctly for ETWTEST26~~ COMPLETED
   - MSRP showing correct retail prices ($107,562)
   - Sale Price showing correct dealer cost ($66,831)
   - Right-hand side (RHS) pricing section COMPLETE ✅
8. **🎨 LEFT-HAND SIDE (LHS)** - Boat specs and standard features
   - Verify boat specifications display (LOA, BEAM, etc.)
   - Verify standard features list correctly
   - Test with multiple CPQ boat models (beyond 23ML)
9. Determine default performance package logic (for boat_specs single record)
10. Run sync script on production: `python3 sync_cpq_to_eos.py`
11. Verify JavaScript queries work with synced data
12. Test legacy boats still work correctly (ensure margin calculations still work)
13. Create production deployment plan
