# Modified Queries for JavaScript (Future-Proof)

**Purpose:** Simple modifications to the two queries used in JavaScript to handle CPQ boats without item numbers.

---

## Query 1: SEL_ONE_SER_NO_MST (Boat Query)

### Original:
```sql
SELECT *
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = @PARAM1
```

### Modified (Future-Proof):
```sql
SELECT
    *,
    COALESCE(NULLIF(BoatItemNo, ''), CONCAT(Series, ' - ', BoatDesc1)) as BoatIdentifier
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = @PARAM1;
```

**What Changed:**
- Added `BoatIdentifier` column (computed)
- All original columns still returned via `*`
- No changes to WHERE clause

**Returns:**
- Current boats: `BoatIdentifier = "20SVSRSR"` (uses ItemNo)
- Future CPQ boats: `BoatIdentifier = "SV - 20 S VALUE STERN RADIUS"` (uses description)

---

## Query 2: SEL_ONE_ENG_SER_NO_MST (Engine Query)

### Original:
```sql
SELECT *
FROM warrantyparts.EngineSerialNoMaster
WHERE Boat_SerialNo = @PARAM1
  AND (OrigOrderType = 'C' OR OrigOrderType = 'I' OR OrigOrderType = 'O')
  AND Active > 0
```

### Modified (Future-Proof):
```sql
SELECT
    *,
    COALESCE(NULLIF(EngineItemNo, ''), CONCAT(EngineBrand, ' - ', EngineDesc1)) as EngineIdentifier
FROM warrantyparts.EngineSerialNoMaster
WHERE Boat_SerialNo = @PARAM1
  AND (OrigOrderType = 'C' OR OrigOrderType = 'I' OR OrigOrderType = 'O')
  AND Active > 0;
```

**What Changed:**
- Added `EngineIdentifier` column (computed)
- All original columns still returned via `*`
- No changes to WHERE clause

**Returns:**
- Current boats: `EngineIdentifier = "115ELPT4EFCT"` (uses ItemNo)
- Future CPQ boats: `EngineIdentifier = "MERCURY ENGINES - MERC 115 HP 4S CT EFI 20 IN"` (uses description)

---

## JavaScript Changes

### OLD Code (Breaks when ItemNo is NULL):
```javascript
// Query 1
var boatItemNo = result[0].BoatItemNo;  // ❌ Will be NULL for CPQ boats

// Query 2
var engineItemNo = result[0].EngineItemNo;  // ❌ Will be NULL for CPQ boats
```

### NEW Code (Works with or without ItemNo):
```javascript
// Query 1 - Use new identifier
var boatItemNo = result[0].BoatIdentifier;  // ✓ Always populated

// Query 2 - Use new identifier
var engineItemNo = result[0].EngineIdentifier;  // ✓ Always populated
```

**Or for backward compatibility:**
```javascript
// Fallback to identifier if ItemNo is missing
var boatItemNo = result[0].BoatItemNo || result[0].BoatIdentifier;
var engineItemNo = result[0].EngineItemNo || result[0].EngineIdentifier;
```

---

## Test Results

### Test Boat: ETWP7154K324

**Query 1 Results:**
```
BoatItemNo:     20SVSRSR
BoatIdentifier: 20SVSRSR  ← Uses ItemNo (current boat)
```

**Query 2 Results:**
```
EngineItemNo:      115ELPT4EFCT
EngineIdentifier:  115ELPT4EFCT  ← Uses ItemNo (current boat)
```

**Simulated CPQ Boat (NULL ItemNo):**
```
BoatItemNo:     NULL
BoatIdentifier: SV - 20 S VALUE STERN RADIUS  ← Uses description ✓

EngineItemNo:      NULL
EngineIdentifier:  MERCURY ENGINES - MERC 115 HP 4S CT EFI 20 IN  ← Uses description ✓
```

---

## Benefits

✅ **Backward Compatible** - All original columns still returned
✅ **Forward Compatible** - Works when ItemNo is NULL
✅ **Minimal Changes** - Only adds one column to each query
✅ **Simple JavaScript Update** - Just use new identifier columns
✅ **No Breaking Changes** - Original columns unchanged

---

## Summary

**Only two changes needed:**

1. Add `BoatIdentifier` to boat query
2. Add `EngineIdentifier` to engine query

That's it! JavaScript can then use these new columns instead of ItemNo, and it will work with both current and future CPQ boats.
