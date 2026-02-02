# warrantyparts_test Database Analysis

**Date**: January 28, 2026
**Database**: warrantyparts_test @ ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com

---

## Overview

The `warrantyparts_test` database contains a **hybrid system** combining:
1. **New CPQ Infrastructure** (2025+ models) - Normalized, API-driven
2. **Legacy Production Tables** (Historical data) - Wide tables, ERP-driven

**Total Tables**: 86 tables

---

## Table Categories

### ✅ CPQ Infrastructure Tables (NEW)

These tables were created for the Infor CPQ integration and store 2025+ model data.

#### Core CPQ Tables
| Table | Rows | Purpose |
|-------|------|---------|
| `Series` | ? | Boat series definitions (Q, QX, R, LXS, M, S, etc.) |
| `Models` | ? | Central catalog of boat models |
| `ModelPricing` | ? | MSRP pricing with effective date tracking |
| `ModelPerformance` | ? | Performance specs per model × performance package |
| `ModelStandardFeatures` | ? | Junction table: models ↔ standard features |
| `PerformancePackages` | ? | Performance package definitions |
| `StandardFeatures` | ? | Master list of standard features |
| `Dealers` | ? | Dealer information (from CPQ API) |
| `DealerMargins` | ? | Margin percentages per dealer × series |

#### CPQ Views
- `CurrentModelPricing` - Active pricing for all models
- `ModelWithCurrentPrice` - Complete model info with pricing
- `ModelStandardFeaturesList` - Features per model
- `ModelPerformanceDetails` - Performance specs per model
- `CurrentDealerMargins` - Active margins per dealer-series
- `DealerMarginsSummary` - Margin summary with examples
- `ActiveDealersWithMargins` - Dealers and configured series

**Characteristics**:
- ✅ Normalized schema (proper foreign keys)
- ✅ Effective date tracking (historical data)
- ✅ Data loaded from Infor CPQ APIs
- ✅ Clean, modern design
- ⚠️ Only contains 2025+ models

---

### 📊 Legacy Production Tables (NON-CPQ)

These tables existed before CPQ and contain historical operational data.

#### 1. DealerQuotes (422 rows) ⭐ IMPORTANT

**Purpose**: Dealer margin/quote configuration (PRODUCTION SYSTEM)

**Structure**: Wide table format - one column per series
```
Columns (96 total):
- DealerID (int)
- Dealership (varchar)
- Q_BASE_BOAT, Q_ENGINE, Q_OPTIONS, Q_FREIGHT, Q_PREP, Q_VOL_DISC
- QX_BASE_BOAT, QX_ENGINE, QX_OPTIONS, QX_FREIGHT, QX_PREP, QX_VOL_DISC
- QXS_BASE_BOAT, QXS_ENGINE, QXS_OPTIONS, QXS_FREIGHT, QXS_PREP, QXS_VOL_DISC
- R_BASE_BOAT, R_ENGINE, R_OPTIONS, R_FREIGHT, R_PREP, R_VOL_DISC
- RX_BASE_BOAT, RX_ENGINE, RX_OPTIONS, RX_FREIGHT, RX_PREP, RX_VOL_DISC
- RT_BASE_BOAT, RT_ENGINE, RT_OPTIONS, RT_FREIGHT, RT_PREP, RT_VOL_DISC
- G_BASE_BOAT, G_ENGINE, G_OPTIONS, G_FREIGHT, G_PREP, G_VOL_DISC
- S_BASE_BOAT, S_ENGINE, S_OPTIONS, S_FREIGHT, S_PREP, S_VOL_DISC
- SX_BASE_BOAT, SX_ENGINE, SX_OPTIONS, SX_FREIGHT, SX_PREP, SX_VOL_DISC
- L_BASE_BOAT, L_ENGINE, L_OPTIONS, L_FREIGHT, L_PREP, L_VOL_DISC
- LX_BASE_BOAT, LX_ENGINE, LX_OPTIONS, LX_FREIGHT, LX_PREP, LX_VOL_DISC
- LT_BASE_BOAT, LT_ENGINE, LT_OPTIONS, LT_FREIGHT, LT_PREP, LT_VOL_DISC
- S_23_BASE_BOAT, S_23_ENGINE, S_23_OPTIONS, S_23_FREIGHT, S_23_PREP, S_23_VOL_DISC
- SV_23_BASE_BOAT, SV_23_ENGINE, SV_23_OPTIONS, SV_23_FREIGHT, SV_23_PREP, SV_23_VOL_DISC
- M_BASE_BOAT, M_ENGINE, M_OPTIONS, M_FREIGHT, M_PREP, M_VOL_DISC
```

