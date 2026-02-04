# JavaScript CPQ Integration - Complete Data Flow & Required Changes

**Purpose:** Document the complete flow from MSSQL → MySQL → JavaScript and identify changes needed for CPQ orders

---

## Complete Data Flow

```
┌─────────────┐
│   MSSQL     │ Syteline ERP
│   (CSISTG)  │ - coitem_mst
│             │ - cfg_attr_mst (CPQ components)
│             │ - co_mst, serial_mst, etc.
└──────┬──────┘
       │
       │ Python Import Script
       │ (import_boatoptions_test.py)
       │ - UNION query (Part 1 + Part 2)
       │ - ROW_NUMBER() for unique LineSeqNo
       │
       ▼
┌─────────────┐
│    MySQL    │ RDS Database
│  (warrantyparts_boatoptions_test)
│             │
│  Tables:    │
│  - BoatOptions15-26
│  - BoatOptions11_14
│  - BoatOptions08_10
│  - etc.
└──────┬──────┘
       │
       │ Infor CPQ JavaScript
       │ - packagePricing.js
       │ - Calculate2021.js
       │
       ▼
┌─────────────┐
│  CPQ UI     │ Web Interface
│             │ - Window stickers
│             │ - Dealer quotes
│             │ - Pricing calculations
└─────────────┘
```

---

## The Two Critical JavaScript Queries

### Query 1: Load Boat Options (packagePricing.js - Line 35)

**Current Query (FOR MODEL YEAR 2015+):**

```javascript
window.boatoptions = loadByListName('BoatOptions' + serialYear,
    "WHERE ItemMasterMCT <> 'DIC'
    AND ItemMasterMCT <> 'DIF'
    AND ItemMasterMCT <> 'DIP'
    AND ItemMasterMCT <> 'DIR'
    AND ItemMasterMCT <> 'DIA'
    AND ItemMasterMCT <> 'DIW'
    AND ItemMasterMCT <> 'LOY'
    AND ItemMasterMCT <> 'PRD'
    AND ItemMasterMCT <> 'VOD'
    AND (ItemMasterMCT <> 'DIS' OR (ItemMasterMCT = 'DIS' AND ItemNo = 'NPPNPRICE16S'))
    AND ItemMasterMCT <> 'DIV'
    AND ItemMasterMCT <> 'DIW'
    AND (ItemMasterMCT <> 'ENZ' OR (ItemMasterMCT = 'ENZ' AND ItemDesc1 LIKE '%VALUE%'))
    AND ItemMasterMCT <> 'SHO'
    AND ItemMasterMCT <> 'GRO'
    AND ItemMasterMCT <> 'ZZZ'
    AND ItemMasterMCT <> 'FRE'
    AND ItemMasterMCT <> 'WAR'
    AND ItemMasterMCT <> 'DLR'
    AND ItemMasterMCT <> 'FRT'
    AND ItemMasterProdCat <> '111'
    AND (InvoiceNo = '" + snmInvoiceNo + "'
         OR (ERP_OrderNo = '" + engineERPNo + "'
             AND (MCTDesc = 'ENGINES'
                  OR MCTDesc = 'Engine'
                  OR MCTDesc = 'ENGINES IO'
                  OR ItemMasterMCT= 'ELU'
                  OR ItemMasterProdCatDesc = 'EngineLowerUnit')))
    AND BoatSerialNo= '" + serial + "'
    ORDER BY CASE `MCTDesc`
        WHEN 'PONTOONS' THEN 1
        WHEN 'Pontoon Boats OB' THEN 1
        WHEN 'Pontoon Boats IO' THEN 1
        WHEN 'Lower Unit Eng' THEN 2
        WHEN 'ENGINES' THEN 3
        WHEN 'Engine' THEN 3
        WHEN 'Engine IO' THEN 3
        WHEN 'PRE-RIG' THEN 4
        WHEN 'Prerig' THEN 4
        ELSE 5
    END, LineNo ASC"
);
```

**Location:** `packagePricing.js`, Line 35

**Problem for CPQ Orders:**
- Uses `BoatSerialNo` as primary filter
- CPQ orders have **empty BoatSerialNo**!
- Will return 0 rows for CPQ boats

### Query 2: Lookup Items in Options Matrix (Calculate2021.js - Line 373)

```javascript
itemOmmLine = $.grep(optionsMatrix, function (i) {
    return i.PART === itemno; // Uses ItemNo for lookup
});
```

