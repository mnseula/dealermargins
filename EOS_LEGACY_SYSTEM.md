# EOS Legacy System - How It Worked Without CPQ

## Overview

Before the CPQ integration, the entire boat configuration and pricing system relied solely on the **EOS (Enterprise Operating System)** database. This document explains how that legacy system worked and how data was structured.

---

## Historical Context

### Timeline
- **Pre-2025**: All boat data stored exclusively in EOS database
- **2025+**: CPQ system introduced for new models
- **Current**: Hybrid system with CPQ primary, EOS fallback for backward compatibility

### Why EOS Only?
The EOS system was the original manufacturing and sales database that contained:
- All historical boat models (going back to early 2000s)
- Production records and serial numbers
- Dealer information and margins
- Standard features and options matrices
- Performance package specifications

---

## EOS Database Structure (Eos database)

### Core Tables

#### 1. **options_matrix_YYYY** (e.g., options_matrix_2024, options_matrix_2025)
**Purpose**: Defines all available options for each model by year

**Structure**:
```sql
CREATE TABLE options_matrix_2024 (
    SERIES VARCHAR(5),           -- Boat series (Q, QX, S, SV, etc.)
    MODEL VARCHAR(15),           -- Full model ID (168SFSR, 20SVFSR, etc.)
    PART VARCHAR(50),            -- Part number for the option
    CATEGORY VARCHAR(30),        -- Option category
    OPT_NAME VARCHAR(1000),      -- Option description
    PROD_TITLE VARCHAR(255),     -- Product title
    QTY VARCHAR(5),              -- Quantity
    MORE_OPTION INT,             -- Flag for additional option
    VISIBILITY_LEVEL INT,        -- Who can see this option
    REQ_BY_MODEL INT,            -- Required by model flag
    INC_BY_MODEL INT,            -- Included by model flag
    COMPAT_PERF_PKG VARCHAR(60), -- Compatible performance packages
    MODEL_DEFAULT INT,           -- Default for this model
    UPSELL INT,                  -- Upsell flag
    REQ_CUSTOM_DRAW INT,         -- Requires custom drawing
    CUST_DRAW_NO VARCHAR(100),   -- Custom drawing number
    OBSOLETE INT                 -- Obsolete flag
);
```

**Example Data**:
```
SERIES: S
MODEL: 168SFSR
PART: 901254
CATEGORY: Electronics
OPT_NAME: ECHOMAP GARMIN GIMBLE MNT SV-S
COMPAT_PERF_PKG: 23_IN_16,SPS_23_16
```

**Key Points**:
- One table per model year
- Contains ALL possible options for each model
- Includes compatibility rules with performance packages
- Shows which options are standard vs. available

---

#### 2. **perf_pkg_spec**
**Purpose**: Performance package specifications across all models and years

**Structure**:
```sql
CREATE TABLE perf_pkg_spec (
    MODEL VARCHAR(255),          -- Model ID (can have variations)
    PKG_ID FLOAT,               -- Package ID number
    PKG_NAME VARCHAR(255),       -- Package display name
    STATUS VARCHAR(255),         -- Active/Inactive
    MAX_HP VARCHAR(255),         -- Maximum horsepower (e.g., "90 HP")
    CAP VARCHAR(255),            -- Person capacity (e.g., "10 People")
    WEIGHT VARCHAR(255),         -- Hull weight (e.g., "1,761 lbs")
    PONT_GAUGE VARCHAR(255),     -- Pontoon gauge (e.g., "0.08")
    TRANSOM INT,                 -- Transom height in inches
    ORDER INT                    -- Display order
);
```

**Example Data**:
```
MODEL: 168SF23SR
PKG_NAME: 1. With 23" Tubes (20" transom)
MAX_HP: 40 HP
CAP: 6 People
WEIGHT: 1,546 lbs
PONT_GAUGE: 0.08
TRANSOM: 20
```