**Sample Data**:
```
DealerID: 5
Dealership: SUSAN BUFF
Q_BASE_BOAT: 28.00%
Q_ENGINE: 25.00%
Q_OPTIONS: 25.00%
Q_FREIGHT: $850.00 (fixed amount, not percentage)
Q_PREP: $2000.00 (fixed amount, not percentage)
```

**Key Insights**:
- ⚠️ **FREIGHT and PREP are FIXED DOLLAR AMOUNTS, not percentages**
- ⚠️ DealerID is `int` here vs `VARCHAR(20)` in CPQ Dealers table
- ✅ More comprehensive than CPQ DealerMargins (422 dealers vs fewer in CPQ)
- ✅ Contains all active dealer configurations
- 🔑 **This is the production table** used for actual quotes

**Comparison to CPQ DealerMargins**:
| Feature | DealerQuotes (Legacy) | DealerMargins (CPQ) |
|---------|----------------------|---------------------|
| Structure | Wide (96 columns) | Narrow (normalized) |
| DealerID | int | VARCHAR(20) |
| Freight/Prep | Fixed $ amounts | Percentages |
| Series Coverage | 16 series | Variable |
| Dealers | 422 | Fewer (CPQ only) |
| Status | PRODUCTION | New/Testing |

---

#### 2. BoatConfigurationAttributes (2,323 rows)

**Purpose**: Stores boat configuration selections from CPQ

**Schema**:
```sql
id                    INT PRIMARY KEY
boat_serial_no        VARCHAR(15)
boat_model_no         VARCHAR(14)
erp_order_no          VARCHAR(30)
web_order_no          VARCHAR(30)
config_id             VARCHAR(50)     -- CPQ configuration ID
attr_name             VARCHAR(100)    -- Configuration attribute name
attr_value            VARCHAR(255)    -- Selected value
cfg_value             VARCHAR(255)    -- Configuration value code
comp_id               VARCHAR(50)     -- Component ID
series                VARCHAR(5)
invoice_no            VARCHAR(30)
invoice_date          INT
created_at            TIMESTAMP
updated_at            TIMESTAMP
```

**Sample Data**:
```
boat_model_no:  26MFB
erp_order_no:   SO00935955
web_order_no:   SOBHO00555
config_id:      BENN0000000000000000000000000001
attr_name:      "Additional Display"
attr_value:     "No Additional Display"
cfg_value:      "NoAdditionalDisplay"
series:         M
```

**Use Case**:
- Tracks every configuration choice made in CPQ
- Links web orders to ERP orders
- One row per attribute selection
- Multiple rows per boat (all configuration choices)

---

#### 3. SerialNumberMaster (62,781 rows) ⭐ CRITICAL

**Purpose**: Master record of all boats produced

**Schema**:
```sql
SN_MY                  INT             -- Serial Number Model Year
Boat_SerialNo          VARCHAR(20) PK  -- HIN (Hull Identification Number)
BoatItemNo             VARCHAR(255)    -- Model number (e.g., 25QXFBWA)
Series                 VARCHAR(10)
BoatDesc1              VARCHAR(255)    -- Description
BoatDesc2              VARCHAR(255)    -- Description 2
SerialModelYear        VARCHAR(4)      -- Model year
ERP_OrderNo            VARCHAR(10)
ProdNo                 INT             -- Production number
OrigOrderType          VARCHAR(1)      -- 'O' = Order, 'I' = Invoice
InvoiceNo              VARCHAR(10)
ApplyToNo              VARCHAR(10)
InvoiceDateYYYYMMDD    VARCHAR(10)
DealerNumber           VARCHAR(20)
DealerName             VARCHAR(255)
DealerCity             VARCHAR(30)
DealerState            VARCHAR(20)
DealerZip              VARCHAR(10)
DealerCountry          VARCHAR(20)
ParentRepName          VARCHAR(255)
ColorPackage           VARCHAR(50)
PanelColor             VARCHAR(30)
AccentPanel            VARCHAR(30)
TrimAccent             VARCHAR(30)
BaseVinyl              VARCHAR(30)
WebOrderNo             VARCHAR(20)
Presold                VARCHAR(1)
Active                 INT
SN_ID                  INT
Quantity               INT
```

