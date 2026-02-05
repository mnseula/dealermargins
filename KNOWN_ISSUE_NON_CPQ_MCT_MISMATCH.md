# KNOWN ISSUE: Non-CPQ Boat MCT Mismatch

**Status:** Known issue - team is aware
**Date Documented:** 2026-02-05
**Impact:** Non-CPQ boat pricing calculations may be incorrect

---

## Problem Summary

Calculate2021.js expects specific MCTDesc values, but non-CPQ boats from the ERP system have different MCTDesc values, causing margin misapplication.

---

## The Mismatch

### What Calculate2021.js Expects:

```javascript
// Line 49 - Base boat check
if (mct === 'PONTOONS') {
    // Apply base boat margin (27%)
}

// Line 198 - Engine check
if (mct === 'ENGINES' || mct === 'ENGINES I/O') {
    // Apply engine margin (27%)
}

// Line 256 - Pre-rig check
if (mct === 'PRE-RIG') {
    // Apply options margin (27%)
}

// Line 411 - Everything else (accessories)
else if (mct !== 'ENGINES' && mct !== 'ENGINES I/O' && mct != 'Lower Unit Eng' && mct != 'PRE-RIG') {
    // Apply options margin (27%)
}
```

### What Non-CPQ Boats Actually Have:

| Expected by JavaScript | Actual in Database | Match? |
|------------------------|-------------------|--------|
| `'PONTOONS'` | `'Pontoon Boats OB'` | ❌ NO |
| `'ENGINES'` | `'Engine'` | ❌ NO |
| `'ENGINES I/O'` | Not found | ❌ NO |
| `'PRE-RIG'` | `'Prerig'` | ❌ NO |
| N/A | `'Accessory'` | ⚠️ Different |

---

## Example: Order SO00930189

**Non-CPQ boat from ERP system:**

```
MCTDesc Distribution:
- Accessory: 19 items (various accessories)
- Pontoon Boats OB: 2 items (base boat)
- Engine: 1 item (Yamaha 150HP)
- Prerig: 3 items (pre-rig components)
- Discounts: Various discount types
```

**What Calculate2021.js Will Do:**

| Item | Amount | Has MCTDesc | JS Checks For | Match? | Applied Margin |
|------|--------|-------------|---------------|--------|----------------|
| Base Boat | $28,570 | Pontoon Boats OB | PONTOONS | ❌ | Options (27%) ❌ |
| Engine | $13,942 | Engine | ENGINES | ❌ | Options (27%) ❌ |
| Pre-rig | $1,495 | Prerig | PRE-RIG | ❌ | Options (27%) ✅ (by accident) |
| Accessories | $8,000+ | Accessory | (else clause) | ✅ | Options (27%) ✅ |

**Impact:**
- Base boat gets **options margin instead of base boat margin**
- Engine gets **options margin instead of engine margin**
- Pre-rig happens to get correct margin (by falling through to else clause)

**Net Result:** With all margins at 27%, the final price might be correct by coincidence, but the logic is broken.

---

## Root Cause

**Two Different Data Sources:**

1. **CPQ Boats (New):**
   - MCTDesc set by our classification logic in import query
   - Uses expected values: "PONTOONS", "PRE-RIG", "ACCESSORIES", etc.
   - ✅ Matches Calculate2021.js expectations

2. **Non-CPQ Boats (Legacy):**
   - MCTDesc comes from `prodcode_mst.description` in ERP
   - Uses ERP values: "Pontoon Boats OB", "Engine", "Prerig", etc.
   - ❌ Does NOT match Calculate2021.js expectations

---

## Why This Might Not Be Noticed

**Reason:** All margins are currently 27%

```sql
-- From DealerMargins table
Q_BASE_BOAT: 27.00   (baseboatmargin = 0.73)
Q_ENGINE: 27.00      (enginemargin = 0.73)
Q_OPTIONS: 27.00     (optionmargin = 0.73)
```

**Result:**
- Wrong margin type applied, but same percentage
- Final prices might be correct by coincidence
- Issue will become critical if margins diverge (e.g., base boat 27%, engine 10%, options 20%)

---

## Potential Solutions

### Option 1: Normalize MCTDesc in Import Query (Recommended)

**Modify Part 1 of import_boatoptions_test.py:**

```python
# Line 110: Replace this
pcm.description AS [MCTDesc],

# With this normalized version
CASE
    WHEN pcm.description LIKE '%Pontoon%' THEN 'PONTOONS'
    WHEN pcm.description LIKE '%Engine%' AND pcm.description NOT LIKE '%Lower%' THEN 'ENGINES'
    WHEN pcm.description LIKE '%Prerig%' OR pcm.description = 'Prerig' THEN 'PRE-RIG'
    WHEN pcm.description LIKE '%Lower Unit%' THEN 'Lower Unit Eng'
    WHEN pcm.description LIKE '%Accessory%' THEN 'ACCESSORIES'
    ELSE pcm.description
END AS [MCTDesc],
```

