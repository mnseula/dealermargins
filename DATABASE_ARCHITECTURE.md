# Database Architecture - MSSQL to MySQL Import for CPQ Window Stickers

## Overview

This document describes the complete database architecture for importing boat configuration and sales data from SyteLine ERP (MSSQL) to the MySQL window sticker database. This is the **second biggest selling feature** in the company.

## System Architecture

```
SyteLine ERP (MSSQL)  →  Python Import Script  →  MySQL (Window Sticker DB)  →  JavaScript (Window Sticker UI)
```

---

## MSSQL Source Database (SyteLine ERP)

**Server:** MPL1STGSQL086.POLARISSTAGE.COM
**Database:** CSISTG
**Purpose:** Enterprise Resource Planning (ERP) system containing all order, inventory, and configuration data

### Core Tables

#### `coitem_mst` - Order Line Items
**Purpose:** Central table containing ALL order line items (both CPQ and non-CPQ boats)

**Key Fields:**
- `co_num` - Order number (e.g., "SO00936068")
- `co_line` - Line number within order
- `co_release` - Release number
- `item` - Item code
- `config_id` - Configuration ID (CPQ boats only, NULL for non-CPQ)
- `price` - Line item price
- `qty_invoiced` - Quantity invoiced
- `Uf_BENN_BoatSerialNumber` - Boat serial number
- `Uf_BENN_BoatModel` - Boat model number
- `Uf_BENN_BoatWebOrderNumber` - Web order number
- `site_ref` - Site reference (always 'BENN')

**Usage:**
- **Part 1 Query:** Gets physical line items for ALL boats (CPQ and non-CPQ)
- **Part 2 Query:** Joins to cfg_attr_mst to get configuration attributes for CPQ boats only

---

#### `cfg_main_mst` - Configuration Header
**Purpose:** One row per CPQ configuration (header record)

**Key Fields:**
- `config_id` - Configuration ID (links to coitem_mst and cfg_attr_mst)
- `config_hdr_id` - Configuration header ID
- `site_ref` - Site reference