**Use Case**:
- **Master boat registry** - Every boat ever produced
- Links HIN to model, dealer, invoice, colors
- Used for warranty lookups, registrations
- Critical for backward compatibility (pre-CPQ boats)

---

#### 4. EngineSerialNoMaster (53,244 rows)

**Purpose**: Tracks engine serial numbers for boats

**Schema**:
```sql
SN_MY              INT
Boat_SerialNo      VARCHAR(20)     -- Links to SerialNumberMaster
BoatItemNo         VARCHAR(255)
ERP_OrderNo        INT
OrigOrderType      VARCHAR(20)
EngineItemNo       VARCHAR(255)    -- Engine part number
EngineSerialNo     VARCHAR(255)    -- Actual engine serial
EngineBrand        VARCHAR(255)    -- YAMAHA, MERCURY, etc.
EngineDesc1        VARCHAR(255)    -- "YAMAHA 200 HP 4S 25 IN 4 CYL"
SN_ID              INT
Active             INT
```

**Sample Data**:
```
Boat_SerialNo:   ETWC7809F516
EngineItemNo:    F200XBDE
EngineSerialNo:  6DAX 1014893
EngineBrand:     YAMAHA ENGINES
EngineDesc1:     YAMAHA 200 HP 4S 25 IN 4 CYL
```

**Use Case**:
- Engine warranty tracking
- Recall management
- Service history
- Links boats to engines

---

#### 5. DealerAddr (2,086 rows)

**Purpose**: Dealer address records (multiple addresses per dealer)

**Schema**:
```sql
Cust_Num        VARCHAR(20)     -- Customer/Dealer number
Cust_Seq        VARCHAR(5)      -- Sequence (0 = default, 1+ = additional)
Addr_Name       VARCHAR(255)
City            VARCHAR(255)
State           VARCHAR(255)
Zip             VARCHAR(255)
County          VARCHAR(255)
Country         VARCHAR(255)
Addr1           VARCHAR(255)
Addr2           VARCHAR(255)
Addr3           VARCHAR(255)
addr4           VARCHAR(255)
isDefault       TINYINT         -- 1 = default address
```

**Sample Data**:
```
Cust_Num:  "      1"
Cust_Seq:  "0"
Addr_Name: "JASON CALL"
City:      "GRANGER"
State:     "IN"
isDefault: 1
```

**Use Case**:
- Multiple shipping addresses per dealer
- Default vs alternate locations
- Shipping documentation

---

#### 6. options_matrix_2016 (81,403 rows) ⭐ IMPORTANT

**Purpose**: Catalog of available options per model (2016 model year)

**Schema**:
```sql
SERIES              VARCHAR(2)      -- G, Q, R, S, L, etc.
MODEL               VARCHAR(15)     -- Model number
PART                VARCHAR(50)     -- Part number for option
CATEGORY            VARCHAR(30)     -- Category (Amenities, Performance, etc.)
OPT_NAME            VARCHAR(1000)   -- Option description
PROD_TITLE          VARCHAR(255)    -- Product title
QTY                 VARCHAR(5)      -- Quantity
MORE_OPTION         INT             -- 0 or 1
VISIBILITY_LEVEL    INT             -- Who can see it
REQ_BY_MODEL        INT             -- Required by model
INC_BY_MODEL        INT             -- Included by model
COMPAT_PERF_PKG     VARCHAR(30)     -- Compatible performance packages
MODEL_DEFAULT       INT             -- Is default
UPSELL              INT             -- Is upsell
REQ_CUSTOM_DRAW     INT             -- Requires custom drawing
CUST_DRAW_NO        VARCHAR(100)    -- Drawing number
OBSOLETE            INT             -- Is obsolete
```