**Pros:**
- ✅ Fixes at data source
- ✅ No JavaScript changes needed
- ✅ Backward compatible

**Cons:**
- ❌ Must maintain mapping logic
- ❌ Might miss edge cases

---

### Option 2: Update Calculate2021.js to Accept Both Formats

**Modify Calculate2021.js:**

```javascript
// Line 49: Make it flexible
if (mct === 'PONTOONS' || mct === 'Pontoon Boats OB' || mct === 'Pontoon Boats' || mct === 'Pontoon Boats IO') {
    // Base boat logic
}

// Line 198: Make it flexible
if (mct === 'ENGINES' || mct === 'ENGINES I/O' || mct === 'Engine' || mct === 'Engine IO') {
    // Engine logic
}

// Line 256: Make it flexible
if (mct === 'PRE-RIG' || mct === 'Prerig') {
    // Pre-rig logic
}
```

**Pros:**
- ✅ Handles both formats
- ✅ More robust

**Cons:**
- ❌ Changes JavaScript (risky)
- ❌ Might affect CPQ boats
- ❌ Must test thoroughly

---

### Option 3: Create Mapping Table

**Add MCT mapping table in MySQL:**

```sql
CREATE TABLE MCTMapping (
    source_mct_desc VARCHAR(50) PRIMARY KEY,
    standard_mct_desc VARCHAR(50) NOT NULL,
    mct_code VARCHAR(10)
);

INSERT INTO MCTMapping VALUES
    ('Pontoon Boats OB', 'PONTOONS', 'BOA'),
    ('Pontoon Boats', 'PONTOONS', 'BOA'),
    ('Engine', 'ENGINES', 'ENG'),
    ('Engine IO', 'ENGINES I/O', 'EIO'),
    ('Prerig', 'PRE-RIG', 'PRE'),
    ('Accessory', 'ACCESSORIES', 'ACC');
```

**Join in import query:**
```sql
LEFT JOIN MCTMapping mm ON pcm.description = mm.source_mct_desc
COALESCE(mm.standard_mct_desc, pcm.description) AS [MCTDesc]
```

**Pros:**
- ✅ Clean, maintainable
- ✅ Easy to add new mappings
- ✅ Centralized logic

**Cons:**
- ❌ Additional table to maintain
- ❌ More complex query

---

## Current Workaround

**None.** Non-CPQ boats currently calculate with potentially incorrect margin types.

**Impact:** Minimal if all margins are equal (27%), but will become critical if margins diverge.

---

## Testing After Fix

### Verify MCTDesc Values:
```sql
SELECT
    MCTDesc,
    COUNT(*) as count,
    SUM(ExtSalesAmount) as total_amount
FROM BoatOptions26
WHERE ERP_OrderNo = 'SO00930189'
GROUP BY MCTDesc
ORDER BY total_amount DESC;
```

**Expected After Fix:**
```
PONTOONS          2 items    $28,570
ENGINES           1 item     $13,942
PRE-RIG           3 items    $1,495
ACCESSORIES      19 items    $8,000+
```

### Test Calculate2021.js:
1. Load non-CPQ boat (SO00930189)
2. Run Calculate2021.js
3. Verify:
   - Base boat gets `baseboatmargin`
   - Engine gets `enginemargin`
   - Pre-rig gets `optionmargin`
   - Accessories get `optionmargin`

---

## Related Files

- `Calculate2021.js` - Pricing calculation with MCT checks
- `import_boatoptions_test.py` - Import script Part 1 (non-CPQ)
- `packagePricing.js` - Boat data loading with MCT filters
- `CPQ_MCT_CLASSIFICATION.md` - CPQ attribute classification (works correctly)

---

## Notes

- **Team is aware of this issue** (as of 2026-02-05)
- CPQ boats use correct MCTDesc values (our classification logic)
- Non-CPQ boats use ERP MCTDesc values (mismatched)
- Issue masked by uniform 27% margins across all types
- Will become critical if margin percentages diverge

---

## Decision Needed

Which solution to implement:
- [ ] Option 1: Normalize in import query (recommended)
- [ ] Option 2: Update Calculate2021.js
- [ ] Option 3: Create mapping table
- [ ] Leave as-is (known issue)

---

## Last Updated

2026-02-05 - Initial documentation of known issue
