# JavaScript Serial Number Query Updates

**Purpose:** Update JavaScript queries to use new BoatIdentifier and EngineIdentifier columns for CPQ compatibility

---

## Overview

**Problem:** CPQ boats don't have traditional `BoatItemNo` and `EngineItemNo` values.

**Solution:** Use computed `BoatIdentifier` and `EngineIdentifier` columns that fallback to descriptive names.

---

## Database Changes

### 1. Create Views (Run SQL script)

```bash
mysql -h ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com \
      -u awsmaster -p \
      warrantyparts_test < create_serial_views.sql
```

This creates:
- `SerialNumberMasterView` with `BoatIdentifier` column
- `EngineSerialNoMasterView` with `EngineIdentifier` column

---

## JavaScript Changes

### Query 1: SEL_ONE_SER_NO_MST (Boat Query)

**Location:** Wherever this query is defined (likely in a query definitions file or inline)

**Old Query:**
```sql
SELECT
    *
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = @PARAM1;
```

**New Query:**
```sql
SELECT
    *,
    COALESCE(
        NULLIF(BoatItemNo, ''),
        CONCAT(IFNULL(Series, ''), ' - ', IFNULL(BoatDesc1, ''))
    ) AS BoatIdentifier
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = @PARAM1;
```

**Alternative (Use View):**
```sql
SELECT
    *
FROM warrantyparts.SerialNumberMasterView
WHERE Boat_SerialNo = @PARAM1;
```

**JavaScript Change:**
```javascript
// OLD:
var boatItemNo = result[0].BoatItemNo;  // Can be empty for CPQ boats ❌

// NEW:
var boatItemNo = result[0].BoatIdentifier;  // Always populated ✅
```

---

### Query 2: SEL_ONE_ENG_SER_NO_MST (Engine Query)

**Location:** Wherever this query is defined

**Old Query:**
```sql
SELECT
    *
FROM warrantyparts.EngineSerialNoMaster
WHERE Boat_SerialNo = @PARAM1
  AND (OrigOrderType = 'C' OR OrigOrderType = 'I' OR OrigOrderType = 'O')
  AND Active > 0;
```

**New Query:**
```sql
SELECT
    *,
    COALESCE(
        NULLIF(EngineItemNo, ''),
        CONCAT(IFNULL(EngineBrand, ''), ' - ', IFNULL(EngineDesc1, ''))
    ) AS EngineIdentifier
FROM warrantyparts.EngineSerialNoMaster
WHERE Boat_SerialNo = @PARAM1
  AND (OrigOrderType = 'C' OR OrigOrderType = 'I' OR OrigOrderType = 'O')
  AND Active > 0;
```

**Alternative (Use View):**
```sql
SELECT
    *
FROM warrantyparts.EngineSerialNoMasterView
WHERE Boat_SerialNo = @PARAM1
  AND (OrigOrderType = 'C' OR OrigOrderType = 'I' OR OrigOrderType = 'O')
  AND Active > 0;
```

**JavaScript Change:**
```javascript
// OLD:
var engineItemNo = result[0].EngineItemNo;  // Can be empty for CPQ engines ❌

// NEW:
var engineItemNo = result[0].EngineIdentifier;  // Always populated ✅
```

---

## Expected Results

### Traditional Boats (Have ItemNo)

**Boat:**
```
BoatItemNo = "20SVSRSR"
BoatIdentifier = "20SVSRSR"  ✓ (uses ItemNo)
```

**Engine:**
```
EngineItemNo = "115ELPT4EFCT"
EngineIdentifier = "115ELPT4EFCT"  ✓ (uses ItemNo)
```

### CPQ Boats (No ItemNo)

**Boat:**
```
BoatItemNo = NULL or ''
Series = "SV"
BoatDesc1 = "20 S VALUE STERN RADIUS"
BoatIdentifier = "SV - 20 S VALUE STERN RADIUS"  ✓ (fallback)
```

**Engine:**
```
EngineItemNo = NULL or ''
EngineBrand = "MERCURY ENGINES"
EngineDesc1 = "MERC 115 HP 4S CT EFI 20 IN"
EngineIdentifier = "MERCURY ENGINES - MERC 115 HP 4S CT EFI 20 IN"  ✓ (fallback)
```

---

## Implementation Options

### Option A: Modify Base Tables (ALTER TABLE)

**Pros:**
- No query changes needed (just JavaScript variable)
- Transparent to all queries

**Cons:**
- Modifies production tables
- Harder to rollback
- Computed column recalculates on every row access

```sql
ALTER TABLE SerialNumberMaster
ADD COLUMN BoatIdentifier VARCHAR(300) GENERATED ALWAYS AS (
    COALESCE(
        NULLIF(BoatItemNo, ''),
        CONCAT(IFNULL(Series, ''), ' - ', IFNULL(BoatDesc1, ''))
    )
) STORED;

ALTER TABLE EngineSerialNoMaster
ADD COLUMN EngineIdentifier VARCHAR(300) GENERATED ALWAYS AS (
    COALESCE(
        NULLIF(EngineItemNo, ''),
        CONCAT(IFNULL(EngineBrand, ''), ' - ', IFNULL(EngineDesc1, ''))
    )
) STORED;
```

### Option B: Create Views (RECOMMENDED)

**Pros:**
- Doesn't modify base tables
- Easy to rollback (just DROP VIEW)
- Can switch between view and base table easily
- Same result as computed columns

**Cons:**
- Need to update query to use view name OR add column in SELECT

```sql
-- Already provided in create_serial_views.sql
CREATE VIEW SerialNumberMasterView AS ...
CREATE VIEW EngineSerialNoMasterView AS ...
```

### Option C: Add Column in SELECT (NO TABLE CHANGES)

**Pros:**
- Zero database changes
- Works immediately

**Cons:**
- Need to update every query that uses these tables
- More JavaScript/query changes

```sql
-- Just add the column in each SELECT
SELECT
    *,
    COALESCE(NULLIF(BoatItemNo, ''), CONCAT(...)) AS BoatIdentifier
FROM SerialNumberMaster
WHERE ...
```

---

## Recommendation

**Use Option B (Views)** for TEST environment, then:

1. **Test thoroughly** with both traditional and CPQ boats
2. **Validate JavaScript** works with BoatIdentifier/EngineIdentifier
3. **Deploy to production** once validated

**Then consider Option A (Computed Columns)** for production if views perform poorly.

---

## Testing Checklist

- [ ] Create views in TEST database
- [ ] Update JavaScript queries to use BoatIdentifier/EngineIdentifier
- [ ] Test with traditional boat (has ItemNo) - should show ItemNo
- [ ] Test with CPQ boat (no ItemNo) - should show "Series - Desc"
- [ ] Verify JavaScript logic works with both formats
- [ ] Check performance (views vs direct table access)
- [ ] Deploy to PRODUCTION when validated

---

## Files

- `create_serial_views.sql` - SQL script to create views
- This document - JavaScript change instructions