**Usage:**
- Identifies CPQ boats (if config_id exists, it's a CPQ boat)
- Not directly used in import (we use cfg_attr_mst which has config_id)

---

#### `cfg_attr_mst` - Configuration Attributes ⭐ CRITICAL FOR CPQ
**Purpose:** Contains ALL configuration attributes for CPQ boats (multiple rows per boat)

**Key Fields:**
- `config_id` - Configuration ID (links to coitem_mst)
- `attr_name` - Attribute name (e.g., "Battery Switching", "Base Boat", "ACCENT PANEL COLOR")
- `attr_value` - Attribute value (e.g., "Single Battery Switch", "22SFC", "No Accent")
- `print_flag` - **CRITICAL FILTER**
  - **'E'** = Exportable/External/User-facing attributes (IMPORT THESE)
  - **'I'** = Internal/System attributes (SKIP THESE)
- `Uf_BENN_Cfg_Price` - Individual attribute price (e.g., $126 for Battery Switching)
- `Uf_BENN_Cfg_MSRP` - Individual attribute MSRP
- `sl_field` - SyteLine field reference
- `attr_type` - Attribute type (Schema, String, etc.)
- `site_ref` - Site reference

**Important:**
- **print_flag = 'E'** gives ~56-61 user-facing attributes per boat
- **print_flag = 'I'** gives ~108 internal system attributes per boat
- **We ONLY import print_flag = 'E'** to avoid internal attributes

**Example Data (SO00936068):**
| attr_name | attr_value | print_flag | Uf_BENN_Cfg_Price |
|-----------|-----------|------------|-------------------|
| Base Boat | 22SFC | E | $29,847.00 |
| Battery Switching | Single Battery Switch | E | $126.00 |
| Engine Rigging | Single Engine Rigging (50-115 HP) | E | $1,349.00 |
| ACCENT PANEL COLOR | No Accent | E | $0.00 |

---

#### `cfg_comp_mst` - Configuration Components
**Purpose:** Component definitions for configurations

**Key Fields:**
- `config_id` - Configuration ID
- `comp_name` - Component name
- `comp_id` - Component ID

**Usage:**
- Optionally used for component-level details (not currently imported)

---

#### `item_mst` - Item Master
**Purpose:** Master item catalog with product classifications

**Key Fields:**
- `item` - Item code
- `Uf_BENN_MaterialCostType` - Material Cost Type (MCT) - e.g., 'BOA', 'ENG', 'ACC'
- `Uf_BENN_ProductCategory` - Product category code
- `Uf_BENN_Series` - Boat series

**Usage:**
- Provides MCT and product category for filtering
- Linked to coitem_mst for physical items

---

#### `serial_mst` - Serial Numbers
**Purpose:** Serial number tracking for boats

**Key Fields:**
- `ser_num` - Serial number
- `ref_num` - Reference order number
- `ref_line` - Reference line number
- `ref_type` - Reference type ('O' for Order)
- `item` - Item code

**Usage:**
- Links serial numbers to order line items

---

#### `inv_item_mst` - Invoice Items
**Purpose:** Invoice line item details

**Key Fields:**
- `inv_num` - Invoice number
- `co_num` - Order number
- `co_line` - Order line number
- `co_release` - Order release number

**Usage:**
- Links orders to invoices
- Filter: Only import invoiced items (iim.inv_num IS NOT NULL)

---

#### `arinv_mst` - Invoice Header
**Purpose:** Invoice header with dates

**Key Fields:**
- `inv_num` - Invoice number
- `inv_date` - Invoice date
- `apply_to_inv_num` - Applied to invoice number (for credits)

**Usage:**
- Provides invoice dates for filtering (e.g., >= '2025-12-14')

---

#### `co_mst` - Order Header
**Purpose:** Order header information

**Key Fields:**
- `co_num` - Order number
- `order_date` - Order date
- `type` - Order type
- `external_confirmation_ref` - External confirmation reference

**Usage:**
- Provides order-level data
- Filter by order_date for date ranges

---

#### `prodcode_mst` - Product Code Master
**Purpose:** Product code descriptions

**Key Fields:**
- `product_code` - Product code
- `description` - Description (MCT description)

**Usage:**
- Provides MCT descriptions (e.g., "PONTOONS", "ENGINES")

---

## MySQL Destination Database (Window Sticker)

**Server:** ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com
**Database:**
- `warrantyparts_boatoptions_test` (TEST)
- `warrantyparts_test` (PRODUCTION)

**Purpose:** Stores boat options and configuration data for window sticker generation

### Table Structure

#### `BoatOptions[YY]` - Boat Options by Year
**Examples:** BoatOptions26, BoatOptions25, BoatOptions24

**Purpose:** One table per model year containing both physical line items and configuration attributes

**Key Fields:**
- `ERP_OrderNo` - Order number (PRIMARY KEY part 1)
- `LineSeqNo` - Line sequence number (PRIMARY KEY part 2, generated via ROW_NUMBER())
- `ItemNo` - Item number OR attribute name (e.g., "Battery Switching", "ACCENT PANEL COLOR")
- `ItemDesc1` - Item description OR attribute value (e.g., "Single Battery Switch", "No Accent")
- `ExtSalesAmount` - **Individual price** (NOT boat total)
  - For physical items: `price * qty_invoiced`
  - For config attributes: `Uf_BENN_Cfg_Price`
- `ValueText` - Attribute value (for CPQ attributes)
- `ConfigID` - Configuration GID (e.g., "BENN0000000000000000000000005299")
- `BoatSerialNo` - Boat serial number
- `BoatModelNo` - Boat model number
- `InvoiceNo` - Invoice number
- `InvoiceDate` - Invoice date (YYYYMMDD format)
- `QuantitySold` - Quantity sold
- `ItemMasterMCT` - Material Cost Type (BOA, ENG, ACC, etc.)
- `ItemMasterProdCat` - Product category code
- `ItemMasterProdCatDesc` - Product category description
- `MCTDesc` - MCT description (PONTOONS, ENGINES, etc.)
- `WebOrderNo` - Web order number
- `C_Series` - Boat series
- `Orig_Ord_Type` - Original order type
- `OptionSerialNo` - Option serial number
- `LineNo` - Original line number
- `ApplyToNo` - Apply to number (for credits)
- `order_date` - Order date
- `external_confirmation_ref` - External confirmation reference

**Primary Key:** (`ERP_OrderNo`, `LineSeqNo`)

**Data Types:**
- **Non-CPQ boats:** Only physical items (engines, accessories, boat hull)
- **CPQ boats:** Physical items (Part 1) + Configuration attributes (Part 2)

---

## Import Query Architecture

### Two-Part UNION Query

The import uses a **UNION ALL** query with two distinct parts:

```sql
Part 1: Physical Line Items (ALL boats)
UNION ALL
Part 2: Configuration Attributes (CPQ boats only)
```

---

### Part 1: Physical Line Items (Non-CPQ Logic)

**Purpose:** Import physical line items for ALL boats (CPQ and non-CPQ)

**Source:** `coitem_mst` with standard joins

**Key Logic:**
```sql
FROM coitem_mst coi
LEFT JOIN inv_item_mst iim ON (order matching)
LEFT JOIN arinv_mst ah ON (invoice matching)
LEFT JOIN co_mst co ON (order header)
LEFT JOIN item_mst im ON (item details)
LEFT JOIN prodcode_mst pcm ON (MCT descriptions)
LEFT JOIN serial_mst ser ON (serial numbers)
WHERE
  coi.site_ref = 'BENN'
  AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL
  AND iim.inv_num IS NOT NULL  -- Only invoiced items
  AND coi.qty_invoiced > 0
  AND co.order_date >= '2025-12-14'
```

**ExtSalesAmount Calculation:**
```sql
CAST((coi.price * coi.qty_invoiced) AS DECIMAL(10,2)) AS [ExtSalesAmount]
```
*Standard line item pricing: price × quantity*

**ConfigID:**
```sql
'' AS [ConfigID]  -- Empty for non-CPQ boats
```

**What This Gets:**
- Boat hull/base
- Engines
- Physical accessories
- Standard line items
- Works for **both CPQ and non-CPQ boats**

**Comparison to C# Code:**
- ✅ Similar logic to original C# import for non-CPQ boats
- ✅ Avoids RowPointer issues from C# version
- ✅ Uses standard line item pricing

---

### Part 2: Configuration Attributes (CPQ-Only Logic)

**Purpose:** Import configuration attributes ONLY for CPQ boats

**Source:** `coitem_mst` with **INNER JOIN to cfg_attr_mst**

**Key Logic:**
```sql
FROM coitem_mst coi
INNER JOIN cfg_attr_mst attr_detail  -- INNER JOIN = CPQ boats only
    ON coi.config_id = attr_detail.config_id
    AND coi.site_ref = attr_detail.site_ref
    AND attr_detail.attr_value IS NOT NULL
    AND attr_detail.print_flag = 'E'  -- ⭐ CRITICAL: User-facing attributes only
-- (same joins as Part 1 for invoice, order, etc.)
```

**Critical Filter:**
```sql
attr_detail.print_flag = 'E'
```
- **'E'** = ~56-61 user-facing attributes (Battery Switching, Base Boat, etc.)
- **'I'** = ~108 internal system attributes (SKIP THESE)

**ItemNo Mapping:**
```sql
LEFT(attr_detail.attr_name, 50) AS [ItemNo]
```
*Uses attribute name directly (e.g., "Battery Switching", "ACCENT PANEL COLOR")*

**ExtSalesAmount Calculation:**
```sql
CAST(ISNULL(attr_detail.Uf_BENN_Cfg_Price, 0) AS DECIMAL(10,2)) AS [ExtSalesAmount]
```
*⭐ CRITICAL FIX: Individual attribute pricing, NOT boat total*

**ConfigID:**
```sql
LEFT(coi.config_id, 30) AS [ConfigID]
```
*Configuration GID (e.g., "BENN0000000000000000000000005299")*

**What This Gets:**
- Base Boat with price (e.g., $29,847)
- Battery Switching with price (e.g., $126)
- Engine Rigging with price (e.g., $1,349)
- All user-selected configuration options
- Standard features (price = $0)

**What Changed (The Fix):**

**Before (WRONG):**
```sql
CAST((coi.price * coi.qty_invoiced) AS DECIMAL(10,2)) AS [ExtSalesAmount]
-- Result: ALL attributes showed boat total ($32,757) ❌
```

**After (CORRECT):**
```sql
CAST(ISNULL(attr_detail.Uf_BENN_Cfg_Price, 0) AS DECIMAL(10,2)) AS [ExtSalesAmount]
-- Result: Each attribute shows individual price ✅
```

---

## Data Flow Examples

### Example 1: CPQ Boat (SO00936068)

**MSSQL Source:**
- Order: SO00936068
- config_id: "BENN0000000000000000000000005299"
- cfg_attr_mst rows with print_flag='E': 56 rows

**MySQL Result:**
- BoatOptions26 rows: 56 configuration attributes
- ItemNo examples:
  - "Base Boat" → $29,847.00
  - "Battery Switching" → $126.00
  - "Engine Rigging" → $1,349.00
  - "ACCENT PANEL COLOR" → $0.00 (standard)
- Total: $32,757.00

**Query Path:**
- Part 1: Physical items (if any engines/accessories as separate line items)
- Part 2: All 56 configuration attributes from cfg_attr_mst

---

### Example 2: Non-CPQ Boat (Hypothetical SO00999999)

**MSSQL Source:**
- Order: SO00999999
- config_id: NULL (no configuration)
- No rows in cfg_attr_mst

**MySQL Result:**
- BoatOptions26 rows: Physical line items only
- ItemNo examples:
  - Boat hull line item
  - Engine line item
  - Accessory line items
- ExtSalesAmount: price × qty_invoiced

**Query Path:**
- Part 1: Physical items ONLY
- Part 2: SKIPPED (no config_id, INNER JOIN fails)

---

## Key Design Decisions

### 1. Why print_flag = 'E' Instead of Other Filters?

**Problem:** Need to separate user-facing attributes from internal system attributes

**Solution:** Use `print_flag = 'E'` filter

**Why:**
- ✅ Explicit flag in source system for "exportable" attributes
- ✅ Gets exactly 56-61 attributes per boat (user-facing)
- ✅ Excludes 108 internal system attributes
- ✅ Future-proof: New attributes automatically included if marked 'E'

**Rejected Alternatives:**
- ❌ `attr_name = 'Description'` - Too restrictive, only gets 1 attribute
- ❌ `attr_type = 'Schema'` - Doesn't distinguish user vs system attributes
- ❌ `sl_field = 'jobmatl.description'` - Too specific to one field type

---

### 2. Why Uf_BENN_Cfg_Price Instead of coi.price?

**Problem:** All configuration attributes were showing boat total price ($32,757) instead of individual prices

**Solution:** Use `attr_detail.Uf_BENN_Cfg_Price` for Part 2

**Why:**
- ✅ `Uf_BENN_Cfg_Price` = Individual attribute price (e.g., $126 for Battery Switching)
- ✅ `coi.price * coi.qty_invoiced` = Total boat price (same for all attributes)
- ✅ Allows accurate breakdown of boat pricing by component

**Impact:**
- **Before:** All 56 attributes showed $32,757 (boat total) ❌
- **After:** Each attribute shows individual price ✅

---

### 3. Why UNION ALL Instead of Separate Queries?

**Problem:** Need both physical items AND configuration attributes in same table

**Solution:** Single UNION ALL query

**Why:**
- ✅ Single import process handles all boat types
- ✅ Consistent table structure for CPQ and non-CPQ boats
- ✅ ROW_NUMBER() generates sequential LineSeqNo across both parts
- ✅ Simplifies downstream JavaScript consumption

---

### 4. Why ROW_NUMBER() for LineSeqNo?

**Problem:** Need unique line numbers combining Part 1 and Part 2 results

**Solution:**
```sql
ROW_NUMBER() OVER(PARTITION BY coi.co_num ORDER BY coi.co_line) AS LineSeqNo
```

**Why:**
- ✅ Generates sequential numbers starting at 1 for each order
- ✅ Works across UNION ALL parts
- ✅ Stable ordering (by co_line)
- ✅ Avoids gaps in numbering

**Primary Key:** (`ERP_OrderNo`, `LineSeqNo`)

---

### 5. Why LEFT vs INNER Joins?

**Part 1:** Uses LEFT joins to item_mst, serial_mst, etc.
- Some data may be optional (serial numbers might not be linked yet)

**Part 2:** Uses INNER JOIN to cfg_attr_mst
- CPQ boats MUST have configuration attributes
- INNER JOIN filters to only CPQ boats automatically

---

## Import Script Details

**File:** `import_boatoptions_test.py`

**Process:**
1. Connect to MSSQL (SyteLine)
2. Execute two-part UNION query
3. Fetch all rows
4. Group rows by target table (BoatOptions[YY] based on serial year)
5. Connect to MySQL
6. UPSERT data using ON DUPLICATE KEY UPDATE
7. Verify final counts

**UPSERT Logic:**
```sql
INSERT INTO BoatOptions26 (...)
VALUES (...)
ON DUPLICATE KEY UPDATE
  ItemNo = VALUES(ItemNo),
  ItemDesc1 = VALUES(ItemDesc1),
  ExtSalesAmount = VALUES(ExtSalesAmount),
  ...
```

**Key:** (`ERP_OrderNo`, `LineSeqNo`)

**Important:**
- Upsert updates existing rows but doesn't delete orphaned rows
- Best practice: Delete test orders before re-import to avoid stale data

---

## JavaScript Integration

**Files:**
- `packagePricing.js` - Loads boat options data
- `window_sticker.js` - Generates window stickers

**Data Loading:**
```javascript
window.boatoptions = loadByListName('BoatOptions26', "WHERE ...");
```

**Filters Applied:**
- Excludes certain MCTs: DIC, DIF, DIP, DIR, DIA, DIW, LOY, PRD, VOD, etc.
- Filters by InvoiceNo and/or ERP_OrderNo
- Orders by MCTDesc (PONTOONS, ENGINES, PRERIG, etc.)

**Usage:**
- Window sticker displays all configuration attributes with pricing
- Works seamlessly for both CPQ and non-CPQ boats
- CPQ boats show detailed configuration breakdown
- Non-CPQ boats show physical items only

---

## Testing & Verification

### Test Orders

**SO00936068:**
- Expected: 56 configuration attributes
- Result: ✅ 56 rows
- Pricing: ✅ Individual prices (5 unique values)
- Match rate: ✅ 98.2% attribute name match (55/56)

**SO00936066:**
- Expected: 61 configuration attributes
- Result: ✅ 61 rows
- Pricing: ✅ Individual prices (5 unique values)

### Verification Queries

**Check row count:**
```sql
SELECT
    ERP_OrderNo,
    COUNT(*) as total_rows
FROM BoatOptions26
WHERE ERP_OrderNo IN ('SO00936066', 'SO00936068')
GROUP BY ERP_OrderNo;
```

**Check pricing diversity:**
```sql
SELECT
    ERP_OrderNo,
    COUNT(DISTINCT ExtSalesAmount) as unique_prices,
    MIN(ExtSalesAmount) as min_price,
    MAX(ExtSalesAmount) as max_price,
    SUM(ExtSalesAmount) as total_amount
FROM BoatOptions26
WHERE ERP_OrderNo = 'SO00936068';
```

**Expected Result:**
- Unique prices: 5+ (not just 1)
- Min price: $0.00 (standard features)
- Max price: ~$29,847 (Base Boat)
- Total: Boat total price

---

## Critical Success Factors

### ✅ Correct Filters
- `print_flag = 'E'` - Gets user-facing attributes only
- `iim.inv_num IS NOT NULL` - Only invoiced items
- `coi.qty_invoiced > 0` - Only sold items
- `co.order_date >= '2025-12-14'` - Date range filtering

### ✅ Correct Pricing
- Part 1: `coi.price * coi.qty_invoiced` for physical items
- Part 2: `attr_detail.Uf_BENN_Cfg_Price` for configuration attributes

### ✅ Correct Attribute Names
- Use `attr_detail.attr_name` directly
- 98.2% match rate with source data
- Minor trailing spaces acceptable

### ✅ Backward Compatibility
- Non-CPQ boats continue to work (Part 1 only)
- CPQ boats get enhanced data (Part 1 + Part 2)
- No breaking changes to existing boats

---

## Business Impact

**Importance:** Second biggest selling feature in the company

**Capabilities Enabled:**
1. **Window Stickers:** Complete pricing breakdown for customers
2. **Configuration Display:** Show all customer selections and upgrades
3. **Pricing Transparency:** Individual component pricing visible
4. **CPQ Integration:** Seamless integration with Infor CPQ system
5. **Historical Compatibility:** Works with old non-CPQ boats and new CPQ boats

**Users:**
- Dealers generating window stickers
- Sales team reviewing boat configurations
- Customers viewing detailed pricing

---

## Maintenance Notes

### Adding New Model Years

1. Create new table: `BoatOptions27` (for 2027)
2. Update year detection logic in import script
3. Update JavaScript to reference new table name

### Troubleshooting

**Problem:** Missing configuration attributes
**Check:**
- Verify `print_flag = 'E'` filter is present
- Check if boat has config_id in MSSQL
- Verify cfg_attr_mst has rows for that config_id

**Problem:** All prices the same
**Check:**
- Verify Part 2 uses `attr_detail.Uf_BENN_Cfg_Price`
- Should NOT use `coi.price * coi.qty_invoiced` in Part 2

**Problem:** Too many attributes (100+ rows)
**Check:**
- Verify `print_flag = 'E'` filter (not getting 'I' internal attributes)

**Problem:** Attribute name mismatches
**Check:**
- Verify using `attr_detail.attr_name` directly
- Consider adding RTRIM() if trailing spaces are an issue

---

## Related Documentation

- `CPQ_IMPORT_FIX.md` - Details of the pricing fix
- `CLAUDE.md` - Overall project documentation
- `import_boatoptions_test.py` - Import script source code

---

## Version History

**2026-02-04:** Individual attribute pricing fix
- Changed Part 2 to use `Uf_BENN_Cfg_Price`
- Verified with test orders SO00936068 and SO00936066
- Documented complete database architecture

**Previous:** C# version (non-CPQ boats only)
- Had RowPointer issues
- Did not support CPQ configuration attributes
