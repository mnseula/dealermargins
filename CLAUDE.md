# Bennington Dealer Margins & CPQ System

## Project Overview

This project builds a SQL-driven dealer margin and quote system for Bennington Marine. It combines boat specifications from Infor CPQ APIs with sales data to generate window stickers and dealer quotes with margin calculations.

## Architecture

### Data Flow
```
Infor CPQ APIs → Python Scripts → MySQL Database → SQL Stored Procedures → Quotes/Window Stickers
                                                  ↗
                 BoatOptions25_test (read-only)
```

### Key Principle
- **Python scripts ONLY for data loading** - Fetch from APIs and populate database
- **SQL-driven for everything else** - Quotes, window stickers, calculations all done via stored procedures and views
- **BoatOptions25_test is read-only** - Never modify sales database, only query it

## Database Architecture

### Primary Database: `bennington_cpq`
Main CPQ database with boat models, pricing, performance specs, dealer margins.

**Core Tables:**
- `Series` - Boat series (Q, QX, R, LXS, M, S, etc.)
- `Models` - Central catalog of all boat models
- `ModelPricing` - MSRP pricing with effective date tracking
- `ModelPerformance` - Performance specs per model × performance package
- `PerformancePackages` - Performance package definitions
- `StandardFeatures` - Master list of standard features
- `ModelStandardFeatures` - Junction table linking models to features
- `Dealers` - Dealer information
- `DealerMargins` - Margin percentages per dealer × series combination

### Secondary Database: `warrantyparts_test`
Existing sales database - **READ ONLY**

**Key Table:**
- `BoatOptions25_test` - Historical sales data with line items
  - Used to get included options where `ItemMasterProdCat = 'ACC'`
  - Contains: ItemNo, ItemDesc1, QuantitySold, ExtSalesAmount, BoatModelNo

## Database Credentials

**RDS MySQL:**
```
Host:     ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com
User:     awsmaster
Password: VWvHG9vfG23g7gD
Database: bennington_cpq (main) / warrantyparts_test (sales data)
```

## API Credentials

### Production Environment (PRD)
```
Client ID:     QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo
Client Secret: 4O7OIZ64sukP1N6YeGZ6IpzsFTG4T6RFkcTZgq6ZwAetb4VoNOOJ1qMkGQAlvnOqqcgaZDlXKux6YEQNvoZQgg
Service Key:   QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9xuXKp_iYp49_M7JuB7UaEo0xjWDqTAE1Q15rQhxojw
Service Secret: IZq8wArFnHi4rESTZ-3SQT5zMgiCQfre8aLM6KirsVmvBhXmGDZS_4TXvCZlD40AjpXX6igL7y8A3svCHV-glg
Token Endpoint: https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2
```

### Training Environment (TRN)
```
Client ID:     QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8
Client Secret: CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAnyArDH3ZebqYTKAoMq37_aQ
Service Key:   QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw
Service Secret: pAze3yNlj8r6dbcTv-Fn8AiGvhIcs2x-yEgJaMiuoraAJdkFB6iLQFKaFQCP_17KZIYoroUoF_CeEoslHWlXug
Token Endpoint: https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2
```

### API Endpoints
- **Model Prices (PRD):** `https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/DataImport/QA2FNBZCKUAUH7QB_PRD/v1/OptionLists/bb38d84e-6493-40c7-b282-9cb9c0df26ae/values`
- **Performance Data (TRN):** `https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/{series}_PerformanceData_2026/values`
- **Standard Features (TRN):** `https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/{series}_ModelStandards_2026/values`
- **Dealer Margins (TRN):** `https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities/C_GD_DealerMargin`

## Key Files

### Database Schema Files
- `database_schema.sql` - Main CPQ database schema (Series, Models, ModelPricing, Performance, Features)
- `dealer_margins_schema.sql` - Dealer and margin tables with views and procedures
- `stored_procedures.sql` - Comprehensive stored procedures for quotes and window stickers

