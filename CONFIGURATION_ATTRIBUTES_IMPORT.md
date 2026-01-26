# Boat Configuration Attributes Import

## Overview

This import pulls boat configuration data from SQL Server staging database into a dedicated MySQL table. This consolidates all configuration information (Performance Package, Console, Fuel, Colors, etc.) in one place.

## Problem Solved

**Before:** Configuration data (like Performance Package) exists in SQL Server `cfg_attr_mst` table but wasn't being imported to MySQL.

**After:** All key configuration attributes are imported to `BoatConfigurationAttributes` table, making it easy to look up what performance package, console type, fuel config, etc. each boat has.

## Database Structure

### New Table: `BoatConfigurationAttributes`

Stores configuration attributes for each boat from SQL Server.

**Key Fields:**
- `boat_serial_no` - HIN (Hull Identification Number)
- `boat_model_no` - Boat model number
- `erp_order_no` - Sales order number (links to BoatOptions25_test)
- `attr_name` - Configuration attribute name (e.g., "Performance Package")
- `attr_value` - Configuration value (e.g., "ESP+_25")
- `cfg_value` - Value from `cfgaUf_BENN_Cfg_Value` field
- `config_id` - Configuration ID from configurator

### Views Created

**1. BoatPerformancePackages**
```sql
SELECT * FROM BoatPerformancePackages WHERE boat_model_no = '25QXFBWA';
```
Quick lookup of performance packages by boat.

**2. BoatConfigurationSummary**
```sql
SELECT * FROM BoatConfigurationSummary WHERE boat_model_no = '25QXFBWA';
```
Pivot view showing all key configuration options in columns.

## Setup Instructions

### 1. Create the MySQL Table

```bash
mysql -h ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com -u awsmaster -p warrantyparts_test < boat_configuration_attributes_schema.sql
```

### 2. Run the Import (C# .NET)

Add to your existing CustomerPortalTools project:

```csharp
// In your Main() method or import routine:
var configImporter = new ConfigurationAttributesImporter();
configImporter.ExportFromSqlServerAndImportToMySql();
```

This will:
1. Query SQL Server `cfg_attr_mst` table
2. Export to CSV: `C:\temp\boat_config_attrs_export.csv`
3. Import to MySQL `BoatConfigurationAttributes` table
4. Show summary of imported attributes

### 3. Verify Import

```sql
-- Check row count
SELECT COUNT(*) FROM BoatConfigurationAttributes;

-- See what attributes were imported
SELECT attr_name, COUNT(*) as record_count
FROM BoatConfigurationAttributes
GROUP BY attr_name
ORDER BY record_count DESC;

-- Check Performance Package data
SELECT * FROM BoatPerformancePackages LIMIT 10;
```

## Key Configuration Attributes Imported

The import focuses on these attributes (from `cfg_attr_mst.attr_name`):

**Performance & Technical:**
- **Performance Package** ⭐ (ESP+_25, SPS+, etc.)
- Fuel
- Lifting Strakes
- Saltwater Package

**Console & Electronics:**
- Console
- Main Display
- Additional Display
- Rockford Fosgate Stereo
- Steering Wheels

**Furniture & Interior:**
- Captain's Chairs
- Co-Captain's Chairs
- Tables - Bow
- Tables - Aft
- FURNITURE UPGRADE
- BASE VINYL
- FLOORING

**Exterior & Colors:**
- Canvas Color
- Trim Accents
- Exterior Color Packages
- Bimini Cable Stays
- Aft Bimini Tops
- Bow Bimini Tops
- Arch

## Using the Data

### Find Performance Package for a Boat

**By Model Number:**
```sql
SELECT
    boat_model_no,
    performance_package,
    erp_order_no,
    invoice_date
FROM BoatPerformancePackages
WHERE boat_model_no = '25QXFBWA';
```

**By Sales Order:**
```sql
SELECT
    attr_name,
    attr_value,
    cfg_value
FROM BoatConfigurationAttributes
WHERE erp_order_no = 'SO00930192'
ORDER BY attr_name;
```

### Match Performance Package to CPQ Data

```sql
-- Get performance package for boats and match to ModelPerformance specs
SELECT
    bpp.boat_model_no,
    bpp.performance_package,
    mp.max_hp,
    mp.no_of_tubes,
    mp.person_capacity,
    mp.hull_weight,
    mp.pontoon_gauge
FROM BoatPerformancePackages bpp
LEFT JOIN ModelPerformance mp
    ON mp.perf_package_id = bpp.performance_package
    AND mp.year = 2025
WHERE bpp.boat_model_no LIKE '25%'
LIMIT 20;
```

### Loop Through Config Attrs (as you mentioned)

