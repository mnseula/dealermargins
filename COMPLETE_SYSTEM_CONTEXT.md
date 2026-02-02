# Complete Dealer Margins & Window Sticker System - Master Context

**Date**: January 28, 2026
**Session**: Comprehensive System Documentation
**Next Session**: MSSQL colines and cfg_attributes work

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Data Sources](#data-sources)
3. [Database Architecture](#database-architecture)
4. [Data Flow](#data-flow)
5. [Key Components](#key-components)
6. [Business Logic](#business-logic)
7. [Critical Findings](#critical-findings)
8. [Production Systems](#production-systems)
9. [Next Session Prep](#next-session-prep)

---

## System Overview

### Purpose
Build a comprehensive dealer margin and window sticker system for Bennington Marine that:
- Calculates dealer costs from MSRP
- Generates window stickers with pricing
- Supports both CPQ (2025+) and EOS (pre-2025) models
- Syncs dealer margins between MySQL and Infor CPQ

### Business Model
```
BENNINGTON MANUFACTURING
  ↓ Sells at dealer cost (MSRP minus margin %)
DEALER (e.g., NICHOLS MARINE)
  ↓ Sells at MSRP or negotiated price
END CUSTOMER

Dealer Profit = MSRP - Dealer Cost
Example: $35,618 MSRP - $29,563 dealer cost = $6,055 profit (17%)
```

### Key Metrics
- **2,334 dealers** in production system
- **35,003 dealer margin configs** (2,334 dealers × 15 series)
- **283 CPQ models** (2025+ boats)
- **62,781 boats** in serial number registry
- **422 dealers** with configured margins (rest are placeholders)

---

## Data Sources

### 1. MySQL Databases

#### **warrantyparts** (PRODUCTION)
- **Primary database** for production operations
- Contains EOS legacy data
- **Key tables**:
  - `DealerMargins` (2,334 dealers) - **SOURCE OF TRUTH**
  - `SerialNumberMaster` (62,781 boats)
  - `BoatOptions{YY}` - Historical sales data with MSRP
  - `DealerAddr` (2,086 addresses)
  - `dealermaster - use the one in eos` - Dealer master data

#### **warrantyparts_test** (CPQ/TEST)
- **CPQ infrastructure** and testing
- Contains new normalized tables
- **Key tables**:
  - `Models` (283 models)
  - `ModelPricing` (283 pricing records)
  - `ModelPerformance` (281 performance specs)
  - `ModelStandardFeatures` - Standard features
  - `StandardFeatures` - Feature catalog
  - `DealerMargins` (CPQ import cache - 100→35,003 records)
  - `DealerQuotes` (422 dealers) - **Was incorrect source, now deprecated**
  - `BoatConfigurationAttributes` (2,323 configs)
  - `Dealers` (12 CPQ dealers)

### 2. MSSQL Server (CSI/ERP System)

**Server**: `MPL1STGSQL086.POLARISSTAGE.COM`
**Database**: `CSISTG`
**Credentials**: svccsimarine / CNKmoFxEsXs0D9egZQXH

**Purpose**: Polaris CSI ERP system with actual order/invoice data

**Key Tables**:
- `coitem_mst` - **Customer Order Line Items** (THE PRICING SOURCE)
  - Item numbers, descriptions, quantities
  - Unit prices, extended prices
  - Serial numbers, model numbers, order numbers
  - **Product categories**: BS1 (base boat), EN7 (engine), ACC (accessories)

- `cfg_attr_mst` - **Configuration Attributes**
  - Performance package selections
  - Console, Fuel, Colors, Trim, Furniture choices
  - Actual boat configuration data

- `item_mst` - **Item Master**
  - Item descriptions
  - Product categories
  - Series information

- `inv_item_mst` - **Invoice Items**
  - Links orders to invoices

- `arinv_mst` - **AR Invoice Master**
  - Invoice dates and headers

**Import Scripts**:
- `import_configuration_attributes.py` → Loads cfg_attr_mst to BoatConfigurationAttributes
- `import_line_items.py` → Loads coitem_mst to BoatOptions25_test

### 3. Infor CPQ APIs

**Environment**: TRN (Training) and PRD (Production)

**TRN Credentials**:
```
Client ID:     QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8
Service Key:   QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw
Token URL:     https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2
```

**PRD Credentials**:
```
Client ID:     QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo
Service Key:   QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9xuXKp_iYp49_M7JuB7UaEo0xjWDqTAE1Q15rQhxojw
Token URL:     https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2
```

**API Endpoints**:
1. **Model Prices** (PRD):
   - `https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/DataImport/QA2FNBZCKUAUH7QB_PRD/v1/OptionLists/bb38d84e-6493-40c7-b282-9cb9c0df26ae/values`
   - Returns: 283 models with MSRP

2. **Performance Data** (TRN):
   - `https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/{series}_PerformanceData_2026/values`
   - Returns: Performance specs per series

3. **Standard Features** (TRN):
   - `https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/{series}_ModelStandards_2026/values`
   - Returns: Standard features per model

4. **Dealer Margins** (TRN):
   - `https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities/C_GD_DealerMargin`
   - Returns: **35,003 dealer margin records** (with `$top=50000`)
   - Currently: 83% have 27% placeholder, 17% have real margins

---

## Database Architecture

### Production Dealer Margins: warrantyparts.DealerMargins

**Structure**: Wide table (92 columns)

```sql
DealerID      VARCHAR(10)     -- e.g., '00333836'
Dealership    VARCHAR(255)    -- e.g., 'NICHOLS MARINE - NORMAN'

-- Repeated for 15 series: Q, QX, QXS, R, RX, RT, G, S, S_23, SV_23, SX, L, LX, LT, M
{SERIES}_BASE_BOAT   DECIMAL(10,2)  -- Base boat margin %
{SERIES}_ENGINE      DECIMAL(10,2)  -- Engine margin %
{SERIES}_OPTIONS     DECIMAL(10,2)  -- Options margin %
{SERIES}_FREIGHT     DECIMAL(10,2)  -- Freight discount ($ or %)
{SERIES}_PREP        DECIMAL(10,2)  -- Prep discount ($ or %)
{SERIES}_VOL_DISC    DECIMAL(10,2)  -- Volume discount %
```

**Data**:
- 2,334 total dealers
- 420 dealers with real margins (≠ 0 and ≠ 27%)
- 1,914 dealers with 27% placeholder

**Special Cases**:
- Series naming: `SV` in database = `SV_23` in columns
- Series naming: `S` in database = `S_23` in columns
- Freight/Prep: **MIXED format**
  - Most dealers: `0.00`
  - ~38 dealers: Dollar amounts (`$1500`, `$2500`, up to `$5707`)
  - Some dealers: Percentages (0-100)

**Example**:
```sql
DealerID: 00333836
Dealership: NICHOLS MARINE - NORMAN
Q_BASE_BOAT: 27.00
Q_ENGINE: 27.00
Q_OPTIONS: 27.00
Q_FREIGHT: 0.00
Q_PREP: 0.00
Q_VOL_DISC: 27.00
SV_23_BASE_BOAT: 27.00
SV_23_ENGINE: 27.00
...
```

### CPQ Dealer Margins: warrantyparts_test.DealerMargins

**Structure**: Normalized (long format)

```sql
margin_id           INT PRIMARY KEY AUTO_INCREMENT
dealer_id           VARCHAR(20)
series_id           VARCHAR(20)
base_boat_margin    DECIMAL(10,2)  -- Percentage
engine_margin       DECIMAL(10,2)  -- Percentage
options_margin      DECIMAL(10,2)  -- Percentage
freight_margin      DECIMAL(10,2)  -- Percentage (from CPQ)
prep_margin         DECIMAL(10,2)  -- Percentage (from CPQ)
volume_discount     DECIMAL(10,2)  -- Percentage
enabled             BOOLEAN
effective_date      DATE
end_date            DATE           -- NULL = current
year                INT
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

**Purpose**: Import cache from CPQ API (not for production queries)

**Data** (BEFORE FIX):
- 100 records (broken - only first page)

**Data** (AFTER FIX):
- Should have 35,003 records (after next load_cpq_data.py run)

### CPQ API: C_GD_DealerMargin Entity

**Structure**: JSON (long format)

```json
{
  "Id": "guid",
  "C_DealerId": "00333836",
  "C_DealerName": "NICHOLS MARINE - NORMAN",
  "C_Series": "SV 23",
  "C_BaseBoat": 27.0,      // Percentage
  "C_Engine": 27.0,        // Percentage
  "C_Options": 27.0,       // Percentage
  "C_Freight": 27.0,       // Percentage
  "C_Prep": 27.0,          // Percentage
  "C_Volume": 27.0,        // Percentage
  "C_Enabled": false
}
```

**Data**:
- **35,003 total records**
- **2,334 unique dealers**
- **15 series** (Q, QX, QXS, R, RX, RT, G, S, S 23, SV 23, SX, L, LX, LT, M)
- **29,021 records (83%)** with 27% placeholder
- **5,982 records (17%)** with real margins
- **All disabled** (C_Enabled = false)

### BoatOptions Tables (MSRP Source)

**Format**: One table per year or year range

**Tables**:
- `BoatOptions99_04` - 1999-2004
- `BoatOptions05_07` - 2005-2007
- `BoatOptions08_10` - 2008-2010
- `BoatOptions11_14` - 2011-2014
- `BoatOptions15` - 2015
- `BoatOptions16` - 2016
- `BoatOptions24_6252025` - 2024 through 6/25/2025
- `BoatOptions25_test` - 2025 test data

**Structure**:
```sql
BoatSerialNo        VARCHAR(20)   -- HIN
BoatModelNo         VARCHAR(14)   -- Model number
ItemNo              VARCHAR(30)   -- Item/part number
ItemDesc1           VARCHAR(255)  -- Item description
ItemMasterProdCat   VARCHAR(10)   -- Product category
QuantitySold        INT           -- Quantity
ExtSalesAmount      DECIMAL(10,2) -- Extended price
```

**Product Categories** (ItemMasterProdCat):
- `BS1` - Base Boat (hull)
- `EN7` - Engine
- `ACC` - Accessories
- `ENG` - Engine related
- `MTR` - Motor
- `L2` - Labor
- `H1` - Colors/packages
- `C1L` - Discounts
- `GRO` - Fees

**MSRP Calculation**:
```sql
SELECT
    SUM(CASE WHEN ItemMasterProdCat='BS1' THEN ExtSalesAmount END) as base_boat,
    SUM(CASE WHEN ItemMasterProdCat='EN7' THEN ExtSalesAmount END) as engine,
    SUM(CASE WHEN ItemMasterProdCat='ACC' THEN ExtSalesAmount END) as accessories
FROM BoatOptions24
WHERE BoatSerialNo = 'ETWP6278J324'
-- Result: $25,895 + $9,011 + $712 = $35,618 total MSRP
```

### BoatConfigurationAttributes Table

**Source**: MSSQL cfg_attr_mst table (imported via import_configuration_attributes.py)

**Structure**:
```sql
id                  INT PRIMARY KEY
boat_serial_no      VARCHAR(15)
boat_model_no       VARCHAR(14)
erp_order_no        VARCHAR(30)
web_order_no        VARCHAR(30)
config_id           VARCHAR(50)   -- CPQ configuration ID
attr_name           VARCHAR(100)  -- Attribute name
attr_value          VARCHAR(255)  -- Selected value
cfg_value           VARCHAR(255)  -- Configuration code
comp_id             VARCHAR(50)   -- Component ID
series              VARCHAR(5)
invoice_no          VARCHAR(30)
invoice_date        INT
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

**Purpose**: Stores actual boat configuration choices from CPQ

**Sample Attributes**:
- Performance Package
- Console
- Fuel
- Canvas Color
- Captain's Chairs
- Trim Accents
- BASE VINYL
- FLOORING
- FURNITURE UPGRADE
- Tables - Bow
- Tables - Aft

**Data**: 2,323 configuration records

---

## Data Flow

### Complete System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  DATA SOURCES                                                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. MSSQL (CSI ERP)                          2. Infor CPQ APIs   │
│     └─ coitem_mst (line items)                  ├─ Model Prices  │
│     └─ cfg_attr_mst (configs)                   ├─ Performance   │
│                                                  ├─ Features      │
│                                                  └─ Margins       │
│                                                                   │
└───────────────┬────────────────────────────────────┬─────────────┘
                │                                    │
                │ import scripts                     │ load_cpq_data.py
                │ (nightly)                          │ (nightly)
                │                                    │
                ▼                                    ▼
┌────────────────────────────────────────────────────────────────────┐
│  MYSQL DATABASES                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  warrantyparts (PRODUCTION)        warrantyparts_test (CPQ/TEST)   │
│  ├─ DealerMargins (SOURCE)         ├─ Models                       │
│  ├─ SerialNumberMaster              ├─ ModelPricing                │
│  ├─ BoatOptions{YY}                 ├─ ModelPerformance            │
│  └─ dealermaster                    ├─ DealerMargins (cache)       │
│                                      └─ BoatConfigurationAttributes │
│                                                                     │
└──────────────┬──────────────────────────────────────┬──────────────┘
               │                                      │
               │ GetDealerMarginsProduction()         │
               │ (stored procedure)                   │
               │                                      │
               ▼                                      ▼
┌────────────────────────────────────────────────────────────────────┐
│  PRODUCTION SYSTEMS                                                 │
├────────────────────────────────────────────────────────────────────┤
│  ├─ Window Sticker Generator                                       │
│  ├─ Dealer Quote System                                            │
│  └─ Dealer Portal (web interface)                                  │
└────────────────────────────────────────────────────────────────────┘
```

### Nightly Data Sync Jobs (JAMS Scheduler)

#### Job 1: Import from CPQ APIs
```
load_cpq_data.py (runs nightly)
├─ Fetch model prices (PRD) → Models, ModelPricing
├─ Fetch performance data (TRN) → ModelPerformance
├─ Fetch standard features (TRN) → StandardFeatures
└─ Fetch dealer margins (TRN) → DealerMargins (cache)
   └─ ✅ FIXED: Now uses $top=50000 to get all 35,003 records
```

#### Job 2: Import from MSSQL
```
import_configuration_attributes.py
└─ Fetch cfg_attr_mst → BoatConfigurationAttributes

import_line_items.py
└─ Fetch coitem_mst → BoatOptions25_test
```

#### Job 3: Upload to CPQ (PAUSED - needs freight/prep fix)
```
upload_margin.py
├─ Read warrantyparts.DealerMargins (2,334 dealers)
├─ Transform wide → long (2,334 → 35,003 records)
├─ Convert freight/prep formats ($ → %)
└─ Upload to CPQ API (POST/PUT)
   └─ ⚠️ ISSUE: Can't convert $1500 to % without base freight cost
```

---

## Key Components

### 1. Stored Procedures

#### GetDealerMarginsProduction()
**File**: `unified_dealer_margins_production.sql`
**Location**: warrantyparts_test database
**Purpose**: Query production dealer margins

**Usage**:
```sql
CALL GetDealerMarginsProduction('333836', 'SV_23');
```

**Returns**:
```
dealer_id, dealer_name, series_id,
base_boat_margin_pct, engine_margin_pct, options_margin_pct,
freight_type ('FIXED_AMOUNT'), freight_value,
prep_type ('FIXED_AMOUNT'), prep_value,
volume_discount_pct, data_source ('warrantyparts.DealerMargins')
```

**Key Logic**:
- Normalizes dealer ID (removes leading zeros)
- Maps series names (SV → SV_23, S → S_23)
- Uses dynamic SQL to query wide table
- Always queries `warrantyparts.DealerMargins` (production)

#### GetSeriesColumnPrefix()
**Purpose**: Map series ID to column prefix

**Examples**:
```sql
SELECT GetSeriesColumnPrefix('SV');     -- Returns: 'SV_23_'
SELECT GetSeriesColumnPrefix('SV 23');  -- Returns: 'SV_23_'
SELECT GetSeriesColumnPrefix('Q');      -- Returns: 'Q_'
```

#### GetWindowStickerData()
**File**: `stored_procedures_with_eos_fallback.sql`
**Purpose**: Get complete window sticker data

**Usage**:
```sql
CALL GetWindowStickerData('25QXFBWA', '333836', 2025, NULL);
CALL GetWindowStickerData('20SVFSR', '333836', 2024, 'ETWP6278J324');
```

**Returns** (4 result sets):
1. Model information with pricing
2. Performance specifications
3. Standard features by area
4. Included options (accessories)

**Logic**:
- Tries CPQ first (Models, ModelPricing tables)
- Falls back to EOS (SerialNumberMaster, Eos.perf_pkg_spec)
- Filters by year for historical accuracy

### 2. Python Scripts

#### load_cpq_data.py
**Purpose**: Nightly import from CPQ APIs to MySQL

**Fixed Issues**:
- ✅ Now uses `$top=50000` for dealer margins (was only getting 100)
- ✅ Will import all 35,003 margin records

**Flow**:
```python
1. Get tokens (PRD and TRN)
2. Fetch model prices → Models, ModelPricing
3. Fetch performance data (per series) → ModelPerformance
4. Fetch standard features (per series) → StandardFeatures
5. Fetch dealer margins (ALL 35,003) → DealerMargins
```

#### upload_margin.py
**Purpose**: Upload dealer margins from MySQL to CPQ

**Status**: ⚠️ ON HOLD - freight/prep conversion issue

**Fixed Issues**:
- ✅ Now reads from `warrantyparts.DealerMargins` (was reading test table)

**Outstanding Issue**:
- ⚠️ Can't convert freight/prep dollar amounts to percentages
- 38 dealers have values like `$1500`, `$2500`
- Need base freight cost per series to calculate %

**Flow**:
```python
1. Read warrantyparts.DealerMargins (2,334 rows)
2. Transform wide → long format (→ 35,003 records)
3. For each dealer-series combination:
   - Query CPQ to check if exists
   - If exists: PUT (update)
   - If not: POST (create)
4. Update all 35,003 records in CPQ
```

#### generate_window_sticker_with_pricing.py
**Purpose**: Generate window stickers with MSRP and dealer costs

**Usage**:
```bash
python3 generate_window_sticker_with_pricing.py 20SVFSR 333836 2024 ETWP6278J324
```

**Features**:
- Calculates MSRP from BoatOptions table
- Gets dealer margins from production table
- Calculates dealer costs
- Shows both MSRP and dealer cost
- Displays standard features and options

**Status**: ✅ Working with production data

#### import_configuration_attributes.py
**Purpose**: Import boat configurations from MSSQL to MySQL

**Source**: `CSISTG.dbo.cfg_attr_mst`
**Target**: `warrantyparts_test.BoatConfigurationAttributes`

**Data Imported**:
- Performance Package selections
- Console, Fuel, Colors choices
- Trim, Furniture, Tables selections
- All boat configuration attributes

#### import_line_items.py
**Purpose**: Import order line items with pricing from MSSQL

**Source**: `CSISTG.dbo.coitem_mst`
**Target**: `warrantyparts_test.BoatOptions25_test` (or appropriate year table)

**Data Imported**:
- Item numbers, descriptions
- Quantities, prices
- Product categories (BS1, EN7, ACC)
- Invoice information

---

## Business Logic

### Dealer Margin Calculation

**Formula**:
```
Dealer Cost = MSRP × (1 - margin% / 100)
Dealer Savings = MSRP × (margin% / 100)
```

**Example** (NICHOLS MARINE - NORMAN, SV_23, 27% margin):
```
MSRP Components:
  Base Boat:      $25,895.00
  Engine:         $9,011.00
  Accessories:    $712.00
  ─────────────────────────
  Total MSRP:     $35,618.00

Dealer Cost (27% margin):
  Base Boat:      $25,895 × 0.73 = $18,903.35
  Engine:         $9,011 × 0.73 = $6,578.03
  Accessories:    $712 × 0.73 = $519.76
  ─────────────────────────
  Dealer Cost:    $26,001.14

Dealer Savings:   $35,618 - $26,001 = $9,617 (27%)
```

**Note**: The actual calculation uses 27% margins from warrantyparts.DealerMargins for this dealer.

### Freight & Prep Handling

**Production Table** (warrantyparts.DealerMargins):
- **Most dealers**: `0.00` (no discount)
- **~38 dealers**: Fixed dollar amounts (`$1500`, `$2500`, etc.)
- **Some dealers**: Percentages (0-100)

**CPQ API** (C_GD_DealerMargin):
- **All values**: Percentages only

**Conversion Challenge**:
```
Production: Q_FREIGHT = $1500 (dealer saves $1500)
CPQ needs: C_Freight = ??%

To convert: Need to know base freight cost
            $1500 / $base_freight × 100 = ??%
```

**Current Workaround**: Upload as 0% if value > 100

### Window Sticker Display Options

Dealers can choose what pricing to show customers:

1. **MSRP Only** - Just manufacturer suggested retail price
2. **Selling Price** - Dealer's retail price (may differ from MSRP)
3. **Sale & MSRP** - Show both (displays savings)
4. **No Pricing** - Show boat features only
5. **Special Pricing** - Custom override price with description

**Configuration**: Stored in web application state (not in MySQL)

**Flow**:
```
Dealer configures sticker in web portal
  ↓
Web app queries MySQL for boat data
  ↓
Web app applies display preferences
  ↓
Generates PDF/HTML window sticker
```

### EOS Backward Compatibility

**CPQ Models** (2025+):
- Data from: Models, ModelPricing, ModelPerformance tables
- MSRP from: ModelPricing table (from CPQ API)

**EOS Models** (pre-2025):
- Data from: SerialNumberMaster, Eos.perf_pkg_spec, Eos.standards_matrix_{year}
- MSRP from: BoatOptions{YY} table (calculated from line items)

**Series Name Handling**:
- EOS returns: `SV`, `S`
- DealerMargins columns: `SV_23_`, `S_23_`
- GetSeriesColumnPrefix() handles mapping

---

## Critical Findings

### Finding 1: Three Dealer Margin Tables (Not One!)

**Discovery**: System has THREE tables, each serving different purposes

| Table | Database | Rows | Purpose | Status |
|-------|----------|------|---------|--------|
| **DealerMargins** | warrantyparts | 2,334 | **PRODUCTION SOURCE** | ✅ Correct |
| DealerQuotes | warrantyparts_test | 422 | Test/deprecated | ❌ Do not use |
| DealerMargins | warrantyparts_test | 100→35,003 | CPQ import cache | ℹ️ Cache only |

**Action Taken**:
- Updated all systems to use `warrantyparts.DealerMargins`
- Created `GetDealerMarginsProduction()` procedure
- Fixed `upload_margin.py` to read from correct table

### Finding 2: CPQ API Has 35,003 Records (Not 100!)

**Discovery**: CPQ API has all the data, but load_cpq_data.py wasn't fetching it

**Before**:
```python
response = requests.get(DEALER_MARGIN_ENDPOINT, ...)
# Returned: 100 records (default page size)
```

**After**:
```python
response = requests.get(f"{DEALER_MARGIN_ENDPOINT}?$top=50000", ...)
# Returns: 35,003 records
```

**Data in CPQ**:
- 35,003 total records
- 2,334 unique dealers
- 15 series per dealer
- 83% have 27% placeholder (29,021 records)
- 17% have real margins (5,982 records)

### Finding 3: Mixed Freight/Prep Format

**Discovery**: Production table has BOTH dollar amounts AND percentages

**Breakdown**:
- **Most dealers**: `0.00` (no freight/prep discount)
- **38 dealers**: Dollar amounts up to `$5,707`
- **Some dealers**: Percentages (0-100)

**Problem**: Can't convert $ → % without base freight cost per series

**Impact**: 38 dealers will lose freight/prep discounts when uploaded to CPQ

### Finding 4: MSRP Comes from Two Sources

**For CPQ Models** (2025+):
- Source: ModelPricing table
- From: Infor CPQ OptionList API
- Example: Model 25QXFBWA = $103,726 MSRP

**For Actual Boats** (with serial numbers):
- Source: BoatOptions{YY} table
- From: MSSQL coitem_mst (imported)
- Calculated: BS1 + EN7 + ACC = Total MSRP
- Example: ETWP6278J324 = $25,895 + $9,011 + $712 = $35,618

### Finding 5: All CPQ Margins Are Disabled

**Discovery**: All 35,003 records in CPQ have `C_Enabled = false`

**Status**: Likely for testing/validation before enabling

**Impact**: CPQ system may not be using these margins yet

---

## Production Systems

### What's Working ✅

1. **Dealer Margin Lookup**
   - ✅ `GetDealerMarginsProduction()` procedure created
   - ✅ Queries `warrantyparts.DealerMargins` (2,334 dealers)
   - ✅ Handles dealer ID normalization
   - ✅ Maps series names correctly (SV → SV_23)

2. **Window Sticker Generation**
   - ✅ Generates stickers for both CPQ and EOS models
   - ✅ Calculates MSRP from BoatOptions
   - ✅ Shows dealer costs with margins
   - ✅ Displays standard features and options
   - ✅ Backward compatible with pre-2025 boats

3. **CPQ Data Import**
   - ✅ Imports model prices (283 models)
   - ✅ Imports performance data (281 models)
   - ✅ Imports standard features (282 models)
   - ✅ Fixed to import all 35,003 dealer margins

4. **MSSQL Integration**
   - ✅ Imports configuration attributes (cfg_attr_mst)
   - ✅ Imports line items with pricing (coitem_mst)
   - ✅ Populates BoatConfigurationAttributes table

### What Needs Attention ⚠️

1. **upload_margin.py**
   - ⚠️ ON HOLD: Freight/prep conversion issue
   - 38 dealers have $ amounts that can't be converted to %
   - Need: Base freight/prep costs per series OR accept 0% for these dealers

2. **Window Sticker Display Modes**
   - ⚠️ Currently shows both MSRP and dealer cost
   - Need: Implement display mode selection (MSRP only, Sale & MSRP, etc.)
   - Question: Where are display preferences stored?

3. **CPQ Margin Enablement**
   - ⚠️ All 35,003 records disabled (C_Enabled = false)
   - Question: When/how should these be enabled?

4. **Data Validation**
   - ⚠️ 83% of CPQ records still have 27% placeholder
   - Need: Run upload_margin.py to update with real margins

---

## Next Session Prep

### Focus: MSSQL colines and cfg_attributes

**Context for Next Session**:

We'll be working with the **MSSQL CSI/ERP system** to enhance the window sticker and quote generation capabilities.

#### Data Sources:

**1. coitem_mst (Customer Order Line Items)**
- Contains: Every line item sold on boat orders
- Includes: Item numbers, descriptions, quantities, prices
- Product categories: BS1, EN7, ACC, etc.
- Purpose: **THE source for MSRP calculations**
- Current status: Imported to BoatOptions{YY} tables

**2. cfg_attr_mst (Configuration Attributes)**
- Contains: Actual configuration choices made in CPQ
- Includes: Performance packages, colors, trim, furniture
- Purpose: Shows what customer selected
- Current status: Imported to BoatConfigurationAttributes table

#### Import Scripts Ready:

```python
# Import configuration attributes
python3 import_configuration_attributes.py

# Import line items with pricing
python3 import_line_items.py
```

#### Sample Data Already Available:

**BoatConfigurationAttributes** (2,323 records):
- Boat serial: ETWP6278J324
- Attributes: Performance Package, Console, Colors, etc.
- Links: ERP orders to web orders

**BoatOptions25_test**:
- Line items with MSRP breakdown
- Product categories (BS1, EN7, ACC)
- Used for MSRP calculation

#### What We'll Build:

Likely working on:
- Enhanced window sticker with configuration details
- Better MSRP breakdown showing all components
- Integration of configuration choices into quotes
- Comprehensive boat build/spec sheets

#### Key Files to Reference:

- `import_configuration_attributes.py` - Import logic
- `import_line_items.py` - Line item import
- `generate_window_sticker_with_pricing.py` - Current sticker generator
- `BoatConfigurationAttributes` table schema
- `BoatOptions{YY}` table structure

#### MSSQL Connection Info (Ready):

```python
SQL_SERVER = "MPL1STGSQL086.POLARISSTAGE.COM"
SQL_DATABASE = "CSISTG"
SQL_USERNAME = "svccsimarine"
SQL_PASSWORD = "CNKmoFxEsXs0D9egZQXH"
```

---

## Quick Reference

### Database Connections

**Production MySQL**:
```python
host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com'
user='awsmaster'
password='VWvHG9vfG23g7gD'
database='warrantyparts'  # or 'warrantyparts_test'
```

**MSSQL Server**:
```python
server='MPL1STGSQL086.POLARISSTAGE.COM'
database='CSISTG'
user='svccsimarine'
password='CNKmoFxEsXs0D9egZQXH'
```

### Key Queries

**Get dealer margins**:
```sql
CALL GetDealerMarginsProduction('333836', 'SV_23');
```

**Calculate MSRP**:
```sql
SELECT
    SUM(CASE WHEN ItemMasterProdCat='BS1' THEN ExtSalesAmount END) as base_boat,
    SUM(CASE WHEN ItemMasterProdCat='EN7' THEN ExtSalesAmount END) as engine,
    SUM(CASE WHEN ItemMasterProdCat='ACC' THEN ExtSalesAmount END) as accessories
FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = 'ETWP6278J324';
```

**Get boat configuration**:
```sql
SELECT attr_name, attr_value
FROM BoatConfigurationAttributes
WHERE boat_serial_no = 'ETWP6278J324'
ORDER BY attr_name;
```

### Key Scripts

**Generate window sticker**:
```bash
python3 generate_window_sticker_with_pricing.py 20SVFSR 333836 2024 ETWP6278J324
```

**Import CPQ data** (nightly):
```bash
python3 load_cpq_data.py
```

**Import MSSQL data**:
```bash
python3 import_configuration_attributes.py
python3 import_line_items.py
```

---

## Summary

This system integrates data from:
- **MySQL Production** (warrantyparts) - Dealer margins, historical sales
- **MySQL Test/CPQ** (warrantyparts_test) - CPQ models, cache
- **MSSQL ERP** (CSISTG) - Order line items, configurations
- **Infor CPQ APIs** - Model catalog, margins, features

Key achievements:
- ✅ Identified production source: `warrantyparts.DealerMargins` (2,334 dealers)
- ✅ Fixed CPQ import: Now fetches all 35,003 margin records
- ✅ Created production query: `GetDealerMarginsProduction()`
- ✅ Window stickers work with both CPQ and EOS models
- ✅ MSRP calculation from BoatOptions data
- ✅ Dealer cost calculation with margins
- ✅ Backward compatibility for pre-2025 boats

Outstanding items:
- ⚠️ Freight/prep conversion ($ to %)
- ⚠️ Window sticker display mode selection
- ⚠️ CPQ margin enablement strategy
- ⚠️ Update CPQ with real margins (83% placeholder)

**Ready for next session on MSSQL colines and cfg_attributes integration!**

---

**Document Version**: 1.0 (Master Context)
**Author**: Claude Code
**Date**: January 28, 2026
**Status**: Complete System Documentation
**Next Session**: MSSQL Line Items & Configuration Attributes
