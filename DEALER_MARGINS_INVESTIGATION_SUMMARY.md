# Dealer Margins Investigation - Session Summary

**Date**: 2026-02-11
**Topic**: Tracing dealer margin data sources and calculations in Bennington CPQ system

---

## 🎯 Original Question

User provided margin data:
- Base Boat: 20%
- Engine: 20%
- Options: 20%
- Volume Discount: 10%
- **Freight: $1,500**
- **Prep: $1,000**

**Question**: Where does this data come from?

---

## 🔍 Key Findings

### 1. Database Structure

**Two DealerMargins Tables Found:**

#### A. `warrantyparts.DealerMargins` (SOURCE OF TRUTH)
- **Format**: WIDE (92 columns)
- **Records**: 2,335 dealers
- **Freight/Prep**: DOLLAR AMOUNTS ($1,500, $1,000)
- **Purpose**: Master data that uploads TO the CPQ API
- **Structure**: One row per dealer, separate columns per series
  - Example columns: `Q_BASE_BOAT`, `Q_ENGINE`, `Q_FREIGHT`, `Q_PREP`, etc.

#### B. `warrantyparts_test.DealerMargins` (CPQ SYNC)
- **Format**: NORMALIZED (18 columns)
- **Records**: 100 active margin records (12 dealers)
- **Freight/Prep**: PERCENTAGES (27.00%)
- **Purpose**: Loaded FROM CPQ API for testing
- **Structure**: One row per dealer-series combination

---

### 2. Margin Data Sources

#### Original Question Data (20/20/20/10 + $1,500/$1,000)
**Source**: Dealer **158772 - GILLES SALES & SERVICE**

Found in `warrantyparts.DealerMargins`:
```
S, SX, L, LX, M Series:
- Base: 20%, Engine: 20%, Options: 20%, Vol: 10%
- Freight: $1,500, Prep: $1,000
```

#### NICHOLS MARINE SE OK LLC
**Dealer ID**: 333834 (without leading zeros) or 00333834 (with leading zeros)

**Two entries found with DIFFERENT margins:**

**With leading zeros (00333834):**
- All series: 27/27/27/27%, Freight: $0, Prep: $0

**Without leading zeros (333834):**
- Q/QX: 25/25/25/10%
- R/S/L: 20/20/20/10%
- M: 37/37/37/10%
- Freight: $0, Prep: $0 (all series)

#### PONTOON BOAT, LLC
**Dealer ID**: 50 (Used in console logs)

Margins by series:
- Most series (Q, QX, R, S, L, etc.): **22/22/22/10% + $750 freight + $750 prep**
- SV_23: **17/17/17/10% + $0 freight + $0 prep**
- M: **37/37/37/10% + $0 freight + $0 prep**

**Note**: Different margin structures per series for same dealer!

---

### 3. Data Flow Architecture

```
warrantyparts.DealerMargins (MySQL - SOURCE OF TRUTH)
    ↓
    ↓ Exported/Synced via upload_margin.py
    ↓
Infor CPQ API (C_GD_DealerMargin endpoint)
    ↓
    ↓ Loaded via load_dealer_margins.py
    ↓
warrantyparts_test.DealerMargins (Normalized format)

ALSO:

warrantyparts.DealerMargins
    ↓
    ↓ Exported to CSV / EOS List
    ↓
EOS List 53ebba158ff57891258fef1e
    ↓
    ↓ Called by applyDealerMargins() function
    ↓
Applied to boat pricing calculations
```

---

## 🔧 Code Flow: When HIN is Clicked

### Example: ETWTEST26 (23ML boat, M Series)

**1. Initial Load** (`packagePricing.js`)
```javascript
// Load boat options from BoatOptions26 table
window.boatoptions = loadByListName('BoatOptions26',
    "WHERE BoatSerialNo='ETWTEST26'");

// Result: 63 items loaded
// Model: 23ML
// Series: M
```

**2. Apply Dealer Margins** (EOS Action: APPLY_CURRENT_DLR_STGS)
```javascript
// Get dealer ID
var dlrID = getValue('DLR', 'DLR_NO'); // "50"

// Load dealer margins from EOS List
filter = 'LIST/DealerID["' + dlrID + '"]';
results = loadList('53ebba158ff57891258fef1e', filter);

// Get series
var thisseries = getValue('DLR', 'SERIES'); // "M"

// Extract M series margins dynamically
var bb = results[0]['M_BASE_BOAT'];   // 37
var eng = results[0]['M_ENGINE'];     // 37
var opt = results[0]['M_OPTIONS'];    // 37
var fre = results[0]['M_FREIGHT'];    // 0
var prp = results[0]['M_PREP'];       // 0
var vd = results[0]['M_VOL_DISC'];    // 10

// Set values
setValue('MARGINS', 'BASE_BOAT', bb);
setValue('MARGINS', 'ENGINE', eng);
setValue('MARGINS', 'OPTIONS', opt);
setValue('FREIGHTPREP', 'FREIGHT', fre);
setValue('FREIGHTPREP', 'PREP', prp);
setValue('MARGINS', 'VOL_DISC', vd);

// Store in window variables
window.freight = fre;  // 0
window.prep = prp;     // 0
```

