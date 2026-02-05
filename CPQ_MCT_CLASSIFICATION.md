# CPQ Configuration Attribute MCT Classification

## Problem Statement

CPQ configuration attributes were all importing with `MCT = "BOA"` (boat), causing incorrect margin calculations because Calculate2021.js applies different margins based on MCT type:
- **PONTOONS** → Base boat margin (27%)
- **PRE-RIG** → Options margin (27%)
- **ACCESSORIES** → Options margin (27%)
- **STANDARD FEATURES** → Included (no additional margin)

Without proper classification, all CPQ items got base boat margin regardless of type.

---

## Solution: Attribute Name Classification

Added CASE logic in Part 2 of `import_boatoptions_test.py` to classify configuration attributes by their `attr_name`:

### Classification Rules:

#### 1. Base Boat → `BOA` / `PONTOONS`
**Criteria:** `attr_name = 'Base Boat'`
**Margin:** Base boat margin (Q_BASE_BOAT from DealerMargins)
**Example:**
```
ItemNo: "Base Boat"
ItemDesc1: "22SFC"
Price: $29,847.00
MCT: BOA
MCTDesc: PONTOONS
→ Gets 27% base boat margin
```

#### 2. Pre-Rig → `PRE` / `PRE-RIG`
**Criteria:**
- `attr_name LIKE '%Pre-Rig%'`
- `attr_name LIKE '%Rigging%'`
- `attr_name LIKE '%Pre Rig%'`

**Margin:** Options margin (Q_OPTIONS from DealerMargins)
**Examples:**
```
ItemNo: "Engine Rigging"
ItemDesc1: "Single Engine Rigging (50-115 HP)"
Price: $1,349.00
MCT: PRE
MCTDesc: PRE-RIG
→ Gets 27% options margin

ItemNo: "Yamaha Mechanical Pre-Rig"
ItemDesc1: "Yamaha Mechanical Pre-Rig"
Price: $1,435.00
MCT: PRE
MCTDesc: PRE-RIG
→ Gets 27% options margin
```

#### 3. Paid Accessories → `ACC` / `ACCESSORIES`
**Criteria:** `Uf_BENN_Cfg_Price > 0` (not Base Boat or Pre-Rig)
**Margin:** Options margin (Q_OPTIONS from DealerMargins)
**Examples:**
```
ItemNo: "Battery Switching"
ItemDesc1: "Single Battery Switch"
Price: $126.00
MCT: ACC
MCTDesc: ACCESSORIES
→ Gets 27% options margin

ItemNo: "Bimini Top"
ItemDesc1: "Straight Single Bimini"
Price: $850.00
MCT: ACC
MCTDesc: ACCESSORIES
→ Gets 27% options margin
```

#### 4. Standard Features → `STD` / `STANDARD FEATURES`
**Criteria:** `Uf_BENN_Cfg_Price = 0` (included/standard)
**Margin:** None (included in base boat price)
**Examples:**
```
ItemNo: "Canvas Color"
ItemDesc1: "Midnight Black Canvas"
Price: $0.00
MCT: STD
MCTDesc: STANDARD FEATURES
→ No additional margin (included)

ItemNo: "Cupholders"
ItemDesc1: "Black Cupholders"
Price: $0.00
MCT: STD
MCTDesc: STANDARD FEATURES
→ No additional margin (included)
```

---

## Implementation in SQL

### MCTDesc Classification (Line 175-182):
```sql
CASE
    WHEN attr_detail.attr_name = 'Base Boat' THEN 'PONTOONS'
    WHEN attr_detail.attr_name LIKE '%Pre-Rig%'
         OR attr_detail.attr_name LIKE '%Rigging%'
         OR attr_detail.attr_name LIKE '%Pre Rig%' THEN 'PRE-RIG'
    WHEN attr_detail.Uf_BENN_Cfg_Price > 0 THEN 'ACCESSORIES'
    ELSE 'STANDARD FEATURES'
END AS [MCTDesc]
```

