# Window Sticker Generation - Pure SQL

## Overview
Window stickers are generated entirely via SQL stored procedures. No Python required.

## Data Successfully Loaded
```
✅ Models:              283 (0 errors)
✅ Performance records: 1083 (0 errors)
✅ Standard features:   1694 (0 errors)
✅ Dealer margins:      100 (0 errors)
```

## Generate Window Sticker

### Method 1: Direct SQL Call

```sql
-- Connect to database
mysql -h ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com -u awsmaster -p warrantyparts_test

-- Generate window sticker
CALL GetWindowStickerData('25QXFBWA', 'NICHOLS MARINE - NORMAN');
```

### Method 2: SQL Client (DBeaver, MySQL Workbench, etc.)

```sql
USE warrantyparts_test;

CALL GetWindowStickerData('25QXFBWA', 'NICHOLS MARINE - NORMAN');
```

## Result Sets Returned

The stored procedure returns **4 result sets**:

### Result Set 1: Model Information
- model_id, model_name, series_id, series_name, parent_series
- floorplan_code, floorplan_desc
- length_feet, length_str, beam_length, beam_str
- loa, loa_str, seats
- msrp, year, effective_date
- dealer_name, generated_date

### Result Set 2: Performance Specifications
- perf_package_id, package_name
- max_hp, no_of_tubes, person_capacity, hull_weight
- pontoon_gauge, transom, tube_height, tube_center_to_center
- max_width, fuel_capacity
- tube_length_str, deck_length_str

### Result Set 3: Standard Features (by Area)
- area (Console Features, Exterior Features, Interior Features, Warranty)
- description
- sort_order

### Result Set 4: Included Options from Sales Database
- ItemNo
- ItemDescription
- Quantity
- SalePrice
- MSRP

## Other Available Stored Procedures

### Calculate Dealer Quote
```sql
CALL CalculateDealerQuote(
    '25QXFBWA',     -- model_id
    '00333836',     -- dealer_id
    15000.00,       -- engine_msrp
    2000.00,        -- freight
    1500.00         -- prep
);
```

Returns complete pricing breakdown with dealer margins applied.

### Get Model Full Details
```sql
CALL GetModelFullDetails('25QXFBWA', '00333836');
```

Returns 5 result sets: model info, performance, features, dealer margins, included options.

### Get Included Options Only
```sql
CALL GetIncludedOptions('25QXFBWA');
```

Returns just the included options/accessories from sales database.

## Example Models to Test

```sql
-- QX Series - Fastback with Windshield and Arch
CALL GetWindowStickerData('25QXFBWA', 'NICHOLS MARINE - NORMAN');

-- Find other models
SELECT model_id, series_id, floorplan_desc, msrp
FROM Models
WHERE series_id = 'QX'
ORDER BY msrp;
```

## Find Dealers

```sql
-- List all active dealers
SELECT dealer_id, dealer_name
FROM Dealers
ORDER BY dealer_name;

-- Find dealers with margins for QX series
SELECT DISTINCT d.dealer_id, d.dealer_name
FROM Dealers d
JOIN DealerMargins dm ON d.dealer_id = dm.dealer_id
WHERE dm.series_id = 'QX' AND dm.end_date IS NULL
ORDER BY d.dealer_name;
```

## Current Database Statistics

```
Active models:           283
Current pricing records: 283
Active dealers:          12
Current margin configs:  100
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  SQL Stored Procedures (Business Logic)                │
├─────────────────────────────────────────────────────────┤
│  • GetWindowStickerData                                 │
│  • CalculateDealerQuote                                 │
│  • GetModelFullDetails                                  │
│  • GetIncludedOptions                                   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  MySQL Database (warrantyparts_test)                   │
├─────────────────────────────────────────────────────────┤
│  CPQ Tables:                                            │
│    • Series, Models, ModelPricing                       │
│    • PerformancePackages, ModelPerformance              │
│    • StandardFeatures, ModelStandardFeatures            │
│    • Dealers, DealerMargins                             │
│                                                          │
│  Sales Database (read-only):                            │
│    • BoatOptions25_test (included options)              │
└─────────────────────────────────────────────────────────┘
                           ↑
┌─────────────────────────────────────────────────────────┐
│  Python Data Loaders (Data Loading ONLY)               │
├─────────────────────────────────────────────────────────┤
│  • load_cpq_data.py (models, pricing, perf, features)  │
└─────────────────────────────────────────────────────────┘
                           ↑
┌─────────────────────────────────────────────────────────┐
│  Infor CPQ APIs                                         │
├─────────────────────────────────────────────────────────┤
│  • PRD: Model prices                                    │
│  • TRN: Performance, features, dealer margins           │
└─────────────────────────────────────────────────────────┘
```

## Key Principle

**Python is ONLY for data loading from APIs. Everything else is SQL-driven.**

- ✅ Window stickers = SQL stored procedures
- ✅ Dealer quotes = SQL stored procedures
- ✅ Price calculations = SQL stored procedures
- ✅ Data queries = SQL views and procedures
- ❌ No Python business logic
- ❌ No Python for generation or calculation
