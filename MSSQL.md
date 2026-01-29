# MSSQL Database Documentation

**Database:** CSISTG (CSI/ERP System)  
**Server:** MPL1STGSQL086.POLARISSTAGE.COM  
**Purpose:** Source of actual sold boat data with pricing

---

## Overview

The MSSQL database contains the **ERP (Enterprise Resource Planning)** data from the CSI (Customer Systems Inc.) system. This is the system of record for:
- Actual boat orders and sales
- Real pricing data for sold boats
- Configuration attributes chosen by customers
- Invoice and billing information

This is different from the **CPQ API data** which contains catalog/base model pricing for planning purposes.

---

## Connection Details

```python
SQL_SERVER = "MPL1STGSQL086.POLARISSTAGE.COM"
SQL_DATABASE = "CSISTG"
SQL_USERNAME = "svccsimarine"
SQL_PASSWORD = "CNKmoFxEsXs0D9egZQXH"
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  MSSQL/CSI ERP (Source of Truth for Actual Sales)               │
│  Server: MPL1STGSQL086.POLARISSTAGE.COM                         │
│  Database: CSISTG                                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ Python Scripts (pymssql)
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  MySQL (warrantyparts_test)                                     │
├─────────────────────────────────────────────────────────────────┤
│  • BoatConfigurationAttributes - Configuration choices          │
│  • BoatOptions25_test - Line items with pricing                 │
│  • SerialNumberMaster - Master boat registry                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Tables

### 1. `coitem_mst` - Customer Order Item Master

**Primary table for pricing and line items.**

**Key Fields:**
| Field | Description |
|-------|-------------|
| `co_num` | ERP Order Number (e.g., "SO00935977") |
| `co_line` | Line number within the order |
| `item` | Item number |
| `price` | **Unit price** (the actual price charged) |
| `qty_ordered` | Quantity ordered |
| `qty_invoiced` | Quantity sold/invoiced |
| `Uf_BENN_BoatSerialNumber` | Boat HIN/Serial Number |
| `Uf_BENN_BoatModel` | Boat model number |
| `Uf_BENN_BoatWebOrderNumber` | Web order reference |
| `config_id` | Configuration ID (links to cfg_attr_mst) |
| `site_ref` | Site reference (always 'BENN' for Bennington) |

**Price Calculation:**
```sql
Unit Price:      CAST(coi.price AS DECIMAL(10,2))
Extended Price:  CAST((coi.price * coi.qty_ordered) AS DECIMAL(10,2))
```

### 2. `item_mst` - Item Master

**Contains item descriptions and categorization.**

**Key Fields:**
| Field | Description |
|-------|-------------|
| `item` | Item number (joins to coitem_mst.item) |
| `description` | Item description |
| `product_code` | Product category classification |
| `Uf_BENN_Series` | Boat series (Q, QX, SV, etc.) |

**Product Codes:**
| Code | Description |
|------|-------------|
| `BS1` | Base Boat |
| `EN7` / `ENG` | Engine |
| `ACC` | Accessories |
| `L2` | Level 2 options |
| `MTR` | Motor options |
| `OA` | Optional accessories |
| `PL` | Pontoons |
| `DC` | Deck components |
| `ENI` | Engine installation |

### 3. `cfg_attr_mst` - Configuration Attributes Master

**Contains customer configuration choices.**

**Key Fields:**
| Field | Description |
|-------|-------------|
| `config_id` | Configuration ID (joins to coitem_mst) |
| `attr_name` | Attribute name (e.g., "Performance Package") |
| `attr_value` | Selected value |
| `Uf_BENN_Cfg_Value` | Configuration value |
| `comp_id` | Component ID |

**Key Attributes Imported:**
- Performance Package
- Fuel type
- Console type
- Canvas/Exterior colors
- Captain's/Co-Captain's chairs
- Trim accents
- Base vinyl
- Flooring
- Furniture upgrades
- Tables (Bow/Aft)
- Rockford Fosgate Stereo
- Main/Additional displays
- Bimini tops (Aft/Bow)
- Arch options
- Steering wheels
- Lifting strakes
- Saltwater package

### 4. `inv_item_mst` - Invoice Item Master

**Links order lines to invoices.**

**Key Fields:**
| Field | Description |
|-------|-------------|
| `co_num` | Order number |
| `co_line` | Line number |
| `co_release` | Release number |
| `inv_num` | Invoice number |

### 5. `arinv_mst` - Accounts Receivable Invoice

**Contains invoice dates.**

**Key Fields:**
| Field | Description |
|-------|-------------|
| `inv_num` | Invoice number |
| `inv_date` | Invoice date |

---

## Python Import Scripts

### 1. `import_line_items.py`

**Purpose:** Import line items with pricing from `coitem_mst`

**Query:**
```sql
SELECT
    LEFT(coi.co_num, 30) AS ERP_OrderNo,
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS BoatSerialNo,
    LEFT(coi.Uf_BENN_BoatModel, 14) AS BoatModelNo,
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
    LEFT(im.Uf_BENN_Series, 5) AS Series,
    coi.co_line AS LineNo,
    LEFT(coi.item, 30) AS ItemNo,
    LEFT(im.description, 255) AS ItemDescription,
    LEFT(im.product_code, 10) AS ItemMasterProdCat,
    coi.qty_ordered AS QuantityOrdered,
    coi.qty_invoiced AS QuantitySold,
    CAST(coi.price AS DECIMAL(10,2)) AS UnitPrice,
    CAST((coi.price * coi.qty_ordered) AS DECIMAL(10,2)) AS ExtendedPrice,
    LEFT(iim.inv_num, 30) AS InvoiceNo,
    CASE WHEN ah.inv_date IS NOT NULL 
         THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112)) 
         ELSE NULL END AS InvoiceDate
