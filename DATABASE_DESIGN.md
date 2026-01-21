# Database Design Documentation

## Entity Relationship Diagram

```
┌─────────────────┐
│     Series      │
│─────────────────│
│ series_id (PK)  │◄────────┐
│ series_name     │         │
│ parent_series   │         │
│ description     │         │
│ active          │         │
└─────────────────┘         │
                            │
                            │ FK
┌─────────────────────────┐ │
│        Models           │ │
│─────────────────────────│ │
│ model_id (PK)           │─┘
│ series_id (FK)          │◄────────┬─────────┬─────────┐
│ model_name              │         │         │         │
│ floorplan_code          │         │         │         │
│ floorplan_desc          │         │         │         │
│ length_feet             │         │         │         │
│ seats                   │         │         │         │
│ visible                 │         │         │         │
│ ...                     │         │         │         │
└─────────────────────────┘         │         │         │
                                    │         │         │
                                    │ FK      │ FK      │ FK
                         ┌──────────┘         │         │
                         │                    │         │
         ┌───────────────▼─────────┐          │         │
         │    ModelPricing         │          │         │
         │─────────────────────────│          │         │
         │ pricing_id (PK)         │          │         │
         │ model_id (FK)           │          │         │
         │ msrp                    │          │         │
         │ effective_date          │          │         │
         │ end_date                │          │         │
         │ year                    │          │         │
         └─────────────────────────┘          │         │
                                              │         │
                         ┌────────────────────┘         │
                         │                              │
         ┌───────────────▼──────────────┐               │
         │    ModelPerformance          │               │
         │──────────────────────────────│               │
         │ performance_id (PK)          │               │
         │ model_id (FK)                │               │
         │ perf_package_id (FK)         │◄──┐           │
         │ year                         │   │           │
         │ max_hp                       │   │           │
         │ no_of_tubes                  │   │ FK        │
         │ hull_weight                  │   │           │
         │ ...                          │   │           │
         └──────────────────────────────┘   │           │
                                            │           │
                 ┌──────────────────────────┘           │
                 │                                      │
         ┌───────▼──────────────┐                      │
         │ PerformancePackages  │                      │
         │──────────────────────│                      │
         │ perf_package_id (PK) │                      │
         │ package_name         │                      │
         │ description          │                      │
         │ active               │                      │
         └──────────────────────┘                      │
                                                       │
                         ┌─────────────────────────────┘
                         │
         ┌───────────────▼───────────────┐
         │  ModelStandardFeatures        │
         │───────────────────────────────│
         │ model_feature_id (PK)         │
         │ model_id (FK)                 │
         │ feature_id (FK)               │◄──┐
         │ year                          │   │
         │ is_standard                   │   │ FK
         └───────────────────────────────┘   │
                                             │
                         ┌───────────────────┘
                         │
         ┌───────────────▼───────────┐
         │   StandardFeatures        │
         │───────────────────────────│
         │ feature_id (PK)           │
         │ feature_code              │
         │ area                      │
         │ description               │
         │ sort_order                │
         │ active                    │
         └───────────────────────────┘
```

## Table Descriptions

### Core Tables

#### 1. **Series**
- **Purpose:** Stores boat series information
- **Key Fields:** series_id, series_name, parent_series
- **Examples:** LXS, Q, QX, R, M, S
- **Notes:** Series can change month-to-month

#### 2. **Models**
- **Purpose:** Central catalog of all boat models
- **Key Fields:** model_id, series_id, floorplan_code, length_feet, seats
- **Examples:** 24LXSFB, 26LXSSBA, 23QXFB
- **Relationships:**
  - Many-to-One with Series
  - One-to-Many with ModelPricing
  - One-to-Many with ModelPerformance
  - Many-to-Many with StandardFeatures (via junction table)

#### 3. **ModelPricing**
- **Purpose:** Track MSRP with effective dates for historical pricing
- **Key Fields:** model_id, msrp, effective_date, end_date, year
- **Notes:**
  - Multiple rows per model for price changes over time
  - Current price has `end_date = NULL`
  - Allows price history tracking

### Performance Tables

#### 4. **PerformancePackages**
- **Purpose:** Master list of performance packages
- **Key Fields:** perf_package_id, package_name
- **Examples:** "25_IN_22", "SPS+_22", "ESP_22", "TWIN_ELLIPTICAL_22"
- **Notes:** Relatively stable list, ~22 unique packages

#### 5. **ModelPerformance**
- **Purpose:** Technical specifications per model × performance package
- **Key Fields:** model_id, perf_package_id, max_hp, hull_weight, fuel_capacity
- **Notes:**
  - One row per model-perfpack combination
  - Some models have multiple performance packages
  - Includes cable/harness lengths for installation

