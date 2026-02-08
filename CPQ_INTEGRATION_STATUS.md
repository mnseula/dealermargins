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

### JavaScript Fixes
- ✅ **packagePricing.js** - CPQ boat detection and data loading
  - Filters out "Base Boat" records
  - Detects CPQ boats via year code fallback (two === '0')
  - Sets `window.isCPQBoat = true`
  - CPQ fallback for SERIES extraction

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
- **print.js** (commits: f04d90a, 060dd5f) - CPQ boat support
- **packagePricing.js** (previous commits) - CPQ detection
- **Emergency rollback**: old_print.js, old_packagePricing.js

## 🔄 Next Steps

1. ✅ ~~Create automated sync script (sync_cpq_to_eos.py)~~ COMPLETED
2. ✅ ~~Add MSRP and configuration metadata to BoatOptions ETL~~ COMPLETED
3. Determine default performance package logic (for boat_specs single record)
4. Test with multiple CPQ boat models (beyond 23ML)
5. Run sync script on production: `python3 sync_cpq_to_eos.py`
6. Verify JavaScript queries work with synced data
7. Test legacy boats still work correctly
8. Create production deployment plan