FROM [CSISTG].[dbo].[coitem_mst] coi
LEFT JOIN [CSISTG].[dbo].[item_mst] im 
    ON coi.item = im.item AND coi.site_ref = im.site_ref
LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim 
    ON coi.co_num = iim.co_num 
    AND coi.co_line = iim.co_line 
    AND coi.co_release = iim.co_release 
    AND coi.site_ref = iim.site_ref
LEFT JOIN [CSISTG].[dbo].[arinv_mst] ah 
    ON iim.inv_num = ah.inv_num AND iim.site_ref = ah.site_ref
WHERE coi.site_ref = 'BENN' 
  AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL 
  AND coi.Uf_BENN_BoatSerialNumber != ''
  AND coi.item IS NOT NULL 
  AND im.product_code IN ('ACC', 'BS1', 'L2', 'MTR', 'OA', 'PL', 'DC', 'ENG', 'ENI')
  AND coi.RecordDate >= DATEADD(day, -90, GETDATE())
ORDER BY coi.co_num, coi.co_line
```

**Filters:**
- Only `site_ref = 'BENN'` (Bennington site)
- Only boats with serial numbers
- Only specific product codes
- Last 90 days (for simple query variant)

**Destination:** `BoatOptions25_test` table in MySQL

### 2. `import_configuration_attributes.py`

**Purpose:** Import configuration attributes from `cfg_attr_mst`

**Query:**
```sql
SELECT
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS BoatSerialNo,
    LEFT(coi.Uf_BENN_BoatModel, 14) AS BoatModelNo,
    LEFT(coi.co_num, 30) AS ERP_OrderNo,
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
    LEFT(coi.config_id, 50) AS ConfigID,
    LEFT(attr.attr_name, 100) AS AttrName,
    LEFT(attr.attr_value, 255) AS AttrValue,
    LEFT(attr.Uf_BENN_Cfg_Value, 255) AS CfgValue,
    LEFT(attr.comp_id, 50) AS CompID,
    LEFT(im.Uf_BENN_Series, 5) AS Series,
    LEFT(iim.inv_num, 30) AS InvoiceNo,
    CASE WHEN ah.inv_date IS NOT NULL 
         THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112)) 
         ELSE NULL END AS InvoiceDate
FROM [CSISTG].[dbo].[coitem_mst] coi
INNER JOIN [CSISTG].[dbo].[cfg_attr_mst] attr 
    ON coi.config_id = attr.config_id AND coi.site_ref = attr.site_ref
LEFT JOIN [CSISTG].[dbo].[item_mst] im 
    ON coi.item = im.item AND coi.site_ref = im.site_ref
LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim 
    ON coi.co_num = iim.co_num 
    AND coi.co_line = iim.co_line 
    AND coi.co_release = iim.co_release 
    AND coi.site_ref = iim.site_ref
LEFT JOIN [CSISTG].[dbo].[arinv_mst] ah 
    ON iim.inv_num = ah.inv_num AND iim.site_ref = ah.site_ref
WHERE coi.config_id IS NOT NULL
  AND coi.site_ref = 'BENN'
  AND attr.attr_name IS NOT NULL
  AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL
  AND coi.Uf_BENN_BoatSerialNumber != ''
  AND attr.attr_name IN (
      'Performance Package', 'Fuel', 'Console', 'Canvas Color',
      'Captain''s Chairs', 'Co-Captain''s Chairs', 'Trim Accents',
      'BASE VINYL', 'FLOORING', 'FURNITURE UPGRADE',
      'Tables - Bow', 'Tables - Aft', 'Rockford Fosgate Stereo',
      'Main Display', 'Additional Display', 'Exterior Color Packages',
      'Bimini Cable Stays', 'Aft Bimini Tops', 'Bow Bimini Tops',
      'Arch', 'Steering Wheels', 'Lifting Strakes', 'Saltwater Package'
  )
ORDER BY coi.co_num, attr.attr_name
```

**Destination:** `BoatConfigurationAttributes` table in MySQL

---

## Data Usage

### Window Sticker Generation

The MSSQL data is used to calculate **actual MSRP** for sold boats:

```sql
-- Calculate MSRP breakdown from BoatOptions
SELECT
    SUM(CASE WHEN ItemMasterProdCat='BS1' THEN ExtSalesAmount END) as base_boat,
    SUM(CASE WHEN ItemMasterProdCat='EN7' THEN ExtSalesAmount END) as engine,
    SUM(CASE WHEN ItemMasterProdCat='ACC' THEN ExtSalesAmount END) as accessories