**Location:** `Calculate2021.js`, Line 372-374

**Problem for CPQ Orders:**
- CPQ items use component IDs (e.g., "LADDER_21", "S_FURN_CAPT_STD")
- These may not exist in the options_matrix tables
- Fallback uses ItemDesc1 which should work

---

## Data Structure Comparison

### Traditional Orders (Pre-CPQ)

**MySQL BoatOptions Table:**
```
ERP_OrderNo | LineSeqNo | BoatSerialNo | ItemNo    | ItemDesc1           | ConfigID | ValueText
------------|-----------|--------------|-----------|---------------------|----------|----------
SO00935000  | 1         | ETWC4149F425 | 25QXFBWA  | 25 QX FASTBACK...  | NULL     | NULL
SO00935000  | 2         | ETWC4149F425 | YAMAHA200 | YAMAHA 200HP...    | NULL     | NULL
SO00935000  | 3         | ETWC4149F425 | 9012345   | BIMINI TOP...      | NULL     | NULL
```

**JavaScript Access:**
```javascript
// Loads by BoatSerialNo → Returns 3 rows
window.boatoptions = loadByListName('BoatOptions25',
    "WHERE BoatSerialNo = 'ETWC4149F425'");

// boatoptions[0].ItemNo = "25QXFBWA"
// boatoptions[1].ItemNo = "YAMAHA200"
// boatoptions[2].ItemNo = "9012345"
```

### CPQ Orders (New - 2025+)

**MySQL BoatOptions Table:**
```
ERP_OrderNo | LineSeqNo | BoatSerialNo | ItemNo              | ItemDesc1                  | ConfigID          | ValueText | WebOrderNo
------------|-----------|--------------|---------------------|----------------------------|-------------------|-----------|------------
SO00936047  | 1         | [EMPTY]      | LADDER_21           | LADDER 21 NON EXT DECK     | BENN...0043      | LADDER... | SOBHO00675
SO00936047  | 2         | [EMPTY]      | 168SLJ_FURN_SB_     | 168SLJ STBD BOW STANDARD   | BENN...0043      | 168SLJ... | SOBHO00675
SO00936047  | 3         | [EMPTY]      | S_FURN_CAPT_STD     | S-RECLINER STANDARD        | BENN...0043      | S-RECL... | SOBHO00675
... (46 total components)
```

**JavaScript Access (Current - BROKEN):**
```javascript
// Tries to load by BoatSerialNo → Returns 0 rows! (BoatSerialNo is empty)
window.boatoptions = loadByListName('BoatOptions26',
    "WHERE BoatSerialNo = '[EMPTY]'");

// Result: Empty array, no data!
```

---

## Required Changes

### Change #1: packagePricing.js - Line 35 (Primary Query)

**Current Line 35:**
```javascript
window.boatoptions = loadByListName('BoatOptions' + serialYear,
    "WHERE ItemMasterMCT <> 'DIC' ... AND BoatSerialNo= '" + serial + "' ORDER BY ...");
```

**NEW - Support Both Serial and WebOrderNo:**
```javascript
// NEW: Detect if this is a CPQ order (has WebOrderNo but no serial)
var isCPQOrder = (serial === '' || serial === null || serial === undefined) && webOrderNo;

if (isCPQOrder) {
    // CPQ Order: Query by WebOrderNo instead of BoatSerialNo
    window.boatoptions = loadByListName('BoatOptions' + serialYear,
        "WHERE ItemMasterMCT <> 'DIC'
        AND ItemMasterMCT <> 'DIF'
        AND ItemMasterMCT <> 'DIP'
        AND ItemMasterMCT <> 'DIR'
        AND ItemMasterMCT <> 'DIA'
        AND ItemMasterMCT <> 'DIW'
        AND ItemMasterMCT <> 'LOY'
        AND ItemMasterMCT <> 'PRD'
        AND ItemMasterMCT <> 'VOD'
        AND (ItemMasterMCT <> 'DIS' OR (ItemMasterMCT = 'DIS' AND ItemNo = 'NPPNPRICE16S'))
        AND ItemMasterMCT <> 'DIV'
        AND ItemMasterMCT <> 'DIW'
        AND (ItemMasterMCT <> 'ENZ' OR (ItemMasterMCT = 'ENZ' AND ItemDesc1 LIKE '%VALUE%'))
        AND ItemMasterMCT <> 'SHO'
        AND ItemMasterMCT <> 'GRO'
        AND ItemMasterMCT <> 'ZZZ'
        AND ItemMasterMCT <> 'FRE'
        AND ItemMasterMCT <> 'WAR'
        AND ItemMasterMCT <> 'DLR'
        AND ItemMasterMCT <> 'FRT'
        AND ItemMasterProdCat <> '111'
        AND WebOrderNo = '" + webOrderNo + "'
        AND ConfigID IS NOT NULL
        ORDER BY LineSeqNo ASC"
    );
} else {
    // Traditional Order: Query by BoatSerialNo (existing logic)
    window.boatoptions = loadByListName('BoatOptions' + serialYear,
        "WHERE ItemMasterMCT <> 'DIC'
        ... [keep existing filters] ...
        AND BoatSerialNo= '" + serial + "'
        ORDER BY CASE `MCTDesc` WHEN 'PONTOONS' THEN 1 ... END, LineNo ASC"
    );
}
```