### ItemMasterMCT Classification (Line 190-197):
```sql
CASE
    WHEN attr_detail.attr_name = 'Base Boat' THEN 'BOA'
    WHEN attr_detail.attr_name LIKE '%Pre-Rig%'
         OR attr_detail.attr_name LIKE '%Rigging%'
         OR attr_detail.attr_name LIKE '%Pre Rig%' THEN 'PRE'
    WHEN attr_detail.Uf_BENN_Cfg_Price > 0 THEN 'ACC'
    ELSE 'STD'
END AS [ItemMasterMCT]
```

---

## How Calculate2021.js Uses MCT Types

### Base Boat (PONTOONS):
```javascript
// Line 49, 180, 189, 401
if (mct === 'PONTOONS') {
    boatsp = (Number(dealercost) / baseboatmargin) * vol_disc + freight + prep;
    saleprice = Number((dealercost * vol_disc) / baseboatmargin) + freight + prep;
}
```

### Pre-Rig:
```javascript
// Line 256, 268, 277, 284
if (mct === 'PRE-RIG') {
    setValue('DLR2', 'PRERIG_FULL_W_MARGIN_SALE',
        Math.round(prerigonboatprice / optionmargin) * vol_disc);
    prerigsp = (Number(prerigincrement) / optionmargin) * vol_disc;
}
```

### Accessories:
```javascript
// Line 411, 421
else if (mct !== 'ENGINES' && mct !== 'ENGINES I/O' && mct != 'Lower Unit Eng' && mct != 'PRE-RIG') {
    if (dealercost > 0) {
        saleprice = (Number(dealercost / optionmargin) * vol_disc);
    }
}
```

---

## Complete Example: CPQ Boat Pricing

### Input Data (SO00936068):
```
Base Boat              $29,847.00  → PONTOONS
Engine Rigging         $1,349.00   → PRE-RIG
Yamaha Pre-Rig         $1,435.00   → PRE-RIG
Battery Switching      $126.00     → ACCESSORIES
Canvas Color           $0.00       → STANDARD FEATURES (45+ items)
```

### Dealer Margins (Q Series):
```sql
-- From warrantyparts.DealerMargins WHERE DealerID = '00333836'
Q_BASE_BOAT: 27.00   (baseboatmargin = 0.73)
Q_ENGINE: 27.00      (enginemargin = 0.73)
Q_OPTIONS: 27.00     (optionmargin = 0.73)
Q_VOL_DISC: 27.00    (vol_disc = 1.0)
Q_FREIGHT: 1200.00
Q_PREP: 800.00
```

### Price Calculations:

**1. Base Boat (PONTOONS):**
```
Dealer Cost: $29,847.00
Formula: (dealercost / baseboatmargin) * vol_disc + freight + prep
Sale Price: ($29,847 / 0.73) * 1.0 + $1,200 + $800
          = $40,888 + $1,200 + $800
          = $42,888
```

**2. Engine Rigging (PRE-RIG):**
```
Dealer Cost: $1,349.00
Formula: (dealercost / optionmargin) * vol_disc
Sale Price: ($1,349 / 0.73) * 1.0
          = $1,848
```

**3. Yamaha Pre-Rig (PRE-RIG):**
```
Dealer Cost: $1,435.00
Formula: (dealercost / optionmargin) * vol_disc
Sale Price: ($1,435 / 0.73) * 1.0
          = $1,966
```

**4. Battery Switching (ACCESSORIES):**
```
Dealer Cost: $126.00
Formula: (dealercost / optionmargin) * vol_disc
Sale Price: ($126 / 0.73) * 1.0
          = $173
```

**5. Standard Features (45 items @ $0):**
```
Dealer Cost: $0.00
Sale Price: $0.00 (included)
```

### Total Pricing:
```
Total Dealer Cost:  $32,757.00
Total Sale Price:   $46,875.00
Dealer Savings:     $14,118.00 (30.1%)
```

---

## Integration with Existing DealerMargins Table

### No Changes Required to DealerMargins
The existing 92-column wide format DealerMargins table works perfectly:

```sql
-- warrantyparts.DealerMargins structure (unchanged)
DealerID | Q_BASE_BOAT | Q_ENGINE | Q_OPTIONS | Q_VOL_DISC | Q_FREIGHT | Q_PREP | ...
00333836 | 27.00       | 27.00    | 27.00     | 27.00      | 1200.00   | 800.00 | ...
```