### Python Data Loading Scripts
- `fetch_model_prices.py` - Loads model pricing from OptionList API
- `fetch_all_performance_data.py` - Loads performance specifications by series
- `fetch_all_model_standards.py` - Loads standard features by series
- `query_boat_info.py` - Query functions for boat info and dealer margins
- `generate_window_sticker.py` - Python version (being deprecated in favor of SQL procedures)

### Database Configuration
- `db_config.py` - Database connection configuration

## Setup Instructions

### 1. Create Database Tables
```sql
-- Connect to MySQL
mysql -h ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com -u awsmaster -p

-- Create main database
CREATE DATABASE IF NOT EXISTS bennington_cpq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bennington_cpq;

-- Run schema files in order
source database_schema.sql;
source dealer_margins_schema.sql;
source stored_procedures.sql;
```

### 2. Load Data from APIs
```bash
# Load model pricing
python3 fetch_model_prices.py

# Load performance data
python3 fetch_all_performance_data.py

# Load standard features
python3 fetch_all_model_standards.py

# Load dealer margins (if available)
# python3 load_dealer_margins.py
```

## Using the System

### Query Dealer Margins
```python
python3 -c "
from query_boat_info import get_dealer_margins
margins = get_dealer_margins('NICHOLS MARINE - NORMAN', 'QX')
print(margins)
"
```

### Generate Window Sticker (SQL)
```sql
CALL GetWindowStickerData('25QXFBWA', 'NICHOLS MARINE - NORMAN');
-- Returns 4 result sets:
--   1. Model info with pricing
--   2. Performance specifications
--   3. Standard features by area
--   4. Included options from sales database
```

### Calculate Dealer Quote
```sql
CALL CalculateDealerQuote(
    '25QXFBWA',     -- model_id
    '00333836',     -- dealer_id
    15000.00,       -- engine_msrp
    2000.00,        -- freight
    1500.00         -- prep
);
-- Returns complete pricing breakdown with margins applied
```

### Get Included Options
```sql
CALL GetIncludedOptions('25QXFBWA');
-- Returns ACC items from BoatOptions25_test
```

### Get Complete Model Details
```sql
CALL GetModelFullDetails('25QXFBWA', '00333836');
-- Returns 5 result sets: model, performance, features, margins, options
```

## Important Design Decisions

### Why ItemMasterProdCat = 'ACC' instead of ItemNo LIKE '90%'
- **Problem:** New system won't use "90" prefix for option item numbers
- **Solution:** Filter by product category field (`ItemMasterProdCat = 'ACC'`) instead
- **Benefit:** Future-proof against numbering system changes

### Why SQL Stored Procedures Instead of Python
- **Real-time calculations** - Always uses current data from tables
- **Better performance** - Database does the work, no data transfer overhead
- **Easier maintenance** - Business logic in one place
- **Simpler architecture** - Application just calls procedures

### Why Read-Only Access to BoatOptions25_test
- **Data integrity** - Sales database is source of truth, never modify historical data
- **Safety** - Queries can't accidentally corrupt sales records
- **Clear separation** - CPQ data (writeable) vs Sales data (read-only)

## Stored Procedures Reference

### GetIncludedOptions(model_id)
Returns accessories for a model from sales database.
```sql
CALL GetIncludedOptions('25QXFBWA');
```

### GetWindowStickerData(model_id, dealer_name)
Returns complete window sticker data (4 result sets).
```sql
CALL GetWindowStickerData('25QXFBWA', 'NICHOLS MARINE - NORMAN');
```

### CalculateDealerQuote(model_id, dealer_id, engine_msrp, freight, prep)
Calculates dealer pricing with margins applied.
```sql
CALL CalculateDealerQuote('25QXFBWA', '00333836', 15000.00, 2000.00, 1500.00);
```

### GetModelFullDetails(model_id, dealer_id)
Returns comprehensive model data (5 result sets).
```sql
CALL GetModelFullDetails('25QXFBWA', '00333836');
```