```sql
-- Get all config attrs for a specific HIN/Sales Order
SELECT
    boat_serial_no,
    erp_order_no,
    attr_name,
    attr_value,
    cfg_value
FROM BoatConfigurationAttributes
WHERE erp_order_no = 'SO00930192'
ORDER BY attr_name;
```

Then in your application code:
```csharp
// Loop through results and match performance package
foreach (var attr in configAttrs)
{
    if (attr.AttrName == "Performance Package")
    {
        string perfPackageId = attr.CfgValue; // or attr.AttrValue
        // Now match to ModelPerformance.perf_package_id
        var perfSpecs = GetPerformanceSpecs(perfPackageId);
        // Display the specs
    }
}
```

### Enhanced Window Sticker Query

Now you can include actual performance package from sales data:

```sql
-- Window sticker with actual performance package sold
SELECT
    m.model_id,
    m.model_name,
    p.msrp,
    bpp.performance_package AS actual_perf_package_sold,
    mp.max_hp,
    mp.no_of_tubes,
    mp.hull_weight,
    mp.pontoon_gauge
FROM Models m
JOIN ModelPricing p ON m.model_id = p.model_id
LEFT JOIN BoatPerformancePackages bpp ON m.model_id = bpp.boat_model_no
LEFT JOIN ModelPerformance mp
    ON mp.model_id = m.model_id
    AND mp.perf_package_id = bpp.performance_package
    AND mp.year = p.year
WHERE m.model_id = '25QXFBWA'
  AND p.end_date IS NULL;
```

## Data Flow Diagram

```
SQL Server (CSISTG)
   ├── coitem_mst (order items)
   └── cfg_attr_mst (configuration attributes) ⭐
         ├── attr_name = 'Performance Package'
         ├── cfgaUf_BENN_Cfg_Value = 'ESP+_25'
         └── ... other attributes
              ↓
       ConfigurationAttributesImporter.cs
              ↓
       CSV Export (C:\temp\boat_config_attrs_export.csv)
              ↓
       MySQL warrantyparts_test
              ↓
       BoatConfigurationAttributes table
              ↓
       BoatPerformancePackages view (filtered)
```

## Matching Logic

**To match performance package to perf package ID:**

1. Query `BoatConfigurationAttributes` for your boat:
   ```sql
   WHERE erp_order_no = 'SO00930192' AND attr_name = 'Performance Package'
   ```

2. Get the `cfg_value` or `attr_value` (e.g., "ESP+_25")

3. Match to `ModelPerformance.perf_package_id`:
   ```sql
   WHERE perf_package_id = 'ESP+_25'
   ```

4. Retrieve all performance specs (HP, tubes, weight, gauge)

## Benefits

✅ **Consolidated Data** - All config attributes in one MySQL table
✅ **No API Calls** - Data is local in MySQL, fast queries
✅ **Easy Matching** - Simple JOIN to link boats to their actual configurations
✅ **Performance Package** - Now know exactly which package each boat has
✅ **Complete Picture** - Can show "as-configured" vs "available options"

## Maintenance

**Refresh Frequency:**
- Run the import whenever you refresh `BoatOptions25_test`
- Same schedule as your existing boat options import
- Configuration attributes should be stable once boat is sold

**Data Size:**
- ~106 records per key attribute
- ~20-25 key attributes = ~2,000-2,500 records
- Very lightweight table

## Troubleshooting

**No records imported:**
- Check SQL Server connection
- Verify `cfg_attr_mst` table exists
- Check that `cfgaUf_BENN_Cfg_Value` column exists

**Performance Package not showing:**
- Verify attr_name = 'Performance Package' exists in SQL Server
- Check the WHERE clause in the import query includes 'Performance Package'
- Query SQL Server directly to confirm data exists

**Can't match to perf_package_id:**
- The `attr_value` or `cfg_value` should match `ModelPerformance.perf_package_id`
- May need to trim whitespace or adjust format
- Check for exact match vs pattern match

## Example: Complete Boat Configuration

```sql
-- Get everything about a boat
SELECT
    'Model' AS category,
    m.model_id AS detail,
    m.model_name AS description
FROM Models m
WHERE m.model_id = '25QXFBWA'

UNION ALL

SELECT
    'Pricing' AS category,
    CONCAT('$', FORMAT(p.msrp, 2)) AS detail,
    CONCAT('Model Year ', p.year) AS description
FROM ModelPricing p
WHERE p.model_id = '25QXFBWA'
  AND p.end_date IS NULL

UNION ALL

SELECT
    'Configuration' AS category,
    attr_name AS detail,
    attr_value AS description
FROM BoatConfigurationAttributes
WHERE boat_model_no = '25QXFBWA'

ORDER BY category, detail;
```

This gives you a complete picture of the boat configuration in one query!