**3. Calculate Pricing** (`calculate2021.js`)
```javascript
// Boat MSRP: $58,171.00
// Dealer Cost: $41,131.00

// Apply margins:
baseboatmargin = (100 - 37) / 100;    // 0.63
enginemargin = (100 - 37) / 100;      // 0.63
optionmargin = (100 - 37) / 100;      // 0.63
vol_disc = (100 - 10) / 100;          // 0.90

// Final prices:
DLR2/BOAT_MS = 58171   // MSRP
DLR2/BOAT_SP = 58759   // Sale Price
```

---

## 📊 Console Log Evidence

From actual console output when clicking ETWTEST26:

```
ZACH DEALER ID: 50
thisseries M

MARGINS/BASE_BOAT = 37
MARGINS/ENGINE = 37
MARGINS/OPTIONS = 37
MARGINS/VOL_DISC = 10
FREIGHTPREP/FREIGHT = 0
FREIGHTPREP/PREP = 0

boat package SALE price (+Pontoon) is now 58758.57
Using real MSRP from CPQ: $ 58171
DLR2/BOAT_SP = 58759
DLR2/BOAT_MS = 58171
```

---

## 🗂️ Key Files

### Database Tables
- `warrantyparts.DealerMargins` - 2,335 dealers, wide format, dollar amounts
- `warrantyparts_test.DealerMargins` - 12 dealers, normalized, percentages

### EOS List
- **List ID**: `53ebba158ff57891258fef1e`
- **File**: `list-53ebba158ff57891258fef1e.csv`
- **Contains**: Same data as warrantyparts.DealerMargins

### JavaScript Files
- `packagePricing.js` - Loads boat data, detects CPQ boats
- EOS Action: "Apply Current Dealership Margins" (ID: 5f22cf0109525738576ba044)
  - Function: `applyDealerMargins()`
  - Calls: `loadList('53ebba158ff57891258fef1e', filter)`
- `calculate2021.js` - Applies margins to pricing calculations
- `print.js` - Generates window sticker (no hard-coded freight/prep values)

### Python Scripts
- `upload_margin.py` - Uploads margins FROM warrantyparts TO API
- `load_dealer_margins.py` - Loads margins FROM API TO warrantyparts_test
- `query_dealer_margins.py` - Queries DealerMargins table

---

## ❗ Important Findings

### 1. Duplicate Dealer IDs
NICHOLS dealers appear TWICE with different margin structures:
- **With leading zeros** (00333834): 27% across board
- **Without leading zeros** (333834): Variable margins by series

### 2. Freight/Prep Storage Difference
- **warrantyparts.DealerMargins**: Dollar amounts ($1,500, $1,000)
- **warrantyparts_test.DealerMargins**: Percentages (27.00%)
- **EOS calculations use**: Dollar amounts from warrantyparts

### 3. Series-Specific Margins
Same dealer can have different margins per series:
- Dealer 50: 22% for most series, 17% for SV_23, 37% for M

### 4. No Hard-Coded Defaults
- No hard-coded freight/prep values found in codebase
- All values come from database/EOS list

---

## 🔐 Database Credentials

```
Host:     ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com
User:     awsmaster
Password: VWvHG9vfG23g7gD
Database: warrantyparts (source) / warrantyparts_test (cpq sync)
```

---

## 📝 Queries Used

### Find dealer with specific margins:
```sql
SELECT * FROM warrantyparts.DealerMargins
WHERE S_FREIGHT = 1500 AND S_PREP = 1000;
```

### Check dealer margins by ID:
```sql
SELECT DealerID, Dealership,
       Q_BASE_BOAT, Q_ENGINE, Q_OPTIONS, Q_FREIGHT, Q_PREP, Q_VOL_DISC
FROM warrantyparts.DealerMargins
WHERE DealerID = '50';
```

### Python query example:
```python
import mysql.connector

connection = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)
cursor = connection.cursor(dictionary=True)
cursor.execute("SELECT * FROM DealerMargins WHERE DealerID = '50'")
result = cursor.fetchone()
```

---

## ✅ Summary Answer

**Where does the 20/20/20/10 + $1,500/$1,000 data come from?**

**Answer**:
- **Database**: `warrantyparts.DealerMargins`
- **Dealer**: 158772 - GILLES SALES & SERVICE
- **Series**: S, SX, L, LX, M
- **Storage**: Dollar amounts for freight/prep (not percentages)
- **Usage**: Loaded into EOS List 53ebba158ff57891258fef1e, then applied by `applyDealerMargins()` function when boat HIN is clicked

**NOT from**:
- NICHOLS MARINE dealers (different margins)
- Hard-coded defaults (none found)
- API percentages (different format)

---

## 🔮 Next Steps / Questions to Investigate

1. Why do NICHOLS dealers have duplicate entries (with/without leading zeros)?
2. Should dealer 50 (PONTOON BOAT, LLC) have different margins per series?
3. How often is EOS List 53ebba158ff57891258fef1e synced from the database?
4. Why does warrantyparts_test only have 12 dealers vs 2,335 in source?
5. Are the freight/prep dollar amounts being properly applied in final pricing?

---

**Session ended**: 2026-02-11
**Ready to resume**: Yes - All context saved