## Database Views

### CurrentDealerMargins
Shows current active margins for all dealer-series combinations.
```sql
SELECT * FROM CurrentDealerMargins WHERE dealer_name LIKE '%NICHOLS%';
```

### CurrentModelPricing
Shows current active pricing for all models.
```sql
SELECT * FROM CurrentModelPricing WHERE series_id = 'QX';
```

### DealerMarginsSummary
Summary of dealer margins with calculated examples at $100k MSRP.
```sql
SELECT * FROM DealerMarginsSummary WHERE series_id = 'QX';
```

### ModelWithCurrentPrice
Complete model information with current pricing.
```sql
SELECT * FROM ModelWithCurrentPrice WHERE model_id = '25QXFBWA';
```

## Example Dealer: Nichols Marine - Norman
```
Dealer ID:   00333836
Dealer Name: NICHOLS MARINE - NORMAN
Series:      QX
Margins:     27% across all categories (base, engine, options, freight, prep)
Status:      Configured but currently disabled (C_Enabled = FALSE)
```

## Example Model: 25QXFBWA
```
Model:       25QXFBWA
Series:      QX (Q Parent Series)
Description: 25' Fastback with Windshield and Arch
MSRP:        $103,726.00
Length:      28'-3" LOA
Beam:        8'-6"
Seats:       15
Max HP:      200 HP (base package), up to 500 HP (performance packages)
Tubes:       2 or 3 depending on performance package
```

## Common Queries

### Find all dealers with margins for a series
```sql
SELECT * FROM CurrentDealerMargins
WHERE series_id = 'QX'
ORDER BY dealer_name;
```

### Get all models in a series with pricing
```sql
SELECT * FROM CurrentModelPricing
WHERE series_id = 'QX'
ORDER BY length_feet, msrp;
```

### Calculate dealer cost for a specific boat
```sql
SELECT
    model_id,
    msrp,
    dealer_name,
    base_boat_margin,
    ROUND(msrp * (1 - base_boat_margin/100), 2) as dealer_cost,
    ROUND(msrp * (base_boat_margin/100), 2) as savings
FROM CurrentModelPricing cp
JOIN CurrentDealerMargins dm ON cp.series_id = dm.series_id
WHERE model_id = '25QXFBWA'
  AND dealer_name = 'NICHOLS MARINE - NORMAN';
```

## Troubleshooting

### No included options showing for a model
- Check if model exists in BoatOptions25_test: `SELECT COUNT(*) FROM warrantyparts_test.BoatOptions25_test WHERE BoatModelNo = '25QXFBWA'`
- Check for ACC items: `SELECT COUNT(*) FROM warrantyparts_test.BoatOptions25_test WHERE BoatModelNo = '25QXFBWA' AND ItemMasterProdCat = 'ACC'`
- New models may not have sales data yet - window sticker will show once boats are sold

### Dealer margins not found
- Verify dealer exists: `SELECT * FROM Dealers WHERE dealer_name LIKE '%NICHOLS%'`
- Check margin configuration: `SELECT * FROM DealerMargins WHERE dealer_id = '00333836'`
- Verify series matches: Model series must match margin series_id

### API authentication errors
- Token expires after ~1 hour - script will auto-refresh
- Check credentials in API configuration section above
- Use TRN environment for performance/standards, PRD for pricing

## Next Steps / TODO

- [ ] Populate database with initial data from APIs
- [ ] Test stored procedures with real data
- [ ] Create additional views for common queries
- [ ] Build reporting dashboards/queries
- [ ] Document additional business rules
- [ ] Add freight and prep cost logic
- [ ] Create quote templates

## Notes

- All timestamps in database are UTC
- Model year is currently hardcoded to 2026
- Margins are stored as percentages (27.0 = 27%)
- ExtSalesAmount in BoatOptions25_test may be NULL for some items
- Some models exist in CPQ but not in sales database (and vice versa)