**Sample Data**:
```
SERIES:    G
MODEL:     2874GCWDF
PART:      900068
CATEGORY:  Performance Add-ons
OPT_NAME:  UnderDeck Wave Shield (28)
```

**Use Case**:
- Legacy options catalog (2016 models)
- Compatibility checking
- Option availability per model
- ⚠️ Only 2016 - need separate tables for other years

---

#### 7. modelyear (3 rows)

**Purpose**: Model year date ranges

**Schema**:
```sql
year        INT PRIMARY KEY
start_date  VARCHAR(10)     -- MM/DD/YYYY
end_date    VARCHAR(10)     -- MM/DD/YYYY
```

**Sample Data**:
```
2014: 8/5/2013  - 8/3/2014
2015: 8/4/2014  - 8/2/2015
2016: 8/3/2015  - 8/7/2016
```

**Use Case**:
- Determine which model year a date falls into
- Production planning
- Catalog transitions

---

#### 8. BuildLoc (44,876 rows)

**Purpose**: Build location assignments per model/series

**Schema**:
```sql
ProdNo      VARCHAR(10) PK  -- Production number
Model       VARCHAR(20)     -- Model number
Series      VARCHAR(3)      -- Series code
BuildLoc    VARCHAR(5)      -- Build location code (S = ?)
```

**Sample Data**:
```
ProdNo:   177460
Model:    30QSRWAX2
Series:   Q
BuildLoc: S
```

**Use Case**:
- Production facility assignments
- Manufacturing tracking
- Capacity planning

---

#### 9. BrandMaster (6 rows)

**Purpose**: Brand definitions

**Schema**:
```sql
BrandID              INT
BrandName            VARCHAR(10)     -- Azure, Sedona, Bennington
BrandAbbreviation    VARCHAR(3)      -- AZU, SED, BEN
BrandClaimThreshold  INT             -- Warranty claim threshold
BrandDeleteDate      VARCHAR(15)
```

**Sample Data**:
```
1: Azure       (AZU) - Threshold: $400
2: Sedona      (SED) - Threshold: $400
3: Bennington  (BEN) - Threshold: $400
```

**Use Case**:
- Multi-brand support
- Warranty rules
- Brand filtering

---

#### 10. ERPOrderWebOrderMatrix (3,493 rows)

**Purpose**: Links web orders (CPQ) to ERP orders

**Schema**:
```sql
ERP_OrderNo     INT
WebOrderNo      INT
LineNo          INT
count           INT
```

**Sample Data**:
```
ERP_OrderNo:  357177
WebOrderNo:   120372
LineNo:       1
```

**Use Case**:
- Critical bridge between CPQ and ERP
- Order tracking
- Fulfillment status

---

### 📋 Additional Legacy Tables

#### Boat Options Tables
- `BoatOptions05_07` - Options sold 2005-2007
- `BoatOptions08_10` - Options sold 2008-2010
- `BoatOptions11_14` - Options sold 2011-2014
- `BoatOptions15` - Options sold 2015
- `BoatOptions16` - Options sold 2016
- `BoatOptions24_6252025` - Options sold 2024 (thru 6/25/2025)
- `BoatOptions25_test` - Options sold 2025 (test)
- `BoatOptions99_04` - Options sold 1999-2004

**Purpose**: Line items of what was sold with each boat
**Key for**: MSRP calculation, included options, window stickers

#### Serial Number Tables
- `SerialNumberMaster` - Main table (62,781 rows)
- `SerialNumberMaster_6252025` - Snapshot 6/25/2025
- `SerialNumberMaster_98_06` - Historical 1998-2006
- `SerialNumberMaster_Azure_Southwind_Rainstorm` - Other brands
- `SerialNumberMaster_test` - Test data
- `SerialNumberRegistrationStatus` - Registration status
- `SerialNumberRegistrationStatus_6252025` - Snapshot
- `SerialNumberRegistrationStatus_test` - Test

#### Owner/Registration Tables
- `OwnerRegistrations` - Owner registration data
- `OwnerRegistrations_6` - ?
- `OwnerRegistrations_test` - Test
- `OwnerRegistrations_test2` - Test
- `club_bennington_registrations` - Club registrations

