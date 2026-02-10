# Configure CPQ sStatements in EOS

## Problem
CPQ boats aren't loading LHS data (specs) and Standard Features because the sStatements don't exist in EOS.

## Solution
Configure these two sStatements in the EOS admin panel:

---

## 1. GET_CPQ_LHS_DATA

**Name:** `GET_CPQ_LHS_DATA`
**Type:** Query
**Parameters:** 3
- @PARAM1 = model_id (e.g., '23ML', '22SFC')
- @PARAM2 = year (e.g., 2025, 2022)
- @PARAM3 = hull_no (e.g., 'ETWINVTEST0122')

**SQL Query:**
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
    mp.perf_package_id,
    pp.package_name,
    mp.person_capacity,
    mp.hull_weight,
    mp.max_hp,
    mp.no_of_tubes,
    mp.pontoon_gauge,
    mp.fuel_capacity,
    mp.tube_length_str AS pontoon_length,
    mp.deck_length_str AS deck_length,
    mp.tube_height,
    mp.pontoon_gauge AS pontoon_diameter,
    -- Engine configuration: use field if available, otherwise derive from twin_engine flag
    COALESCE(
        m.engine_configuration,
        CASE
            WHEN m.twin_engine = 1 THEN 'Twin Outboard'
            ELSE 'Single Outboard'
        END
    ) AS engine_configuration
FROM warrantyparts_test.Models m
LEFT JOIN (
    -- Get the performance package ID from the boat's configuration
    -- BoatOptions26 is the catchall table for ALL CPQ boats (regardless of model year)
    SELECT CfgValue AS perf_package_id
    FROM warrantyparts.BoatOptions26
    WHERE BoatSerialNo = @PARAM3
      AND CfgName = 'perfPack'
    LIMIT 1
) boat_perf ON 1=1
LEFT JOIN warrantyparts_test.ModelPerformance mp
    ON m.model_id = mp.model_id
    AND mp.year = @PARAM2
    AND mp.perf_package_id = boat_perf.perf_package_id
LEFT JOIN warrantyparts_test.PerformancePackages pp
    ON mp.perf_package_id = pp.perf_package_id
WHERE m.model_id = @PARAM1
LIMIT 1;
```

**Note:** BoatOptions26 is the catchall table for ALL CPQ boats. All CPQ boats are imported to BoatOptions26 regardless of model year, so we only need to search that one table for the performance package configuration.

---

## 2. GET_CPQ_STANDARD_FEATURES

**Name:** `GET_CPQ_STANDARD_FEATURES`
**Type:** Query
**Parameters:** 2
- @PARAM1 = model_id (e.g., '23ML', '22SFC')
- @PARAM2 = year (e.g., 2025, 2022)

**SQL Query:**
```sql
SELECT
    sf.feature_id,
    sf.feature_code,
    sf.area,
    sf.description,
    sf.sort_order
FROM warrantyparts_test.StandardFeatures sf
JOIN warrantyparts_test.ModelStandardFeatures msf
    ON sf.feature_id = msf.feature_id
WHERE msf.model_id = @PARAM1
  AND msf.year = @PARAM2
  AND sf.active = 1
ORDER BY
    CASE sf.area
        WHEN 'Interior Features' THEN 1
        WHEN 'Exterior Features' THEN 2
        WHEN 'Console Features' THEN 3
        WHEN 'Warranty' THEN 4
        ELSE 5
    END,
    sf.sort_order;
```

**No changes needed** - this query is already correct.

---

## 3. JavaScript Fix Required

**File:** `getunregisteredboats.js`
**Line:** ~219

**Current (WRONG):**
```javascript
var cpqYear = 2025; // Hardcoded!
```

**Fixed:**
```javascript
// Calculate actual year from serialYear
// serialYear 22 → 2022, 25 → 2025, etc.
var cpqYear = 2000 + parseInt(serialYear);
console.log('Calculated CPQ year:', cpqYear, 'from serialYear:', serialYear);
```

This ensures each boat queries with its correct year (2022 for ETWINVTEST0122, not 2025).

---

## Testing

After configuring both sStatements:

1. **Hard refresh browser** (Ctrl+Shift+R / Cmd+Shift+R)
2. **Load ETWINVTEST0122**
3. **Check console** for:
   ```
   ✅ SUCCESS: Got LHS data for model 22SFC hull ETWINVTEST0122
   ✅ SUCCESS: Got XX standard features for model 22SFC
   ```

## Prerequisites

The warrantyparts_test database must have data for:
- `Models` table (22SFC entry)
- `ModelPerformance` table (22SFC for 2022)
- `StandardFeatures` + `ModelStandardFeatures` (22SFC for 2022)

If that data doesn't exist, the queries will return empty results (not an error, just no data).