### Standard Features Tables

#### 6. **StandardFeatures**
- **Purpose:** Master catalog of all possible standard features
- **Key Fields:** feature_id, area, description, sort_order
- **Examples:**
  - Area: "Console Features"
  - Description: "Non-Elevated Fiberglass Console"
- **Notes:**
  - Organized by area (Console, Seating, etc.)
  - ~176 features across most series

#### 7. **ModelStandardFeatures** (Junction Table)
- **Purpose:** Links models to their standard features
- **Key Fields:** model_id, feature_id, year, is_standard
- **Notes:**
  - Only stores records where feature IS standard
  - No row = feature is NOT standard for that model
  - Normalized approach vs. wide format in API

## Design Decisions

### 1. **Normalized vs. Denormalized**
- **Chosen:** Normalized (3NF)
- **Rationale:**
  - Reduces data redundancy
  - Easier to maintain consistency
  - Supports historical tracking
  - Can add new features without schema changes

### 2. **Historical Price Tracking**
- **Approach:** Effective date ranges in ModelPricing table
- **Benefits:**
  - Track price changes over time
  - Know exact price on any given date
  - Audit trail for pricing decisions

### 3. **Standard Features: Wide → Narrow Transformation**
- **API Format:** Wide (features as rows, models as columns, "S" values)
- **DB Format:** Narrow (junction table with only standard features)
- **Rationale:**
  - Normalized approach is more flexible
  - Easy to query "which models have feature X?"
  - Easy to query "what features does model Y have?"
  - No schema changes when new models added

### 4. **Performance Package Separation**
- **Approach:** Separate PerformancePackages table
- **Benefits:**
  - Reusable across models
  - Can update package descriptions globally
  - Clear one-to-many relationship

### 5. **Series as Separate Table**
- **Approach:** Series table with FK from Models
- **Benefits:**
  - Central place for series metadata
  - Support parent-child series relationships
  - Can track series lifecycle (active/inactive)

## Data Loading Strategy

### Phase 1: Load Master Data
```sql
-- 1. Load Series
INSERT INTO Series (series_id, series_name, parent_series)
VALUES ('LXS', 'LXS Series', 'L');

-- 2. Load Models
INSERT INTO Models (model_id, series_id, model_name, ...)
VALUES ('24LXSFB', 'LXS', '24 LXS Fastback', ...);

-- 3. Load Performance Packages
INSERT INTO PerformancePackages (perf_package_id, package_name)
VALUES ('SPS+_22', 'SPS+ Performance Package');

-- 4. Load Standard Features
INSERT INTO StandardFeatures (feature_code, area, description, sort_order)
VALUES ('CONSOLE_FIBERGLASS', 'Console Features', 'Non-Elevated Fiberglass Console', 1);
```

### Phase 2: Load Transactional Data
```sql
-- 5. Load Pricing
INSERT INTO ModelPricing (model_id, msrp, effective_date, year)
VALUES ('24LXSFB', 49046.00, '2026-01-01', 2026);

-- 6. Load Performance Data
INSERT INTO ModelPerformance (model_id, perf_package_id, year, max_hp, ...)
VALUES ('24LXSFB', 'SPS+_22', 2026, 250.0, ...);

-- 7. Load Model-Feature Relationships
INSERT INTO ModelStandardFeatures (model_id, feature_id, year)
VALUES ('24LXSFB', 42, 2026);  -- feature_id 42 = Fiberglass Console
```

## Common Query Patterns

### 1. Get Complete Model Information
```sql
CALL GetModelFullDetails('24LXSFB', 2026);
-- Returns: Model info, pricing, performance specs, standard features
```

### 2. Find Models by Features
```sql
-- Models with specific feature
SELECT m.model_id, m.model_name, m.series_id
FROM Models m
JOIN ModelStandardFeatures msf ON m.model_id = msf.model_id
JOIN StandardFeatures sf ON msf.feature_id = sf.feature_id
WHERE sf.description LIKE '%Console Courtesy Light%'
  AND msf.year = 2026;
```

### 3. Price Range Search
```sql
SELECT * FROM ModelWithCurrentPrice
WHERE msrp BETWEEN 45000 AND 55000
  AND series_id = 'LXS'
ORDER BY msrp;
```

### 4. Feature Comparison Across Models
```sql
-- Compare features between two models
SELECT
    sf.area,
    sf.description,
    MAX(CASE WHEN msf.model_id = '24LXSFB' THEN 'Yes' ELSE NULL END) as Model_24LXSFB,
    MAX(CASE WHEN msf.model_id = '26LXSSBA' THEN 'Yes' ELSE NULL END) as Model_26LXSSBA
FROM StandardFeatures sf
LEFT JOIN ModelStandardFeatures msf ON sf.feature_id = msf.feature_id
    AND msf.model_id IN ('24LXSFB', '26LXSSBA')
    AND msf.year = 2026
GROUP BY sf.feature_id, sf.area, sf.description
ORDER BY sf.area, sf.sort_order;
```

