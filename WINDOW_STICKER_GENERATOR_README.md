# Window Sticker Generator - Using BoatOptions25_test Data

**Created:** January 29, 2026
**Status:** ✅ Complete and Tested

---

## Overview

This window sticker generator creates comprehensive boat window stickers using **actual sold boat data** from your MySQL database:

- **Line Items**: From `BoatOptions25_test` (loaded daily from MSSQL/coitem_mst)
- **Configuration Attributes**: From `BoatConfigurationAttributes` (loaded from cfg_attr_mst)
- **Dealer Margins**: From `warrantyparts.DealerMargins` (2,334 dealers)

## Data Flow

```
MSSQL (CSI/ERP - Source of Truth)
├─ coitem_mst (line items with pricing)
└─ cfg_attr_mst (configuration choices)
        ↓
   DataSync_Function.cs (C# .NET)
   OR import_*.py scripts
        ↓
MySQL (warrantyparts_test)
├─ BoatOptions25_test (323,272 rows, 19,113 boats)
└─ BoatConfigurationAttributes (config choices)
        ↓
   generate_window_sticker_from_boat_options.py
        ↓
   📄 Window Sticker (MSRP + Dealer Cost)
```

---

## Script: `generate_window_sticker_from_boat_options.py`

### Usage

```bash
python3 generate_window_sticker_from_boat_options.py <serial_number> [dealer_id] [display_mode]
```

### Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `serial_number` | ✅ Yes | Boat HIN/Serial Number | `ETWS1607J425` |
| `dealer_id` | ❌ No | Dealer ID (for cost calculation) | `333836` |
| `display_mode` | ❌ No | Pricing display mode | `dealer_cost` |

### Display Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `msrp_only` | Show only MSRP (default) | Customer-facing stickers |
| `dealer_cost` | Show MSRP + dealer cost | Internal dealer use |
| `no_pricing` | Show features only | Display purposes |

### Examples

```bash
# Customer-facing window sticker (MSRP only)
python3 generate_window_sticker_from_boat_options.py ETWS1607J425

# Internal dealer sticker with pricing
python3 generate_window_sticker_from_boat_options.py ETWS1607J425 333836 dealer_cost

# Features only (no prices)
python3 generate_window_sticker_from_boat_options.py ETWS1607J425 "" no_pricing
```

---

## What's Included in the Window Sticker

### 1. Boat Information
- Hull Serial Number (HIN)
- Model number
- Series
- ERP Order Number
- Invoice Number and Date

### 2. Configuration Attributes (if available)
- Performance Package
- Canvas/Exterior Colors
- Captain's Chairs
- Flooring
- Electronics (displays, stereo)
- Console type
- And more...

### 3. Line Items Categorized
Items are automatically categorized and displayed:

| Category | Product Codes | Description |
|----------|---------------|-------------|
| **Base Boat** | BS1 | Base boat package |
| **Engine** | EN7, ENG, ENI | Engine package |
| **Accessories** | ACC | Accessories and options |
| **Hull Items** | H1, H1P, H1V, H1I, H1F, H3A | Hull components |
| **Other** | All others | Miscellaneous items |

### 4. Pricing Breakdown (MSRP)
- Base Boat Package: $XX,XXX.XX
- Engine Package: $X,XXX.XX
- Accessories: $X,XXX.XX
- **TOTAL MSRP**: $XX,XXX.XX

### 5. Dealer Cost (if dealer_cost mode)
- Dealer Information (Name, ID)
- Dealer cost per category with margin %
- Total savings
- Volume discount available

---

## Sample Output

### MSRP Only Mode (Customer-Facing)