**Important Characteristics**:
- **Same model appears multiple times** - one row per performance package
- Model IDs include tube size suffix (e.g., 168SF**23**SR = 23" tubes)
- Some fields stored as text with units included
- May contain duplicate/similar entries with slight naming variations

---

#### 3. **standards_matrix_YYYY** (e.g., standards_matrix_2024)
**Purpose**: Standard features included with each model

**Structure**:
```sql
CREATE TABLE standards_matrix_2024 (
    SERIES VARCHAR(10),          -- Boat series
    MODEL VARCHAR(15),           -- Model ID
    STANDARD VARCHAR(10),        -- Standard item code
    CATEGORY VARCHAR(30),        -- Feature category
    OPT_NAME TEXT                -- Feature description
);
```

**Example Data**:
```
SERIES: S
MODEL: 168SFSR
STANDARD: STD001
CATEGORY: Console Features
OPT_NAME: Console Courtesy Light
```

**Key Points**:
- Contains HTML entities (&quot;, &amp;, &#039;, etc.)
- May have duplicates across different model variations
- Organized by category (Console Features, Exterior, Interior, Warranty)

---

## Production Database (warrantyparts database)

### Core Tables

#### 1. **SerialNumberMaster**
**Purpose**: Master record of every boat produced

**Structure**:
```sql
CREATE TABLE SerialNumberMaster (
    SN_MY INT,                      -- Serial number model year
    Boat_SerialNo VARCHAR(20),      -- HIN (Hull Identification Number)
    BoatItemNo VARCHAR(255),        -- Model ID (production format)
    Series VARCHAR(10),             -- Series code
    BoatDesc1 VARCHAR(255),         -- Model description
    BoatDesc2 VARCHAR(255),         -- Additional description
    SerialModelYear VARCHAR(4),     -- Model year
    ERP_OrderNo VARCHAR(10),        -- ERP order number
    ProdNo INT,                     -- Production number
    OrigOrderType VARCHAR(1),       -- Original order type
    InvoiceNo VARCHAR(10),          -- Invoice number
    ApplyToNo VARCHAR(10),          -- Apply to number
    InvoiceDateYYYYMMDD VARCHAR(10),-- Invoice date
    DealerNumber VARCHAR(20),       -- Dealer ID
    DealerName VARCHAR(255),        -- Dealer name
    DealerCity VARCHAR(30),         -- Dealer city
    DealerState VARCHAR(20),        -- Dealer state
    ColorPackage VARCHAR(50),       -- Color package
    PanelColor VARCHAR(99),         -- Panel color
    AccentPanel VARCHAR(99),        -- Accent panel
    TrimAccent VARCHAR(99),         -- Trim accent
    BaseVinyl VARCHAR(99),          -- Base vinyl
    WebOrderNo VARCHAR(20),         -- Web order number
    Presold VARCHAR(1),             -- Presold flag
    Active INT,                     -- Active status
    BenningtonOwned INT             -- Bennington owned flag
);
```

**Example Data**:
```
Boat_SerialNo: ETWP6278J324
BoatItemNo: 20SVFSR
Series: SV
BoatDesc1: 20 S 4 PT FISHING
SerialModelYear: 2024
InvoiceNo: 1095452
DealerNumber: 333836
DealerName: NICHOLS MARINE - NORMAN
```

**Key Role**:
- Links HIN to model, dealer, and order information
- Contains basic model description
- **Does NOT contain**: pricing, features, performance specs
- Used to look up basic boat information

---

#### 2. **BoatOptionsYY** (e.g., BoatOptions24, BoatOptions25)
**Purpose**: Line items for every boat sold - shows what was actually configured

**Structure**:
```sql
CREATE TABLE BoatOptions24 (
    BoatSerialNo VARCHAR(20),        -- HIN
    BoatModelNo VARCHAR(50),         -- Model ID
    Series VARCHAR(10),              -- Series
    ERP_OrderNo VARCHAR(20),         -- Order number
    Orig_Ord_Type VARCHAR(5),        -- Order type
    InvoiceNo VARCHAR(20),           -- Invoice number
    ApplyToNo VARCHAR(20),           -- Apply to number
    WebOrderNo VARCHAR(20),          -- Web order number
    InvoiceDate DATE,                -- Invoice date
    LineNo INT,                      -- Line number
    LineSeqNo INT,                   -- Line sequence
    MCTDesc VARCHAR(100),            -- MCT description
    ItemNo VARCHAR(50),              -- Item number
    ItemDesc1 VARCHAR(255),          -- Item description
    OptionSerialNo VARCHAR(50),      -- Option serial number
    ItemMasterMCT VARCHAR(10),       -- Item master MCT
    ItemMasterProdCat VARCHAR(10),   -- Product category
    ItemMasterProdCatDesc VARCHAR(50), -- Category description
    QuantitySold DECIMAL(10,2),      -- Quantity sold
    ExtSalesAmount DECIMAL(15,2)     -- Extended sales amount (MSRP)
);
```

**Item Categories** (ItemMasterProdCat):
- **BS1**: Base Boat (the boat package itself)
- **EN7**: Engine (outboard motor)
- **ACC**: Accessories (fish finders, covers, etc.)
- **H1**, **H1F**, **H1I**, **H1V**, **H3A**, **H5**, **L0**, **L12**: Color/Panel/Vinyl/Furniture options
- **C1L**, **C2**, **C3P**, **C3S**: Discounts (CSI, Volume, Package Pricing)
- **GRO**: Discover Boating Fee
- **LAB**: Labor/Rigging
- **PRE**: Pre-rig items

**Example Data**:
```
BoatSerialNo: ETWP6278J324
BoatModelNo: 20SVFSR
ItemNo: 901254
ItemDesc1: ECHOMAP GARMIN GIMBLE MNT SV-S
ItemMasterProdCat: ACC
ExtSalesAmount: 600.00
```

**Critical for MSRP**:
- `ExtSalesAmount` contains the actual MSRP for each line item
- Base boat (BS1) = Base MSRP
- Engine (EN7) = Engine MSRP
- Accessories (ACC) = Add-on options MSRP
- **SUM of all ExtSalesAmount = Total MSRP**

---

#### 3. **dealermaster - use the one in eos**
**Purpose**: Dealer information (shared table name, exists in warrantyparts)

**Structure**:
```sql
CREATE TABLE `dealermaster - use the one in eos` (
    auto INT,
    dealer VARCHAR(40),             -- Dealer name
    dealerno INT,                   -- Dealer number
    dba VARCHAR(100),               -- DBA name
    productline VARCHAR(3),         -- Product line (BEN, AZU, etc.)
    activeyear VARCHAR(5),          -- Active year
    dateactive VARCHAR(10),         -- Date became active
    dateinactive VARCHAR(10),       -- Date became inactive
    city VARCHAR(15),               -- City
    state VARCHAR(2),               -- State
    salesrep VARCHAR(20),           -- Sales rep
    -- ... other fields
);
```

**Example Data**:
```
dealerno: 333836
dealer: NICHOLS MARINE - NORMAN
city: NORMAN
state: OK
productline: BEN
```

**Key Points**:
- One row per dealer × productline
- Same dealer appears multiple times (one for each product line: BEN, AZU, SED, SOU)
- Filter by `productline = 'BEN'` for Bennington boats

---

#### 4. **DealerMargins**
**Purpose**: Dealer margin percentages by series

**Structure**:
```sql
CREATE TABLE DealerMargins (
    DealerID VARCHAR(10),
    Dealership VARCHAR(255),
    -- Q Series
    Q_BASE_BOAT DECIMAL(10,2),
    Q_ENGINE DECIMAL(10,2),
    Q_OPTIONS DECIMAL(10,2),
    Q_FREIGHT DECIMAL(10,2),
    Q_PREP DECIMAL(10,2),
    Q_VOL_DISC DECIMAL(10,2),
    -- QX Series
    QX_BASE_BOAT DECIMAL(10,2),
    QX_ENGINE DECIMAL(10,2),
    QX_OPTIONS DECIMAL(10,2),
    -- ... repeated for each series (QXS, R, RX, RT, G, S, SX, L, LX, LT, S_23, SV_23, M)
    -- Each series has: BASE_BOAT, ENGINE, OPTIONS, FREIGHT, PREP, VOL_DISC
);
```

**Example Data**:
```
DealerID: 333836
Dealership: NICHOLS MARINE - NORMAN
SV_23_BASE_BOAT: 17.00
SV_23_ENGINE: 17.00
SV_23_OPTIONS: 17.00
SV_23_FREIGHT: NULL
SV_23_PREP: NULL
SV_23_VOL_DISC: 10.00
```

**Margin Calculation**:
```
Dealer Cost = MSRP × (1 - Margin%)
Dealer Savings = MSRP × Margin%

Example with 17% margin on $25,895 base boat:
  Dealer Cost = $25,895 × (1 - 0.17) = $21,492.85
  Dealer Savings = $25,895 × 0.17 = $4,402.15
```

---

## How Window Stickers Were Generated (EOS Only)

### Pre-CPQ Process (Legacy)

**Input**: Model ID (e.g., "20SVFSR"), Dealer ID, Year

**Step 1: Get Model Info**
```sql
SELECT BoatItemNo, Series, BoatDesc1, SerialModelYear
FROM warrantyparts.SerialNumberMaster
WHERE BoatItemNo = '20SVFSR'
  AND SerialModelYear = '2024'
LIMIT 1;
```
**Returns**: Basic model description and series

---

**Step 2: Get Performance Packages**
```sql
SELECT DISTINCT PKG_NAME, MAX_HP, CAP, WEIGHT, PONT_GAUGE, TRANSOM
FROM Eos.perf_pkg_spec
WHERE MODEL LIKE '20SVF%'
  AND STATUS = 'Active'
ORDER BY PKG_NAME;
```
**Returns**: All available performance packages for this model
- Multiple variations of same package (with different tube sizes, suffixes)
- Use DISTINCT to reduce duplicates

---

**Step 3: Get Standard Features**
```sql
SELECT DISTINCT CATEGORY, OPT_NAME
FROM Eos.standards_matrix_2024
WHERE MODEL LIKE '20SVF%'
ORDER BY CATEGORY, OPT_NAME;
```
**Returns**: Standard equipment by category
- Console Features
- Exterior Features
- Interior Features
- Warranty

**Note**: Contains HTML entities that need cleaning

---

**Step 4: Get Included Options (from actual boat sales)**
```sql
SELECT DISTINCT ItemNo, ItemDesc1, QuantitySold, ExtSalesAmount
FROM warrantyparts.BoatOptions24
WHERE BoatModelNo = '20SVFSR'
  AND ItemMasterProdCat = 'ACC'
  AND ItemNo IS NOT NULL
ORDER BY ItemDesc1;
```
**Returns**: Accessories that were configured on sold boats

---

**Step 5: Calculate MSRP (if needed)**
```sql
SELECT
    SUM(CASE WHEN ItemMasterProdCat = 'BS1' THEN ExtSalesAmount ELSE 0 END) AS base_boat_msrp,
    SUM(CASE WHEN ItemMasterProdCat = 'EN7' THEN ExtSalesAmount ELSE 0 END) AS engine_msrp,
    SUM(CASE WHEN ItemMasterProdCat = 'ACC' THEN ExtSalesAmount ELSE 0 END) AS accessories_msrp
FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = 'ETWP6278J324';
```
**Returns**: Actual MSRP breakdown from sold boat

---

**Step 6: Get Dealer Info**
```sql
SELECT dealerno, dealer, city, state
FROM warrantyparts.`dealermaster - use the one in eos`
WHERE dealerno = 333836
  AND productline = 'BEN'
LIMIT 1;
```
**Returns**: Dealer name and location

---

**Step 7: Get Dealer Margins**
```sql
SELECT SV_23_BASE_BOAT, SV_23_ENGINE, SV_23_OPTIONS
FROM warrantyparts.DealerMargins
WHERE DealerID = '333836';
```
**Returns**: Margin percentages for this dealer/series

---

### Output Assembly

The window sticker was assembled from these components:

```
1. HEADER
   - "BENNINGTON MARINE"
   - "MANUFACTURER'S SUGGESTED RETAIL PRICE"

2. MODEL INFORMATION
   - Model Number: 20SVFSR
   - Series: SV
   - Year: 2024
   - Description: 20 S 4 PT FISHING

3. VESSEL SPECIFICATIONS
   - From first performance package in perf_pkg_spec:
     * Hull Weight, Max HP, Person Capacity
     * Pontoon specs, Transom height

4. BASE MSRP
   - From BoatOptions: SUM(ExtSalesAmount)
   - Displayed prominently in box

5. STANDARD EQUIPMENT
   - From standards_matrix_YYYY
   - Grouped by CATEGORY
   - Each feature with checkmark (✓)

6. AVAILABLE PERFORMANCE PACKAGES
   - From perf_pkg_spec
   - Listed as options 1, 2, 3, etc.

7. INCLUDED OPTIONS
   - From BoatOptions WHERE ItemMasterProdCat = 'ACC'
   - Item number, description, quantity, price

8. FOOTER
   - Dealer name and location
   - Generated date
   - Compliance statement
```

---

## Data Challenges in EOS System

### 1. **Model ID Variations**
**Problem**: Same model appears with different suffixes
```
Base Model: 168SF
Production Models:
  - 168SFSR (Stern Radius)
  - 168SFSE (Standard something)
  - 168SF23SR (23" tubes + Stern Radius)
  - 168SFDE (Different variant)
```

**Solution**: Pattern matching with LIKE
```sql
WHERE MODEL LIKE '168SF%'
```

---

### 2. **Duplicate Records**
**Problem**: Same feature appears multiple times
```
CATEGORY: Console Features
OPT_NAME: Console Courtesy Light
... appears 3 times for model variations
```

**Solution**: Use DISTINCT in queries

---

### 3. **HTML Entities in Text**
**Problem**: Feature descriptions contain encoded characters
```
&quot;  = "
&amp;   = &
&#039;  = '
&lt;    = <
&gt;    = >
```

**Solution**: Either decode or display as-is

---

### 4. **No Direct MSRP**
**Problem**: EOS tables don't store final pricing
- options_matrix doesn't have prices
- perf_pkg_spec doesn't have prices
- standards_matrix doesn't have prices

**Solution**: Must calculate from BoatOptions (actual sales data)
```sql
SELECT SUM(ExtSalesAmount) FROM BoatOptions24
WHERE BoatSerialNo = 'ETWP6278J324'
  AND ItemMasterProdCat IN ('BS1', 'EN7', 'ACC')
```

---

### 5. **Performance Package Confusion**
**Problem**: Multiple entries per model
```
Model: 168SF23SR has 18 performance packages listed
But only showing options, not which one was actually selected
```

**Solution for "Available Packages"**: Show all distinct packages
**Solution for "Specific Boat"**: Cross-reference with BoatOptions or BoatConfigurationAttributes

---

## Model ID Naming Convention

### Format: `[Length][Series][Floorplan][Suffix]`

**Examples**:
- `168SFSR` = 16' (8' beam) S-Series Fishing Stern-Radius
- `20SVFSR` = 20' SV-Series Fishing Stern-Radius
- `25QXFBWA` = 25' QX-Series Fastback Windshield-Arch
- `168SF23SR` = 16' (8' beam) S-Series Fishing 23"-tubes Stern-Radius