FROM BoatOptions25_test
WHERE BoatSerialNo = 'ETWP6278J324'
```

**Example Output:**
```
Base Boat:      $25,895.00 (BS1 items)
Engine Package: $9,011.00  (EN7/ENG items)
Accessories:    $712.00    (ACC items)
─────────────────────────────
TOTAL MSRP:     $35,618.00
```

### Business Model

```
┌─────────────────────────────────────────────────────────────┐
│  BENNINGTON MANUFACTURING                                    │
│  Builds boat → Assigns serial number (HIN)                  │
└──────────────────┬──────────────────────────────────────────┘
                   │ Sells to dealer at DEALER COST
                   │ (MSRP minus dealer margin %)
                   │ Example: $29,562.94
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  DEALER (e.g., NICHOLS MARINE - NORMAN)                     │
│  • Buys at dealer cost ($29,562.94)                         │
│  • MSRP is $35,618.00                                        │
│  • Margin: 17% (saves $6,055.06)                            │
└──────────────────┬──────────────────────────────────────────┘
                   │ Sells to customer at MSRP or negotiated
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  END CUSTOMER                                                │
│  • Pays at or near MSRP ($35,618)                           │
│  • Dealer profit = Customer price - Dealer cost             │
└─────────────────────────────────────────────────────────────┘
```

---

## Comparison: MSSQL vs CPQ Data

| Aspect | MSSQL/CSI ERP | CPQ API |
|--------|---------------|---------|
| **Data Type** | Actual sales data | Catalog/base model data |
| **Boats** | Only sold boats with serial numbers | All models in catalog |
| **Pricing** | Real prices paid by dealers | MSRP/base pricing |
| **Use Case** | Window stickers for actual boats | Planning and quotes for new orders |
| **Timeframe** | Historical (all years) | Current model year (2025+) |
| **Update Frequency** | Imported periodically | Nightly sync via JAMS |

---

## Key Differences from CPQ

1. **Serial Numbers:** MSSQL data has actual HINs (Hull Identification Numbers) for sold boats
2. **Real Prices:** Shows what dealers actually paid, not just catalog MSRP
3. **Configuration History:** Records what customers actually configured
4. **Invoice Data:** Links to actual invoices and billing
5. **Legacy Support:** Covers all years, not just 2025+ CPQ models

---

## MySQL Destination Tables

After import, MSSQL data is stored in:

### `BoatOptions25_test`
- **Purpose:** Line items with pricing for sold boats
- **Key Fields:** ERP_OrderNo, BoatSerialNo, BoatModelNo, ItemNo, ItemDesc1, ItemMasterProdCat, QuantitySold, ExtSalesAmount, InvoiceNo, InvoiceDate
- **Product Categories:** BS1, EN7, ACC, etc.

### `BoatConfigurationAttributes`
- **Purpose:** Configuration choices for sold boats
- **Key Fields:** boat_serial_no, boat_model_no, erp_order_no, web_order_no, config_id, attr_name, attr_value, cfg_value, series

### `SerialNumberMaster`
- **Purpose:** Master registry of all boats produced
- **Key Fields:** SerialNumber, BoatModel, DealerID, InvoiceDate
- **Records:** 62,781+ boats

---

## Script Execution

### Prerequisites
```bash
pip install pymssql mysql-connector-python
```

### Run Import
```bash
# Import configuration attributes and line items
python3 import_configuration_attributes.py

# Import just line items
python3 import_line_items.py
```

### What Happens
1. Connects to MSSQL using pymssql
2. Extracts data with filters (BENN site, has serial, specific product codes)
3. Loads to MySQL (warrantyparts_test)
4. Shows summary statistics

---

## Data Quality Notes

- **Site Filter:** Only `site_ref = 'BENN'` records are imported
- **Serial Required:** Only boats with `Uf_BENN_BoatSerialNumber` are included
- **Product Codes:** Limited to: ACC, BS1, L2, MTR, OA, PL, DC, ENG, ENI, EN7
- **Date Range:** Simple query variant limits to last 90 days
- **Duplicates:** Import uses `ON DUPLICATE KEY UPDATE` to handle re-imports

---

## Troubleshooting

### Connection Issues
- Verify server: MPL1STGSQL086.POLARISSTAGE.COM is accessible
- Check credentials: svccsimarine / CNKmoFxEsXs0D9egZQXH
- Ensure pymssql is installed: `pip install pymssql`

### No Data Imported
- Check if BENN site exists in coitem_mst
- Verify there are recent orders with serial numbers
- Try the simple query variant (last 90 days)

### Missing Product Codes
- Review item_mst.product_code values
- Update the IN clause if new codes are added

---

## Related Files

- `import_line_items.py` - Line items import script
- `import_configuration_attributes.py` - Configuration import script
- `diagnose_order_mismatch.py` - Order matching diagnostics
- `generate_window_sticker_with_pricing.py` - Uses BoatOptions for MSRP calculation
- `upload_margin.py` - Uploads dealer margins (separate from MSSQL)

---

## Last Updated

January 29, 2026