```
════════════════════════════════════════════════════════════════════
║                 BENNINGTON MARINE - WINDOW STICKER                 ║
════════════════════════════════════════════════════════════════════

📋 BOAT INFORMATION
────────────────────────────────────────────────────────────────────
   Hull Serial Number (HIN):  ETWS1607J425
   Model:                     188SLJSE
   Series:                    S
   ERP Order Number:          SO00925685
   Invoice Number:            25159673

📦 INCLUDED ITEMS
────────────────────────────────────────────────────────────────────

   ✓ BASE BOAT PACKAGE:
      • 18 S CRUISE NARROW BEAM                    $ 21,656.00

💰 PRICING
═══════════════════════════════════════════════════════════════════

   MANUFACTURER'S SUGGESTED RETAIL PRICE (MSRP):
   ────────────────────────────────────────────────────────────────
   Base Boat Package:              $   21,656.00
   Other Items:                    $       31.00
   ────────────────────────────────────────────────────────────────
   TOTAL MSRP:                     $   21,687.00
```

### Dealer Cost Mode (Internal Use)

```
💰 PRICING
═══════════════════════════════════════════════════════════════════

   MANUFACTURER'S SUGGESTED RETAIL PRICE (MSRP):
   ────────────────────────────────────────────────────────────────
   Base Boat Package:              $   21,656.00
   Other Items:                    $       31.00
   ────────────────────────────────────────────────────────────────
   TOTAL MSRP:                     $   21,687.00

   ────────────────────────────────────────────────────────────────

   DEALER INFORMATION:
   Dealer: NICHOLS MARINE - NORMAN (ID: 00333836)

   DEALER COST (Internal Use Only):
   ────────────────────────────────────────────────────────────────
   Base Boat (27.0% margin):        $   15,808.88  (save $5,847.12)
   Other Items (27.0% margin):      $       22.63  (save $8.37)
   ────────────────────────────────────────────────────────────────
   DEALER COST:                    $   15,831.51
   TOTAL SAVINGS:                  $    5,855.49

   Volume Discount Available: 27.0%
```

---

## Database Tables Used

### 1. BoatOptions25_test (warrantyparts_test)

**Source**: MSSQL coitem_mst via DataSync_Function.cs
**Rows**: 323,272 line items for 19,113 boats
**Updated**: Daily via C# sync process

**Key Fields:**
- `BoatSerialNo` - HIN
- `BoatModelNo` - Model number
- `Series` - Boat series (Q, QX, S, SV, etc.)
- `ItemNo` - Item number
- `ItemDesc1` - Item description
- `ItemMasterProdCat` - Product category (BS1, EN7, ACC, etc.)
- `QuantitySold` - Quantity
- `ExtSalesAmount` - **Extended price (unit price × quantity)**
- `InvoiceNo` - Invoice number
- `ERP_OrderNo` - ERP order number

### 2. BoatConfigurationAttributes (warrantyparts_test)

**Source**: MSSQL cfg_attr_mst via import_configuration_attributes.py
**Purpose**: Configuration choices made during boat ordering

**Key Fields:**
- `boat_serial_no` - HIN
- `attr_name` - Attribute name (e.g., "Performance Package")
- `attr_value` - Selected value
- `cfg_value` - Configuration value

### 3. DealerMargins (warrantyparts database)

**Source**: Production dealer margin data
**Rows**: 2,334 dealers
**Purpose**: Dealer margin percentages for pricing calculations

**Key Fields:**
- `DealerID` - Dealer identifier (with leading zeros)
- `Dealership` - Dealer name
- `{SERIES}_BASE_BOAT` - Base boat margin %
- `{SERIES}_ENGINE` - Engine margin %
- `{SERIES}_OPTIONS` - Options margin %
- `{SERIES}_VOL_DISC` - Volume discount %

**Series Columns Available:**
- Q, QX, QXS, R, RX, RT, G, S, SX, L, LX, LT
- S_23, SV_23, M

---

## Product Categories Explained

The script categorizes line items using `ItemMasterProdCat` field:

| Code | Category | Used For |
|------|----------|----------|
| **BS1** | Base Boat | Base boat MSRP |
| **EN7** | Engine | Engine pricing |
| **ENG** | Engine | Engine pricing (alternate) |
| **ENI** | Engine Installation | Installation charges |
| **ACC** | Accessories | Options and accessories |
| **H1, H1P, H1V, H1I, H1F, H3A** | Hull Components | Hull parts |
| **L0, L12** | Level items | Additional options |
| **090, 003, 024** | Various | Parts and components |