**Common Suffixes**:
- **SR**: Stern Radius
- **SE**: Standard (something)
- **SA**: (variant A)
- **ST**: (variant T)
- **23SR**: 23" tubes + Stern Radius
- **25SR**: 25" tubes + Stern Radius

---

## Query Patterns for Window Stickers

### Pattern 1: Get All Available Options
```sql
-- For showing "what's possible" with this model
SELECT * FROM Eos.perf_pkg_spec
WHERE MODEL LIKE CONCAT(base_model, '%')
  AND STATUS = 'Active';
```

### Pattern 2: Get Specific Boat Configuration
```sql
-- For showing "what this actual boat has"
SELECT * FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = 'ETWP6278J324';
```

### Pattern 3: Calculate Total MSRP
```sql
SELECT
    SUM(ExtSalesAmount) as total_msrp
FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = 'ETWP6278J324'
  AND ItemMasterProdCat IN ('BS1', 'EN7', 'ACC');
```

### Pattern 4: Get Dealer Margin for Series
```sql
SELECT
    CASE
        WHEN Series = 'SV' THEN SV_23_BASE_BOAT
        WHEN Series = 'S' THEN S_BASE_BOAT
        WHEN Series = 'Q' THEN Q_BASE_BOAT
        -- etc for each series
    END as base_margin
FROM warrantyparts.DealerMargins
WHERE DealerID = '333836';
```