#### Warranty Tables
- `WarrantyClaimOrderHeaders` - Warranty claim headers
- `WarrantyClaimOrderLineItems` - Warranty claim line items
- `WarrantyClaimAttachments_ToHeaders` - Attachments
- `WarrantyClaimDateAndStatusTracker` - Status tracking
- `WarrantyClaimHeader_StateChangeStatusTracker` - State changes
- `WarrantyClaimLineItemAttachments` - Line item attachments
- `WarrantyClaimsLastStatus` - Last status per claim
- `RGAs` - Return Goods Authorizations
- `RGA_StateChangeStatusTracker` - RGA status tracking

#### Parts Tables
- `PartsList` - Parts catalog
- `PartsOrderHeader` - Parts order headers
- `PartsOrderLines` - Parts order line items
- `PartsOrderComments` - Comments on orders
- `PartsOrderLineItemAttachments` - Attachments
- `PartsOrderHeader_StateChangeStatusTracker` - Status tracking
- `PartsOrderLine_StateChangeStatusTracker` - Line status
- `PartsOrdersLastStatus` - Last status per order
- `parts_order_public_statuses` - Public status codes
- `PartsInvoicedSalesDollarInfo` - Invoice data

#### ERP/Order Tables
- `ERPOrderComments` - Comments on orders
- `ERPOrderComments11_15` - 2011-2015 comments
- `ERPOrderCommentsThru2010` - Pre-2011 comments
- `ERPOrderWebOrderMatrix` - Web ↔ ERP mapping
- `erp2` - ? (ERP related)
- `erp_updates` - Update tracking

#### Inventory Tables
- `FieldInventory_AllBoats` - Field inventory
- `Field_Inventory_Options_98_06` - Historical options
- `Backorders` - Backorder tracking

#### Shipping Tables
- `ShipmentMethodMaster` - Shipping methods
- `ShipmentTrackingInfo` - Tracking information
- `ShipmentTrackingInfo11_6_2015` - Historical
- `ShipmentTrackingInfoHistory` - History

#### Recall Tables
- `Recall_ID_Master` - Recall definitions
- `RecallsBySerialNumber` - Recalls by boat

#### Brochure/Marketing Tables
- `Brochure_Request` - Brochure requests
- `email_accounting_histories` - Email history

#### Master Data Tables
- `SalesRepMaster` - Sales rep information
- `customertype` - Customer type codes
- `artermscodes` - AR terms codes
- `dealer_labor_misc` - Dealer labor/misc charges

#### Miscellaneous Tables
- `Boat_Flag_File` - Boat flags/markers
- `deleted_boats` - Soft-deleted boats
- `test_ship_file` - Test shipping data
- `boat_performance_specs` - Performance specs (0 rows - deprecated?)

---

## Key Findings

### 🔴 Critical Discovery: DealerQuotes vs DealerMargins

There are **TWO dealer margin systems**:

1. **DealerQuotes** (Legacy - PRODUCTION)
   - 422 dealers
   - Freight/Prep are **fixed dollar amounts**
   - DealerID is `int`
   - Wide table (16 series × 6 fields = 96 columns)
   - **Currently in use for production quotes**

2. **DealerMargins** (CPQ - NEW)
   - Fewer dealers (CPQ only)
   - Freight/Prep are **percentages**
   - DealerID is `VARCHAR(20)`
   - Normalized structure
   - Effective date tracking
   - **New system, may not be fully populated**

**Implication**:
- Window stickers/quotes should use **DealerQuotes** for production
- **DealerMargins** is for future CPQ integration
- Need to handle both systems during transition

---

### 🔴 Data Sources by Use Case

#### For Window Stickers (2025+ Models)
```
CPQ Path:
- Models → model info
- ModelPricing → MSRP
- ModelPerformance → performance specs
- ModelStandardFeatures → standard features
- BoatOptions25_test → included options (ACC items)
- DealerQuotes → dealer margins (PRODUCTION)
```