### MSRP Calculation Logic

```sql
Base Boat MSRP  = SUM(ExtSalesAmount WHERE ItemMasterProdCat = 'BS1')
Engine MSRP     = SUM(ExtSalesAmount WHERE ItemMasterProdCat IN ('EN7', 'ENG', 'ENI'))
Accessories     = SUM(ExtSalesAmount WHERE ItemMasterProdCat = 'ACC')
Other Items     = SUM(ExtSalesAmount WHERE ItemMasterProdCat IN ('H1', 'H1P', ...))
────────────────────────────────────────────────────────────────────
TOTAL MSRP      = Base Boat + Engine + Accessories + Other Items
```

### Dealer Cost Calculation

```
Base Boat Cost       = Base Boat MSRP × (1 - base_margin%)
Engine Cost          = Engine MSRP × (1 - engine_margin%)
Accessories Cost     = Accessories MSRP × (1 - options_margin%)
Other Items Cost     = Other Items MSRP × (1 - options_margin%)
───────────────────────────────────────────────────────────
DEALER COST          = Sum of all costs
TOTAL SAVINGS        = TOTAL MSRP - DEALER COST
```

---

## Testing

The script has been tested with:

✅ **Boat**: ETWS1607J425 (188SLJSE, S Series)
✅ **Dealer**: NICHOLS MARINE - NORMAN (333836)
✅ **Display Modes**: msrp_only, dealer_cost, no_pricing
✅ **MSRP Calculation**: $21,687.00 verified
✅ **Dealer Cost**: $15,831.51 (27% margin) verified
✅ **Data Sources**: BoatOptions25_test, DealerMargins

---

## Troubleshooting

### Boat Not Found

```
Error: Boat with serial number 'XXX' not found in BoatOptions25_test
```

**Solution**:
- Verify serial number is correct
- Check if boat data has been loaded into BoatOptions25_test
- Ensure daily sync is running (DataSync_Function.cs)

### No Dealer Margins Found

```
Warning: No dealer margins found for dealer XXX, series YYY
```

**Solution**:
- Verify dealer ID exists in warrantyparts.DealerMargins
- Check series name matches (use "S" not "S_23" for S series)
- Ensure dealer ID has leading zeros (00333836, not 333836)

### No Configuration Attributes

```
⚠️  No configuration attributes found
```

**This is normal**:
- Not all boats have configuration attributes loaded
- Older boats may not have this data
- Sticker will still show line items and pricing

---

## Next Steps

### 1. Web Integration
Integrate this script with your web interface:
- Dealer selects boat serial number
- Chooses display mode (MSRP only, dealer cost, no pricing)
- Generates PDF or HTML window sticker

### 2. Enhanced Features
- Add freight and prep costs
- Include dealer installed options
- Support special pricing promotions
- Add custom dealer notes

### 3. Data Enrichment
- Load more configuration attributes
- Backfill historical boat data
- Add performance specs
- Include standard features

---

## Related Files

- `DataSync_Function.cs` - C# data sync from MSSQL → MySQL
- `MySQL.md` - MySQL database documentation
- `MSSQL.md` - MSSQL database documentation
- `COMPLETE_SYSTEM_CONTEXT.md` - Master system documentation
- `upload_margin.py` - Upload dealer margins to CPQ

---

## Technical Details

### Dependencies
```bash
pip install mysql-connector-python
```

### Database Connection
```python
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}
```

### Series Mapping
- Most series use their direct name (Q, QX, R, S, etc.)
- SV series maps to SV_23 in DealerMargins
- S series uses S (not S_23)

### Dealer ID Format
- Database stores with leading zeros: "00333836"
- Script automatically pads: "333836" → "00333836"

---

## Summary

✅ **Complete Window Sticker Generator** using actual sold boat data
✅ **Three display modes** for different use cases
✅ **Automatic MSRP calculation** from line items
✅ **Dealer cost calculation** with margin percentages
✅ **Professional formatting** with categorized items
✅ **Production ready** and tested

**Ready to integrate with your dealer portal or run standalone!**