**IMPORTANT:** You'll need to pass `webOrderNo` parameter to the function!

### Change #2: packagePricing.js - Line 13 (Function Parameters)

**Current Line 13:**
```javascript
window.loadPackagePricing = window.loadPackagePricing || function (serialYear, serial, snmInvoiceNo, engineERPNo) {
```

**NEW - Add webOrderNo parameter:**
```javascript
window.loadPackagePricing = window.loadPackagePricing || function (serialYear, serial, snmInvoiceNo, engineERPNo, webOrderNo) {
    console.log('Loading Variables');
    console.log('Serial:', serial);
    console.log('WebOrderNo:', webOrderNo); // NEW: Log CPQ order number
```

### Change #3: Calculate2021.js - Lines 39-40 (Item Display)

**Current Lines 39-40:**
```javascript
var itemNo = boatoptions[j].ItemNo; // Original numeric ItemNo
var displayItemNo = boatoptions[j].ItemDesc1 || itemNo; // Use ItemDesc1 for display, fallback to ItemNo
```

**This is CORRECT for CPQ!** ✅

The code already uses `ItemDesc1` for display, which works perfectly for CPQ component names like "LADDER 21 NON EXT DECK".

### Change #4: Calculate2021.js - Line 373 (Options Matrix Lookup)

**Current Line 373:**
```javascript
itemOmmLine = $.grep(optionsMatrix, function (i) {
    return i.PART === itemno; // Use original ItemNo for lookup
});
```

**NEW - Add fallback for CPQ components:**
```javascript
// Try original ItemNo first
itemOmmLine = $.grep(optionsMatrix, function (i) {
    return i.PART === itemno;
});

// If not found and this is a CPQ item (has ConfigID), try ItemDesc1
if (itemOmmLine.length === 0 && boatoptions[j].ConfigID) {
    itemOmmLine = $.grep(optionsMatrix, function (i) {
        return i.PART === displayItemNo || i.OPT_NAME === displayItemNo;
    });
}
```

---

## JavaScript Call Sites

### Where loadPackagePricing() is Called

You'll need to update all call sites to pass the new `webOrderNo` parameter:

**Find calls like:**
```javascript
loadPackagePricing(25, 'ETWC4149F425', 'INV12345', 'SO00935000');
```

**Update to:**
```javascript
// Traditional order (has serial)
loadPackagePricing(25, 'ETWC4149F425', 'INV12345', 'SO00935000', null);

// CPQ order (no serial, has webOrderNo)
loadPackagePricing(26, '', 'INV12345', 'SO00936047', 'SOBHO00675');
```

---

## Testing Strategy

### Test Case 1: Traditional Order (Pre-CPQ)
```javascript
// Input
serialYear: 25
serial: 'ETWC4149F425'
snmInvoiceNo: 'INV12345'
engineERPNo: 'SO00935000'
webOrderNo: null

// Expected
- Uses BoatSerialNo query
- Returns boat + engine + accessories
- All existing logic works
```

### Test Case 2: CPQ Order (2025+)
```javascript
// Input
serialYear: 26
serial: '' or null
snmInvoiceNo: 'INV12346'
engineERPNo: 'SO00936047'
webOrderNo: 'SOBHO00675'

// Expected
- Uses WebOrderNo query
- Returns 46 configured components
- All have ConfigID populated
- ItemNo = component IDs (LADDER_21, etc.)
- ItemDesc1 = component descriptions
```