### 5. Performance Package Availability
```sql
-- Which performance packages are available for a series?
SELECT DISTINCT
    m.series_id,
    pp.perf_package_id,
    pp.package_name,
    COUNT(DISTINCT m.model_id) as model_count
FROM Models m
JOIN ModelPerformance mp ON m.model_id = mp.model_id
JOIN PerformancePackages pp ON mp.perf_package_id = pp.perf_package_id
WHERE m.series_id = 'LXS'
  AND mp.year = 2026
GROUP BY m.series_id, pp.perf_package_id, pp.package_name;
```

## Views Provided

### 1. **CurrentModelPricing**
- Shows current active pricing for all visible models
- Filters out historical prices (end_date IS NULL)

### 2. **ModelWithCurrentPrice**
- Complete model info joined with current price
- Includes series information

### 3. **ModelStandardFeaturesList**
- Flattened view of models and their standard features
- Easy to read, includes area and sort order

### 4. **ModelPerformanceDetails**
- Complete performance data with package names
- Includes series information for context

## Indexes for Performance

### Primary Indexes
- All primary keys are automatically indexed
- Foreign keys are explicitly indexed

### Composite Indexes
- `idx_models_series_visible`: Frequently filter by series + visibility
- `idx_models_length_series`: Common to sort by length within series
- `idx_pricing_year_current`: Quick access to current pricing
- `idx_performance_year`: Year-based performance queries
- `idx_standards_year`: Year-based feature queries

### Query Optimization Tips
1. Always include `year` in queries when available (indexed)
2. Use `visible = TRUE` filter for active catalog
3. Use `end_date IS NULL` for current pricing
4. Leverage views for common query patterns

## Stored Procedures

### 1. **GetModelFullDetails**
```sql
CALL GetModelFullDetails('24LXSFB', 2026);
```
Returns three result sets:
1. Model basic info with price
2. Performance data with all specs
3. Standard features list

### 2. **UpdateModelPrice**
```sql
CALL UpdateModelPrice('24LXSFB', 51000.00, '2026-06-01', 2026);
```
- Automatically ends the current price
- Inserts new price with effective date
- Maintains price history

## Migration from API Data

### Script Requirements
Create Python scripts to:

1. **populate_series.py** - Extract unique series from API
2. **populate_models.py** - Load models from OptionList API
3. **populate_pricing.py** - Load MSRP from OptionList API
4. **populate_performance.py** - Load from Performance Matrix API
5. **populate_standards.py** - Transform and load Standards Matrix API

Each script should:
- Use existing API fetcher scripts as base
- Transform data from API format to DB format
- Handle duplicates (INSERT ... ON DUPLICATE KEY UPDATE)
- Log import statistics

## Maintenance

### Regular Tasks
1. **Update Pricing:** When MSRP changes, use `UpdateModelPrice` procedure
2. **Add New Models:** Insert into Models, then pricing, performance, features
3. **Archive Old Data:** Keep historical data, but can archive by year
4. **Refresh from API:** Run population scripts monthly to sync changes

### Data Integrity Checks
```sql
-- Models without pricing
SELECT m.model_id FROM Models m
LEFT JOIN ModelPricing p ON m.model_id = p.model_id AND p.end_date IS NULL
WHERE m.visible = TRUE AND p.pricing_id IS NULL;

-- Models without performance data
SELECT m.model_id FROM Models m
LEFT JOIN ModelPerformance mp ON m.model_id = mp.model_id AND mp.year = 2026
WHERE m.visible = TRUE AND mp.performance_id IS NULL;

-- Features without any models
SELECT sf.feature_id, sf.description FROM StandardFeatures sf
LEFT JOIN ModelStandardFeatures msf ON sf.feature_id = msf.feature_id
WHERE sf.active = TRUE AND msf.model_feature_id IS NULL;
```

## Future Enhancements

### Potential Additions
1. **Options Table:** Track available options/upgrades per model
2. **ColorSchemes Table:** Track available colors/schemes
3. **ModelImages Table:** Store multiple images per model
4. **CustomerConfigurations:** Save customer-specific configurations
5. **DealerInventory:** Track dealer stock levels
6. **OrderHistory:** Track orders and configurations

### Relationship to Existing DealerMargins Table
- DealerMargins table remains separate
- Series in this schema match series columns in DealerMargins
- Can JOIN on series_id to combine data for quotes

---

**Created:** 2026-01-21
**Version:** 1.0
**Status:** Initial Design