---

## Migration to CPQ

### Why CPQ Was Introduced

**Problems with EOS-Only**:
1. ❌ Data scattered across multiple tables
2. ❌ Inconsistent naming and duplicates
3. ❌ No centralized pricing
4. ❌ HTML entities in descriptions
5. ❌ Performance package confusion
6. ❌ Difficult to query and maintain

**CPQ Benefits**:
1. ✅ Normalized database structure
2. ✅ Clean, consistent data
3. ✅ Centralized pricing with effective dates
4. ✅ Clear performance package relationships
5. ✅ Easier to query and update
6. ✅ Better for future configurators

### Hybrid Approach (Current)

```
Try CPQ First:
  ├─ Model exists in CPQ? → Use CPQ tables
  └─ Model NOT in CPQ? → Fall back to EOS tables
```

**This ensures**:
- ✅ New models get clean CPQ data
- ✅ Historical models still accessible via EOS
- ✅ No data loss during transition
- ✅ Seamless user experience

---

## Complete Example: Window Sticker Generation (EOS Only)

### Input
```
Model: 20SVFSR
Dealer: 333836 (NICHOLS MARINE - NORMAN)
Year: 2024
HIN: ETWP6278J324 (optional - for specific boat)
```

### Process

**1. Detect: Is this in CPQ?**
```sql
SELECT COUNT(*) FROM warrantyparts_test.Models WHERE model_id = '20SVFSR';
-- Result: 0 (not in CPQ)
-- Action: Use EOS fallback
```