### How Margins Get Applied:

1. **Import Query** classifies CPQ attributes by MCT type
2. **BoatOptions26** stores classified data
3. **Calculate2021.js** reads MCT types and applies margins:
   ```javascript
   window.boatoptions = loadByListName('BoatOptions26', ...);
   // Gets margins from DealerMargins table or CPQ variables
   baseboatmargin = 0.73  // From Q_BASE_BOAT
   enginemargin = 0.73    // From Q_ENGINE
   optionmargin = 0.73    // From Q_OPTIONS
   ```
4. **Correct pricing** calculated based on MCT type

---

## Testing & Verification

### Before Fix (All BOA):
```
Base Boat        $29,847  BOA  PONTOONS           ✅ 27% base margin (correct by luck)
Engine Rigging   $1,349   BOA  PONTOONS           ❌ 27% base margin (should be options)
Yamaha Pre-Rig   $1,435   BOA  PONTOONS           ❌ 27% base margin (should be options)
Battery Switching $126    BOA  PONTOONS           ❌ 27% base margin (should be options)
```

### After Fix (Proper Classification):
```
Base Boat        $29,847  BOA  PONTOONS           ✅ 27% base margin
Engine Rigging   $1,349   PRE  PRE-RIG            ✅ 27% options margin
Yamaha Pre-Rig   $1,435   PRE  PRE-RIG            ✅ 27% options margin
Battery Switching $126    ACC  ACCESSORIES        ✅ 27% options margin
Standard items   $0       STD  STANDARD FEATURES  ✅ Included (no margin)
```

### Verification Query:
```sql
-- Run after re-import to verify MCT classification
SELECT
    ItemNo,
    ItemDesc1,
    ExtSalesAmount,
    ItemMasterMCT,
    MCTDesc
FROM warrantyparts_boatoptions_test.BoatOptions26
WHERE ERP_OrderNo = 'SO00936068'
ORDER BY ExtSalesAmount DESC;
```

**Expected Results:**
- 1 PONTOONS (Base Boat)
- 2+ PRE-RIG (rigging items)
- Several ACC (paid accessories)
- Many STD (standard features at $0)

---

## Impact on Existing System

### ✅ Minimal Changes (As Requested):
1. **DealerMargins table:** No changes (keep 92-column format)
2. **Calculate2021.js:** No changes (existing logic works)
3. **packagePricing.js:** No changes (existing logic works)
4. **SQL procedures:** No changes (if using old table)

### ✅ Only Changed:
- `import_boatoptions_test.py` Part 2 query (MCT classification logic)

### ✅ Benefits:
- Correct margin application for CPQ boats
- Works with existing infrastructure
- No JavaScript changes required
- No margin table restructuring
- Backward compatible with non-CPQ boats

---

## Future Enhancements (Optional)

### 1. Engine Classification
If CPQ starts including engine items as configuration attributes:
```sql
WHEN attr_detail.attr_name LIKE '%Engine%'
     AND attr_detail.attr_name NOT LIKE '%Rigging%' THEN 'ENG'
```

### 2. Special Categories
Add classification for specific accessory types:
```sql
WHEN attr_detail.attr_name LIKE '%Stereo%'
     OR attr_detail.attr_name LIKE '%Audio%' THEN 'AUD'  -- Audio accessories
WHEN attr_detail.attr_name LIKE '%Cover%' THEN 'CVR'     -- Covers
```

### 3. Price Threshold
Adjust threshold for "paid" vs "standard":
```sql
WHEN attr_detail.Uf_BENN_Cfg_Price > 50 THEN 'ACC'  -- Only items > $50
```

---

## Related Files

- `import_boatoptions_test.py` - Import script with MCT classification
- `Calculate2021.js` - Pricing calculation logic
- `DATABASE_ARCHITECTURE.md` - Complete system architecture
- `PRICING_AND_MARGINS_EXPLAINED.md` - Pricing formulas and sources

---

## Last Updated
2026-02-05 - Initial MCT classification implementation