#### For Window Stickers (Pre-2025 Models)
```
EOS Path:
- SerialNumberMaster → model info
- Eos.perf_pkg_spec → performance specs
- Eos.standards_matrix_YYYY → standard features
- BoatOptionsYY → included options (ACC items)
- DealerQuotes → dealer margins (PRODUCTION)
```

#### For Dealer Quotes
```
- DealerQuotes → margins (BASE_BOAT, ENGINE, OPTIONS %, FREIGHT $, PREP $)
- BoatOptionsYY → MSRP calculation
- Models/Pricing (if CPQ) or SerialNumberMaster (if legacy)
```

#### For Order Tracking
```
- ERPOrderWebOrderMatrix → Web order → ERP order mapping
- BoatConfigurationAttributes → CPQ selections
- SerialNumberMaster → Production status
```

#### For Warranty Claims
```
- SerialNumberMaster → Boat info
- EngineSerialNoMaster → Engine info
- WarrantyClaimOrderHeaders → Claim details
- WarrantyClaimOrderLineItems → Claim line items
```

---

## Recommendations

### 1. Use DealerQuotes for Production
The CPQ `DealerMargins` table may not be fully populated. For production window stickers and quotes:
- **Use `DealerQuotes` table**
- Note: Freight/Prep are dollar amounts, not percentages
- DealerID is `int`, may need conversion

### 2. Handle FREIGHT/PREP Correctly
```sql
-- WRONG (treating as percentage):
dealer_cost = freight * (1 - freight_margin / 100)

-- CORRECT (fixed dollar amount):
dealer_cost = freight - freight_fixed_amount
```

### 3. Normalize Access
Create views/procedures that:
- Check CPQ DealerMargins first
- Fall back to DealerQuotes if not found
- Handle int vs VARCHAR(20) DealerID
- Handle percentage vs fixed dollar amounts

### 4. BoatOptions Table Selection
```python
# Get correct BoatOptions table by year
year_suffix = str(year)[-2:]  # 2024 → "24"
table_name = f"BoatOptions{year_suffix}"

# Special cases:
# - BoatOptions05_07 (2005-2007)
# - BoatOptions08_10 (2008-2010)
# - BoatOptions11_14 (2011-2014)
# - BoatOptions15 (2015 only)
# - BoatOptions16 (2016 only)
# - BoatOptions24_6252025 (2024 through 6/25/2025)
# - BoatOptions25_test (2025 test data)
```

### 5. Migration Path
```
Phase 1 (Current): Hybrid system
  - Use CPQ for 2025+ models (if data exists)
  - Use EOS/Legacy for pre-2025
  - Use DealerQuotes for ALL margins

Phase 2 (Future): Populate CPQ
  - Backfill DealerMargins from DealerQuotes
  - Convert fixed $ to % (may need business rules)
  - Migrate dealer info to Dealers table

Phase 3 (Final): Full CPQ
  - All margins in DealerMargins
  - DealerQuotes becomes read-only/deprecated
  - Single normalized system
```

---

## Database Size Summary

| Category | Tables | Est. Rows |
|----------|--------|-----------|
| CPQ Infrastructure | 16 | Unknown |
| Boat/Serial Data | 10 | 62,781+ |
| Options/Configuration | 10 | 80,000+ |
| Dealer Data | 3 | 2,500+ |
| Warranty/RGA | 7 | Unknown |
| Parts Orders | 9 | Unknown |
| ERP/Orders | 5 | Unknown |
| Registrations | 7 | Unknown |
| Shipping | 4 | Unknown |
| Master Data | 10 | Small |
| Miscellaneous | 5 | Small |
| **TOTAL** | **86** | **200,000+** |

---

## Next Steps

1. ✅ **Documented all non-CPQ tables**
2. ⚠️ **Critical: Update window sticker to use DealerQuotes**
3. ⚠️ **Handle FREIGHT/PREP as fixed amounts, not percentages**
4. ⚠️ **Create unified dealer margin lookup procedure**
5. 🔄 Test with real dealer data
6. 🔄 Verify MSRP calculations with DealerQuotes margins
7. 🔄 Document migration plan from DealerQuotes → DealerMargins

---

**Document Version**: 1.0
**Author**: Claude Code
**Last Updated**: 2026-01-28