**2. Get Model Info from EOS**
```sql
SELECT Series, BoatDesc1 FROM warrantyparts.SerialNumberMaster
WHERE BoatItemNo = '20SVFSR' LIMIT 1;
-- Result: Series='SV', Desc='20 S 4 PT FISHING'
```

**3. Get Performance Packages**
```sql
SELECT DISTINCT PKG_NAME, MAX_HP, CAP, WEIGHT
FROM Eos.perf_pkg_spec
WHERE MODEL LIKE '20SVF%' AND STATUS='Active';
-- Result: 8 performance packages
```

**4. Get Standard Features**
```sql
SELECT DISTINCT CATEGORY, OPT_NAME
FROM Eos.standards_matrix_2024
WHERE MODEL LIKE '20SVF%';
-- Result: 56 standard features
```

**5. Get Included Options**
```sql
SELECT ItemDesc1, ExtSalesAmount
FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = 'ETWP6278J324'
  AND ItemMasterProdCat = 'ACC';
-- Result: 3 accessories ($712 total)
```

**6. Calculate MSRP**
```sql
SELECT
    SUM(CASE WHEN ItemMasterProdCat='BS1' THEN ExtSalesAmount END) as base,
    SUM(CASE WHEN ItemMasterProdCat='EN7' THEN ExtSalesAmount END) as engine,
    SUM(CASE WHEN ItemMasterProdCat='ACC' THEN ExtSalesAmount END) as acc
FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = 'ETWP6278J324';
-- Result: Base=$25,895, Engine=$9,011, Acc=$712
-- Total MSRP: $35,618
```

