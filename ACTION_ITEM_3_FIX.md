# Action Item 3: Fix Missing Pontoon Length, Deck Length, and Engine Configuration

## Problem
The window sticker was missing:
- **Pontoon Length**: Empty
- **Deck Length**: Empty
- **Engine Configuration**: Empty

## Root Cause
The Models API returns these fields in `customProperties`:
- `TubeLengthStr` (e.g., "19'-4\"")
- `TubeLengthNum` (e.g., 19.33)
- `DeckLengthStr` (e.g., "19'-6\"")
- `DeckLengthNum` (e.g., 19.5)
- `EngineConfiguration` (e.g., "Single Engine Gasoline Outboard")

But `load_cpq_data.py` was NOT extracting these fields from the API and the Models table was missing these columns.

## Solution Implemented

### 1. Added Database Columns
Created `add_model_length_fields.sql`:
```sql
ALTER TABLE Models
ADD COLUMN IF NOT EXISTS tube_length_str VARCHAR(20) AFTER loa_str,
ADD COLUMN IF NOT EXISTS tube_length_num DECIMAL(6,2) AFTER tube_length_str,
ADD COLUMN IF NOT EXISTS deck_length_str VARCHAR(20) AFTER tube_length_num,
ADD COLUMN IF NOT EXISTS deck_length_num DECIMAL(6,2) AFTER deck_length_str,
ADD COLUMN IF NOT EXISTS engine_configuration VARCHAR(100) AFTER twin_engine;
```

### 2. Updated Data Loader
Modified `load_cpq_data.py`:

**Extract from API (lines 121-143):**
```python
custom_props = item.get('customProperties', {})
models.append({
    # ... existing fields ...
    'tube_length_str': custom_props.get('TubeLengthStr', ''),
    'tube_length_num': custom_props.get('TubeLengthNum', 0),
    'deck_length_str': custom_props.get('DeckLengthStr', ''),
    'deck_length_num': custom_props.get('DeckLengthNum', 0),
    # ... existing fields ...
    'engine_configuration': custom_props.get('EngineConfiguration', '')
})
```

**Insert into Database (lines 173-212):**
- Added new columns to INSERT statement
- Added new fields to VALUES tuple
- Added new fields to ON DUPLICATE KEY UPDATE

### 3. Update EOS Queries

The SQL queries that fetch model data need to be updated to use these new fields:

**Current query** (showing in user's earlier message):
```sql
SELECT
    m.model_id,
    m.model_name,
    m.series_id,
    m.floorplan_desc,
    m.loa_str AS loa,
    m.beam_str AS beam,
    m.length_feet,
    m.seats,
    -- ... performance package fields ...
    COALESCE(
        m.engine_configuration,
        CASE
            WHEN m.twin_engine = 1 THEN 'Twin Outboard'
            ELSE 'Single Outboard'
        END
    ) AS engine_configuration
FROM cpq.Models m  -- ❌ WRONG DATABASE
```

**Updated query should be:**
```sql
SELECT
    m.model_id,
    m.model_name,
    m.series_id,
    m.floorplan_desc,
    m.loa_str AS loa,
    m.beam_str AS beam,
    m.tube_length_str AS pontoon_length,  -- ✅ NEW
    m.deck_length_str AS deck_length,     -- ✅ NEW
    m.length_feet,
    m.seats,
    mp.perf_package_id,
    pp.package_name,
    mp.person_capacity,
    mp.hull_weight,
    mp.max_hp,
    mp.no_of_tubes,
    mp.pontoon_gauge,
    mp.fuel_capacity,
    mp.tube_length_str AS pontoon_length,  -- Performance-specific (may override model)
    mp.deck_length_str AS deck_length,     -- Performance-specific (may override model)
    mp.tube_height,
    mp.pontoon_gauge AS pontoon_diameter,
    COALESCE(
        m.engine_configuration,
        CASE
            WHEN m.twin_engine = 1 THEN 'Twin Outboard'
            ELSE 'Single Outboard'
        END
    ) AS engine_configuration
FROM warrantyparts_test.Models m  -- ✅ CORRECT DATABASE
LEFT JOIN (
    SELECT CfgValue AS perf_package_id
    FROM warrantyparts_test.BoatOptions  -- ✅ CORRECT DATABASE (if table exists)
    WHERE BoatSerialNo = @PARAM3
      AND CfgName = 'perfPack'
    LIMIT 1
) boat_perf ON 1=1
LEFT JOIN warrantyparts_test.ModelPerformance mp  -- ✅ CORRECT DATABASE
    ON m.model_id = mp.model_id
    AND mp.year = @PARAM2
    AND mp.perf_package_id = boat_perf.perf_package_id
LEFT JOIN warrantyparts_test.PerformancePackages pp  -- ✅ CORRECT DATABASE
    ON mp.perf_package_id = pp.perf_package_id
WHERE m.model_id = @PARAM1
LIMIT 1;
```

## Steps to Apply Fix

### 1. Run Database Migration
```bash
# Connect to MySQL and run the migration
mysql -h ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com \
      -u awsmaster \
      -pVWvHG9vfG23g7gD \
      < add_model_length_fields.sql
```

### 2. Reload CPQ Data
```bash
# Run the updated data loader
python3 load_cpq_data.py
```

This will:
- Fetch models from API with the new fields
- Update the Models table with pontoon length, deck length, and engine configuration
- Preserve all existing data (ON DUPLICATE KEY UPDATE)

### 3. Update EOS SQL Queries
In the EOS system, update these queries to:
- Change `cpq.` to `warrantyparts_test.`
- Add `m.tube_length_str AS pontoon_length`
- Add `m.deck_length_str AS deck_length`
- Use `m.engine_configuration` (already in query with COALESCE)

### 4. Test
Reload boat CPQTEST26 (or ETWTEST26) and verify:
- ✅ Pontoon Length: Shows value (e.g., "25'-3\"")
- ✅ Deck Length: Shows value (e.g., "22'-6\"")
- ✅ Engine Configuration: Shows "Single Outboard" or "Twin Outboard"

## Expected Results

**Before:**
```
Pontoon Length:
Deck Length:
Engine Configuration:
```

**After:**
```
Pontoon Length: 25'-3"
Deck Length: 22'-6"
Engine Configuration: Single Outboard
```

## Files Modified
- `add_model_length_fields.sql` - Database migration
- `load_cpq_data.py` - Updated to extract new fields from API
- EOS SQL queries - Need to be updated to use `warrantyparts_test` and new columns

## Notes
- The Models API has these fields for ALL models
- Performance Data API does NOT have tube_length_str/deck_length_str (those are NULL)
- The window sticker should use the Models table values for pontoon/deck length
- Engine configuration can be derived from `twin_engine` flag if not set explicitly
