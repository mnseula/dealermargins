# Bennington Dealer Margins - System Context & Documentation

**Last Updated:** 2026-01-21
**Repository:** github.com:mnseula/dealermargins.git

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Data Model & Relationships](#data-model--relationships)
3. [API Endpoints](#api-endpoints)
4. [Scripts & Tools](#scripts--tools)
5. [Database Schema](#database-schema)
6. [Pricing Calculation Flow](#pricing-calculation-flow)

---

## System Overview

This system manages dealer margins, model pricing, and boat specifications for Bennington Marine's CPQ (Configure, Price, Quote) system. It integrates data from multiple sources:

- **MySQL Database** - Stores dealer-specific margin percentages by series
- **Infor CPQ APIs** - Provides model data, pricing, performance specs, and standard features
- **Python Scripts** - Automates data fetching, transformation, and synchronization

---

## Data Model & Relationships

### Hierarchy
```
Dealers (MySQL)
  └─ Series-Level Margins (Q, QX, R, RX, LXS, M, S, etc.)
       └─ Individual Models (API)
            ├─ MSRP Pricing (OptionList API)
            ├─ Performance Data (Matrix API)
            └─ Standard Features (Matrix API)
```

### Example Flow
**Quote for Model 24LXSFB to ABC Marine (Dealer ID: 12345):**

1. **Get Series Margins** (MySQL `DealerMargins` table)
   - Dealer 12345 → LXS series margins
   - `LXS_BASE_BOAT = 15%`
   - `LXS_ENGINE = 10%`
   - `LXS_OPTIONS = 12%`
   - `LXS_FREIGHT = 8%`
   - `LXS_PREP = 5%`
   - `LXS_VOL_DISC = 2%`

2. **Get Model MSRP** (OptionList API)
   - Model: 24LXSFB
   - MSRP: $49,046

3. **Get Performance Specs** (Performance Matrix API)
   - MaxHP: 250
   - NoOfTubes: 3
   - HullWeight: 3,498 lbs
   - PontoonGauge: 0.1
   - FuelCapacity: "34 Gal. - 51 Gal."

4. **Get Standard Features** (Model Standards Matrix API)
   - 176 standard features
   - "Non-Elevated Fiberglass Console" = "S" (Standard)
   - "Console Courtesy Light" = "S" (Standard)
   - etc.

5. **Calculate Dealer Cost**
   - Dealer Cost = MSRP × (1 - Margin%)
   - Example: $49,046 × (1 - 0.15) = $41,689.10

---

## API Endpoints

### 1. OptionList API (Model Catalog & MSRP)

**Environment:** PRD (Production)
**Endpoint:**
```
https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/DataImport/QA2FNBZCKUAUH7QB_PRD/v1/OptionLists/{OPTION_LIST_ID}/values
```

**Option List ID:** `bb38d84e-6493-40c7-b282-9cb9c0df26ae`

**Purpose:** Fetches all boat models with MSRP pricing and metadata

**Response Structure:**
```json
{
  "result": [
    {
      "value": "24LXSFB",
      "visible": true,
      "customProperties": {
        "Series": "LXS",
        "ParentSeries": "L",
        "Price": 49046,
        "Floorplan": "FB",
        "FloorplanDesc": "Fastback",
        "Length": "24",
        "Seats": 15,
        "LOA": 26.25,
        "LOAStr": "26'-3\"",
        "BeamLength": 8.5,
        "BeamStr": "8'-6\"",
        ...
      }
    }
  ],
  "pageInfo": {
    "currentPage": 1,
    "totalPages": 1,
    "totalItems": 283
  }
}
```

**Key Fields:**
- `value` - Model ID (e.g., "24LXSFB")
- `customProperties.Series` - Series code (e.g., "LXS")
- `customProperties.Price` - MSRP
- `visible` - Whether model is active

**Authentication:** OAuth 2.0 (see credentials in scripts)

---

### 2. Performance Data Matrix API

**Environment:** TRN (Training/Test)
**Endpoint Pattern:**
```
https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/{SERIES}_PerformanceData_{YEAR}/values
```

**Example:**
```
https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/LXS_PerformanceData_2026/values
```

**Purpose:** Provides technical specifications for each model in a series

**Response Structure:**
```json
{
  "result": {
    "totalDetailsCount": 72,
    "details": [
      {
        "ExternalId": null,
        "model": "24LXSFB",
        "perfPack": "SPS+_22",
        "MaxHP": 250.0,
        "NoOfTubes": 3.0,
        "PersonCapacity": "12 People",
        "HullWeight": 3498.0,
        "PontoonGauge": 0.1,
        "Transom": "25",
        "TubeHeight": "30.8\"",
        "TubeCentertoCenter": "77\"",
        "MaxWidth": "103\"",
        "FuelCapacity": "34 Gal. - 51 Gal."
      }
    ]
  },
  "pageInfo": {
    "currentPage": 1,
    "totalPages": 1,
    "totalItems": 72
  }
}
```

**Data Format:** Long format (one row per model × performance package combination)

**Series Available:**
- LXS (72 records)
- S (212 records)
- M (193 records)
- R (169 records)
- QX (138 records)
- RX (132 records)
- Q (124 records)
- RT (11 records)
- M1 (14 records)
- S1 (12 records)
- LT (6 records)

---

### 3. Model Standards Matrix API

**Environment:** TRN (Training/Test)
**Endpoint Pattern:**
```
https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/{SERIES}_ModelStandards_{YEAR}/values
```

**Example:**
```
https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/LXS_ModelStandards_2026/values
```

**Purpose:** Lists standard features for each model (what's included in base price)

**Response Structure:**
```json
{
  "result": {
    "totalDetailsCount": 176,
    "details": [
      {
        "ExternalId": null,
        "Sort": 1.0,
        "Area": "Console Features",
        "Description": "Non-Elevated Fiberglass Console",
        "22LXSSB": "S",
        "23LXSFB": "S",
        "23LXSSB": "S",
        "24LXSFB": "S",
        "24LXSFBA": "S",
        "24LXSFBC": "S",
        "24LXSSB": "S",
        "24LXSSBA": "S",
        "26LXSFB": "S",
        "26LXSFBA": "S",
        "26LXSFBC": "S",
        "26LXSSB": "S",
        "26LXSSBA": "S"
      }
    ]
  }
}
```

**Data Format:** Wide format (features as rows, models as columns)

**Values:**
- `"S"` = Standard feature (included)
- `""` = Not applicable or not standard

**Series Available:** All 11 series (LXS, S, M, R, QX, RX, Q, RT, LT, M1, S1)

---

### 4. Dealer Margin API (CPQ Entity)

**Environment:** TRN (Training/Test)
**Endpoint:**
```
https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities/C_GD_DealerMargin
```

**Purpose:** Sync dealer margins TO CPQ system (write/update)

**Methods:**
- GET: Query existing margins with filters
- POST: Create new margin records
- PUT: Update existing margin records

**Query Example:**
```
GET {ENDPOINT}?$filter=C_DealerId eq '12345' and C_Series eq 'LXS'
```

**Payload Format (Long):**
```json
{
  "C_DealerId": "12345",
  "C_DealerName": "ABC Marine",
  "C_Series": "LXS",
  "C_Enabled": true,
  "C_BaseBoat": 15,
  "C_Engine": 10,
  "C_Options": 12,
  "C_Freight": 8,
  "C_Prep": 5,
  "C_Volume": 2
}
```

---

## Scripts & Tools

### Data Fetching Scripts

#### 1. `fetch_model_prices.py`
**Purpose:** Fetch MSRP pricing for all models
**Source:** OptionList API (PRD)
**Output:**
- `model_prices/model_prices.csv`
- `model_prices/model_prices.json`

**Run:**
```bash
python3 fetch_model_prices.py
```

**Features:**
- Extracts 283 models with MSRP
- Pricing analysis by series
- Both CSV and JSON output

---

#### 2. `fetch_all_performance_data.py`
**Purpose:** Fetch performance specifications for all series
**Source:** Performance Matrix API (TRN)
**Output:**
- `performance_data/{SERIES}_PerformanceData_2026.json` (per series)
- `performance_data/fetch_summary_2026.json`

**Run:**
```bash
python3 fetch_all_performance_data.py
```

**Features:**
- Dynamically discovers series from OptionList API
- Fetches performance matrix for each series
- 1,083 total performance records across 11 series
- Automatic retry logic and error handling

---

#### 3. `fetch_all_model_standards.py`
**Purpose:** Fetch standard features for all series
**Source:** Model Standards Matrix API (TRN)
**Output:**
- `model_standards_data/{SERIES}_ModelStandards_2026.json` (per series)
- `model_standards_data/fetch_summary_2026.json`

**Run:**
```bash
python3 fetch_all_model_standards.py
```

**Features:**
- Dynamically discovers series from OptionList API
- Fetches standards matrix for each series
- 1,876 total standard feature records across 11 series
- Wide format (features × models)

---

### Data Upload Scripts

#### 4. `upload_margin.py`
**Purpose:** Upload dealer margins from MySQL to CPQ API
**Source:** MySQL `warrantyparts.DealerMargins` table
**Target:** CPQ Dealer Margin Entity (TRN)

**Run:**
```bash
python3 upload_margin.py [--dry-run]
```

**Features:**
- Reads wide format from MySQL
- Transforms to long format for API
- Handles CREATE (POST) and UPDATE (PUT) automatically
- Concurrent uploads with 8 workers
- Retry logic with automatic token refresh
- Progress bar with tqdm

**Flow:**
1. Connect to MySQL and fetch dealer margins (wide format)
2. Transform to long format (one record per dealer × series)
3. For each record:
   - Query API to check if record exists
   - POST to create new or PUT to update existing
4. Report success/failure counts

---

#### 5. `margins.py`
**Purpose:** Download dealer margins from CPQ API to CSV
**Source:** CPQ Dealer Margin Entity (TRN)
**Output:** `dealer_quotes.csv`

**Run:**
```bash
python3 margins.py
```

**Features:**
- Fetches margins from CPQ API (series by series)
- Converts from long to wide format
- Creates Excel-compatible CSV
- Concurrent downloads with 8 workers
- Pagination handling

**Note:** This is the reverse of `upload_margin.py`

---

#### 6. `optimizeBoatCost.py`
**Purpose:** Calculate boat costs using Selenium automation
**Source:** CPQ Configurator Simulator (web UI)
**Output:** `boat_costs.csv`

**Run:**
```bash
python3 optimizeBoatCost.py [--use-api-models] [--upload-to-api]
```

**Features:**
- Selenium-based browser automation
- Fetches models from OptionList API
- Processes each model through CPQ simulator
- Extracts calculated costs
- Headless mode for performance
- Optional API upload

---

## Database Schema

### MySQL Database

**Host:** `ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com`
**Database:** `warrantyparts`
**Table:** `DealerMargins`

### DealerMargins Table Structure (Wide Format)

**Fixed Columns:**
- `DealerID` (VARCHAR) - Primary identifier
- `Dealership` (VARCHAR) - Dealer name
- `Enabled` (BOOLEAN) - Active status

**Dynamic Series Columns (Pattern: `{SERIES}_{MARGIN_TYPE}`):**

For each series: Q, QX, QXS, R, RX, RT, G, S, SX, L, LX, LT, LXS, S 23, SV 23, M

Six margin columns:
- `{SERIES}_BASE_BOAT` (INT) - Base boat margin %
- `{SERIES}_ENGINE` (INT) - Engine margin %
- `{SERIES}_OPTIONS` (INT) - Options margin %
- `{SERIES}_FREIGHT` (INT) - Freight margin %
- `{SERIES}_PREP` (INT) - Prep margin %
- `{SERIES}_VOL_DISC` (INT) - Volume discount %

**Example Columns:**
```sql
DealerID, Dealership, Enabled,
Q_BASE_BOAT, Q_ENGINE, Q_OPTIONS, Q_FREIGHT, Q_PREP, Q_VOL_DISC,
QX_BASE_BOAT, QX_ENGINE, QX_OPTIONS, QX_FREIGHT, QX_PREP, QX_VOL_DISC,
LXS_BASE_BOAT, LXS_ENGINE, LXS_OPTIONS, LXS_FREIGHT, LXS_PREP, LXS_VOL_DISC,
...
```

**Example Row:**
| DealerID | Dealership | Enabled | LXS_BASE_BOAT | LXS_ENGINE | LXS_OPTIONS | LXS_FREIGHT | LXS_PREP | LXS_VOL_DISC |
|----------|------------|---------|---------------|------------|-------------|-------------|----------|--------------|
| 12345 | ABC Marine | 1 | 15 | 10 | 12 | 8 | 5 | 2 |

---

## Pricing Calculation Flow

### Complete Quote Flow for Model 24LXSFB

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Get Model Information                               │
│ Source: OptionList API                                       │
│ Result: Model 24LXSFB                                        │
│         - Series: LXS                                        │
│         - MSRP: $49,046                                      │
│         - Floorplan: Fastback                                │
│         - Length: 24'                                        │
│         - Seats: 15                                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Get Dealer Margins (for Series LXS)                 │
│ Source: MySQL DealerMargins table                           │
│ Dealer: ABC Marine (ID: 12345)                              │
│ Result: LXS_BASE_BOAT = 15%                                 │
│         LXS_ENGINE = 10%                                     │
│         LXS_OPTIONS = 12%                                    │
│         LXS_FREIGHT = 8%                                     │
│         LXS_PREP = 5%                                        │
│         LXS_VOL_DISC = 2%                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Get Performance Specifications                      │
│ Source: Performance Matrix API (LXS_PerformanceData_2026)   │
│ Model: 24LXSFB                                              │
│ Result: MaxHP = 250                                          │
│         NoOfTubes = 3                                        │
│         HullWeight = 3,498 lbs                               │
│         PontoonGauge = 0.1"                                  │
│         FuelCapacity = "34-51 Gal"                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Get Standard Features                               │
│ Source: Model Standards Matrix API (LXS_ModelStandards_2026)│
│ Model: 24LXSFB                                              │
│ Result: 176 standard features including:                    │
│         - Non-Elevated Fiberglass Console (S)               │
│         - Console Courtesy Light (S)                         │
│         - Black Gloss Wheel (S)                              │
│         - etc.                                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Calculate Dealer Cost                               │
│                                                              │
│ Base Dealer Cost = MSRP × (1 - BASE_BOAT_MARGIN%)          │
│                  = $49,046 × (1 - 0.15)                     │
│                  = $41,689.10                                │
│                                                              │
│ (Engine, Options, Freight, Prep margins applied to          │
│  their respective component costs)                           │
│                                                              │
│ Final Quote = Base Cost + Options + Freight + Prep          │
│               - Volume Discount                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Series Information

### Active Series (2026)

| Series | Parent | Models | Avg MSRP | Description |
|--------|--------|--------|----------|-------------|
| **LXS** | L | 13 | $50,774 | Premium Sport Series |
| S | S | 51 | $26,015 | Standard Series |
| M | M | 31 | $783,384 | Premium Series |
| R | R | 41 | $76,763 | R Series |
| QX | Q | 45 | $140,293 | QX Series |
| RX | R | 28 | $83,523 | RX Series |
| Q | Q | 29 | $89,738 | Q Series |
| RT | R | 11 | $79,301 | RT Series |
| LT | L | 6 | $55,123 | LT Series |
| S1 | S | 8 | $26,394 | S1 Series |
| M1 | M | 2 | $999,999 | M1 Series |

**Total:** 265 visible models across 11 series

### LXS Series Models (13 models)

| Model | Length | Floorplan | MSRP | Seats |
|-------|--------|-----------|------|-------|
| 22LXSSB | 22' | Swingback | $45,744 | 13 |
| 23LXSFB | 23' | Fastback | $48,298 | 13 |
| 23LXSSB | 23' | Swingback | $47,402 | 15 |
| 24LXSFB | 24' | Fastback | $49,046 | 15 |
| 24LXSFBA | 24' | Fastback with Arch | $47,504 | 13 |
| 24LXSFBC | 24' | Fastback Center-Walkthrough | $50,254 | 15 |
| 24LXSSB | 24' | Swingback | $52,763 | 12 |
| 24LXSSBA | 24' | Swingback with Arch | $49,849 | 13 |
| 26LXSFB | 26' | Fastback | $51,497 | 15 |
| 26LXSFBA | 26' | Fastback with Arch | $49,976 | 15 |
| 26LXSFBC | 26' | Fastback Center-Walkthrough | $52,704 | 17 |
| 26LXSSB | 26' | Swingback | $55,110 | 16 |
| 26LXSSBA | 26' | Swingback with Arch | $59,914 | 15 |

---

## API Authentication

### OAuth 2.0 Configuration

**PRD Environment (Production):**
```
Token Endpoint: https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2
Grant Type: password
Client ID: QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo
Client Secret: 4O7OIZ64sukP1N6YeGZ6IpzsFTG4T6RFkcTZgq6ZwAetb4VoNOOJ1qMkGQAlvnOq...
Service Account: QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9...
```

**TRN Environment (Training/Test):**
```
Token Endpoint: https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2
Grant Type: password
Client ID: QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8
Client Secret: CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAn...
Service Account: QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLw...
```

**Token Lifetime:** ~2 hours (7200 seconds)
**Refresh Strategy:** Auto-refresh 5 minutes before expiration

---

## Key Insights

### 1. Series Changes Monthly
- Series list is dynamic (can add/remove series)
- Scripts automatically discover active series from OptionList API
- No hardcoded series lists needed

### 2. Dealer Margins are Series-Level
- Dealers set margins at the SERIES level (not per model)
- All models in a series use the same dealer margins
- Example: All 13 LXS models use the same LXS margins for a dealer

### 3. Data Sources are Separated
- **MSRP** → OptionList API (PRD)
- **Dealer Margins** → MySQL database
- **Performance Specs** → Matrix API (TRN)
- **Standard Features** → Matrix API (TRN)

### 4. Matrix Naming Convention
- Performance: `{SERIES}_PerformanceData_{YEAR}`
- Standards: `{SERIES}_ModelStandards_{YEAR}`
- Year updates annually

### 5. Wide vs Long Format
- **MySQL:** Wide format (dealer rows, series columns)
- **CPQ API:** Long format (one row per dealer × series)
- **Model Standards:** Wide format (feature rows, model columns)
- **Performance Data:** Long format (one row per model × perf package)

---

## Future Enhancements

### Potential Improvements
1. ✅ Add LXS to dealer margins (currently missing from hardcoded list)
2. Schedule automated daily/weekly syncs
3. Add data validation rules
4. Create dealer portal for self-service margin updates
5. Add audit logging for margin changes
6. Implement approval workflow for margin changes
7. Create pricing comparison reports
8. Add competitive pricing analysis

---

## Troubleshooting

### Common Issues

**1. Token Expiration**
- Tokens last ~2 hours
- Scripts automatically refresh
- If manual refresh needed: re-run authentication

**2. 404 Errors on Matrix API**
- Matrix may not exist for that series/year
- Check matrix name spelling: `{SERIES}_ModelStandards_2026`
- Verify series code from OptionList API

**3. MySQL Connection Issues**
- Check RDS security groups
- Verify credentials in script
- Ensure network access to AWS RDS

**4. Slow Upload Performance**
- Default: 8 concurrent workers
- Adjust `MAX_WORKERS` in script if needed
- Check API rate limits

---

## Contact & Support

**Repository:** github.com:mnseula/dealermargins.git
**Created:** 2026-01-21
**Last Updated:** 2026-01-21

For questions or issues, check the scripts' built-in help:
```bash
python3 {script_name}.py --help
```

---

*Generated with assistance from Claude Sonnet 4.5*