**7. Get Dealer Margins**
```sql
SELECT SV_23_BASE_BOAT, SV_23_ENGINE, SV_23_OPTIONS
FROM warrantyparts.DealerMargins
WHERE DealerID = '333836';
-- Result: 17%, 17%, 17%
```

**8. Assemble Window Sticker**
```
╔══════════════════════════════════════════════╗
║      BENNINGTON MARINE                       ║
║ MANUFACTURER'S SUGGESTED RETAIL PRICE        ║
╚══════════════════════════════════════════════╝

MODEL: 20SVFSR
YEAR: 2024
SERIES: SV (20 S 4 PT FISHING)

SPECIFICATIONS:
  Hull Weight: 1,761 lbs
  Max HP: 90 HP
  Capacity: 10 People

╔══════════════════════════════════════════════╗
║       BASE MSRP: $35,618.00                  ║
╚══════════════════════════════════════════════╝

STANDARD EQUIPMENT:
  Console Features (12 items)
  Exterior Features (23 items)
  Interior Features (19 items)
  Warranty (2 items)

AVAILABLE PERFORMANCE PACKAGES: (8 options)
  1. With 25" Tubes (20" transom) - 90 HP
  2. With 25" Tubes - 115 HP
  ...

INCLUDED OPTIONS:
  • Garmin ECHOMAP - $600.00
  • Trolling Motor Harness - $112.00
  • Gate Cover - $0.00

DEALER: NICHOLS MARINE - NORMAN
Generated: January 28, 2026
```

---

## Summary

### EOS System Architecture (Pre-CPQ)

```
┌─────────────────────────────────────────┐
│     Eos Database (Configuration)        │
├─────────────────────────────────────────┤
│  • options_matrix_YYYY                  │
│  • perf_pkg_spec                        │
│  • standards_matrix_YYYY                │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  warrantyparts (Production)             │
├─────────────────────────────────────────┤
│  • SerialNumberMaster (boats made)      │
│  • BoatOptionsYY (what's on each boat)  │
│  • dealermaster (dealer info)           │
│  • DealerMargins (pricing)              │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│     Window Sticker Generator            │
└─────────────────────────────────────────┘
```

### Key Takeaways

1. **EOS = Historical System**: All data before 2025
2. **Multiple Tables Required**: No single source of truth
3. **MSRP from Sales Data**: Calculate from BoatOptions, not stored directly
4. **Pattern Matching Essential**: Model IDs have variations
5. **DISTINCT Required**: Duplicate data common
6. **HTML Entities Present**: In standard features
7. **Dealer Margins by Series**: Wide table with all series columns
8. **Works But Complex**: Functional but harder to maintain than CPQ

---

**Document Version**: 1.0
**Last Updated**: January 28, 2026
**Author**: CPQ Migration Team