### Test Case 3: Mixed Environment
```javascript
// Both order types should work simultaneously
// Traditional orders use serial
// CPQ orders use webOrderNo
```

---

## Summary of Required Changes

### File: packagePricing.js

| Line | Change | Description |
|------|--------|-------------|
| 13 | Add parameter | `function (..., webOrderNo)` |
| 35 | Add CPQ logic | `if (isCPQOrder) { query by WebOrderNo } else { query by BoatSerialNo }` |

### File: Calculate2021.js

| Line | Change | Description |
|------|--------|-------------|
| 39-40 | ✅ No change needed | Already uses ItemDesc1 for display |
| 373 | Add fallback | Try ItemDesc1 if ItemNo lookup fails for CPQ items |

### Call Sites (Various files)

| Location | Change | Description |
|----------|--------|-------------|
| All calls to loadPackagePricing() | Add 5th parameter | Pass webOrderNo for CPQ orders, null for traditional |

---

## Complete Updated Function

### packagePricing.js - Complete Updated Version (Lines 13-40)

```javascript
window.loadPackagePricing = window.loadPackagePricing || function (serialYear, serial, snmInvoiceNo, engineERPNo, webOrderNo) {
    console.log('Loading Variables');
    console.log('Serial Year:', serialYear);
    console.log('Serial:', serial);
    console.log('Invoice No:', snmInvoiceNo);
    console.log('Engine ERP No:', engineERPNo);
    console.log('Web Order No (CPQ):', webOrderNo);

    window.boatYear = serial ? serial.substring(serial.length - 2) : '';
    window.serialYear = serialYear;

    // Boat options - handle both traditional and CPQ orders
    if (serialYear > 4 && serialYear < 8) {
        window.boatoptions = loadByListName('boat_options_05_0', "WHERE BoatSerialNo = '" + serial + "'");
    }
    else if (serialYear > 7 && serialYear < 11) {
        window.boatoptions = loadByListName('boat_options_08_10', "WHERE BoatSerialNo = '" + serial + "'");
    }
    else if (serialYear > 10 && serialYear < 15) {
        window.boatoptions = loadByListName('boat_options11_14', "WHERE BoatSerialNo = '" + serial + "'");
    }
    else if (serialYear > 14) {
        // Modern boats (2015+) - Support both traditional and CPQ orders

        // Detect CPQ order (has webOrderNo, empty/null serial)
        var isCPQOrder = (!serial || serial === '') && webOrderNo;

        if (isCPQOrder) {
            console.log('CPQ ORDER DETECTED - Querying by WebOrderNo:', webOrderNo);

            // CPQ Order: Query by WebOrderNo and ConfigID
            window.boatoptions = loadByListName('BoatOptions' + serialYear,
                "WHERE ItemMasterMCT <> 'DIC' " +
                "AND ItemMasterMCT <> 'DIF' " +
                "AND ItemMasterMCT <> 'DIP' " +
                "AND ItemMasterMCT <> 'DIR' " +
                "AND ItemMasterMCT <> 'DIA' " +
                "AND ItemMasterMCT <> 'DIW' " +
                "AND ItemMasterMCT <> 'LOY' " +
                "AND ItemMasterMCT <> 'PRD' " +
                "AND ItemMasterMCT <> 'VOD' " +
                "AND (ItemMasterMCT <> 'DIS' OR (ItemMasterMCT = 'DIS' AND ItemNo = 'NPPNPRICE16S')) " +
                "AND ItemMasterMCT <> 'DIV' " +
                "AND (ItemMasterMCT <> 'ENZ' OR (ItemMasterMCT = 'ENZ' AND ItemDesc1 LIKE '%VALUE%')) " +
                "AND ItemMasterMCT <> 'SHO' " +
                "AND ItemMasterMCT <> 'GRO' " +
                "AND ItemMasterMCT <> 'ZZZ' " +
                "AND ItemMasterMCT <> 'FRE' " +
                "AND ItemMasterMCT <> 'WAR' " +
                "AND ItemMasterMCT <> 'DLR' " +
                "AND ItemMasterMCT <> 'FRT' " +
                "AND ItemMasterProdCat <> '111' " +
                "AND WebOrderNo = '" + webOrderNo + "' " +
                "AND ConfigID IS NOT NULL " +
                "ORDER BY LineSeqNo ASC"
            );

            console.log('CPQ components loaded:', window.boatoptions.length);
        }
        else {
            console.log('TRADITIONAL ORDER - Querying by BoatSerialNo:', serial);

            // Traditional Order: Query by BoatSerialNo (existing logic)
            window.boatoptions = loadByListName('BoatOptions' + serialYear,
                "WHERE ItemMasterMCT <> 'DIC' " +
                "AND ItemMasterMCT <> 'DIF' " +
                "AND ItemMasterMCT <> 'DIP' " +
                "AND ItemMasterMCT <> 'DIR' " +
                "AND ItemMasterMCT <> 'DIA' " +
                "AND ItemMasterMCT <> 'DIW' " +
                "AND ItemMasterMCT <> 'LOY' " +
                "AND ItemMasterMCT <> 'PRD' " +
                "AND ItemMasterMCT <> 'VOD' " +
                "AND (ItemMasterMCT <> 'DIS' OR (ItemMasterMCT = 'DIS' AND ItemNo = 'NPPNPRICE16S')) " +
                "AND ItemMasterMCT <> 'DIV' " +
                "AND (ItemMasterMCT <> 'ENZ' OR (ItemMasterMCT = 'ENZ' AND ItemDesc1 LIKE '%VALUE%')) " +
                "AND ItemMasterMCT <> 'SHO' " +
                "AND ItemMasterMCT <> 'GRO' " +
                "AND ItemMasterMCT <> 'ZZZ' " +
                "AND ItemMasterMCT <> 'FRE' " +
                "AND ItemMasterMCT <> 'WAR' " +
                "AND ItemMasterMCT <> 'DLR' " +
                "AND ItemMasterMCT <> 'FRT' " +
                "AND ItemMasterProdCat <> '111' " +
                "AND (InvoiceNo = '" + snmInvoiceNo + "' " +
                "     OR (ERP_OrderNo = '" + engineERPNo + "' " +
                "         AND (MCTDesc = 'ENGINES' " +
                "              OR MCTDesc = 'Engine' " +
                "              OR MCTDesc = 'ENGINES IO' " +
                "              OR ItemMasterMCT = 'ELU' " +
                "              OR ItemMasterProdCatDesc = 'EngineLowerUnit'))) " +
                "AND BoatSerialNo = '" + serial + "' " +
                "ORDER BY CASE `MCTDesc` " +
                "    WHEN 'PONTOONS' THEN 1 " +
                "    WHEN 'Pontoon Boats OB' THEN 1 " +
                "    WHEN 'Pontoon Boats IO' THEN 1 " +
                "    WHEN 'Lower Unit Eng' THEN 2 " +
                "    WHEN 'ENGINES' THEN 3 " +
                "    WHEN 'Engine' THEN 3 " +
                "    WHEN 'Engine IO' THEN 3 " +
                "    WHEN 'PRE-RIG' THEN 4 " +
                "    WHEN 'Prerig' THEN 4 " +
                "    ELSE 5 END, LineNo ASC"
            );

            console.log('Traditional boat options loaded:', window.boatoptions.length);
        }
    }

    // Rest of function continues...
    console.log("BEFORE fAILURE");
    window.productids = loadByListName('Product List');
    // ... (rest unchanged)
};
```

---

## Questions for Business Team

1. **WebOrderNo Availability:**
   - Is `WebOrderNo` available in the CPQ UI when displaying boat details?
   - Where do we get this value from (URL parameter, database lookup, etc.)?

2. **Serial Number Workflow:**
   - When do CPQ orders get assigned BoatSerialNo?
   - Should we update the query to use serial if available, webOrderNo if not?

3. **Pricing for CPQ Components:**
   - Do individual CPQ components have their own pricing?
   - Or is pricing aggregated at the configuration level?
   - How should the pricing calculations in Calculate2021.js handle this?

4. **Options Matrix:**
   - Do CPQ component IDs exist in the options_matrix tables?
   - Do we need to create new entries for CPQ components?
   - Or should we use ItemDesc1 as the display name?

---

## Next Steps

1. **Test the updated JavaScript** in a development CPQ environment
2. **Verify CPQ orders load correctly** with WebOrderNo
3. **Validate pricing calculations** for CPQ components
4. **Check options_matrix lookups** work for CPQ items
5. **Update all call sites** to pass webOrderNo parameter
6. **Create regression tests** for both traditional and CPQ orders

---

**CRITICAL:** Make these changes in a TEST environment first! Do not deploy to production until thoroughly tested with both traditional and CPQ orders.
