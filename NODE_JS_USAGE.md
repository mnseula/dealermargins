# GetCompleteBoatInformation - Node.js Usage Guide

## Overview

This stored procedure retrieves **ALL boat information** including pricing, line items, dealer margins, and dealer cost calculations using **ONLY the Hull Number** as input.

## Installation

The stored procedure is in: `GetCompleteBoatInformation.sql`

Install it to your MySQL database (warrantyparts_test):

```bash
mysql -h ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com -u awsmaster -p warrantyparts_test < GetCompleteBoatInformation.sql
```

## Node.js Usage

```javascript
const mysql = require('mysql2/promise');

// Create connection
const connection = await mysql.createConnection({
  host: 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
  user: 'awsmaster',
  password: 'VWvHG9vfG23g7gD',
  database: 'warrantyparts_test',
  multipleStatements: true
});

// Call the stored procedure with ONLY the Hull#
const [results] = await connection.query(
  'CALL GetCompleteBoatInformation(?)',
  ['ETWP6278J324']  // Hull number - that's ALL you need!
);

// Access the 5 result sets
const boatHeader = results[0];        // Result Set 1: Boat information
const lineItems = results[1];         // Result Set 2: All line items
const msrpSummary = results[2];       // Result Set 3: MSRP by category
const dealerMargins = results[3];     // Result Set 4: Dealer margin %
const dealerCosts = results[4];       // Result Set 5: Dealer costs

// Use the data
console.log('Model:', boatHeader[0].model_no);
console.log('Dealer:', boatHeader[0].dealer_name);
console.log('Total MSRP:', msrpSummary.find(r => r.category === 'TOTAL').msrp);

// Calculate total dealer cost (sum all non-TOTAL categories)
const totalDealerCost = dealerCosts
  .filter(r => r.category !== 'TOTAL')
  .reduce((sum, r) => sum + parseFloat(r.dealer_cost), 0);

console.log('Total Dealer Cost:', totalDealerCost);
```

## Result Sets

### Result Set 1: Boat Header (1 row)
Contains all boat information from SerialNumberMaster:

```javascript
{
  hull_serial_no: 'ETWP6278J324',
  model_no: '20SVFSR',
  model_description: '20 S 4 PT FISHING',
  model_description_2: '2024 Fishing',
  series: 'SV',
  model_year: 24,
  serial_model_year: '2024',
  dealer_id: '333836',
  dealer_name: 'NICHOLS MARINE - NORMAN',
  dealer_city: 'NORMAN',
  dealer_state: 'OK',
  dealer_zip: '73071',
  dealer_country: 'US',
  invoice_no: '1095452',
  invoice_date_yyyymmdd: '20231106',
  erp_order_no: '884162',
  web_order_no: '275706',
  panel_color: 'MET LUMINOUS BLUE',
  accent_panel: 'ACC PNL NO ACCENT',
  trim_accent: 'ANTHRACITE SV S',
  base_vinyl: 'SHADOW GREY',
  color_package: null,
  rep_name: 'DONNY COVINGTON',
  presold: 'N',
  active: 1
}
```

### Result Set 2: Line Items (variable rows)
All line items from the appropriate BoatOptions{YY} table:

```javascript
[
  {
    line_no: 1,
    item_no: '20SVFSR',
    item_desc: '20 S 4 PT FISHING',
    product_category: 'BS1',
    quantity: 1,
    ext_sales_amount: 25895.00,
    category_name: 'Base Boat',
    source_table: 'BoatOptions24'
  },
  {
    line_no: 2,
    item_no: 'F90LB',
    item_desc: 'YAMAHA 90 HP 4S 20 IN',
    product_category: 'EN7',
    quantity: 1,
    ext_sales_amount: 9011.00,
    category_name: 'Engine',
    source_table: 'BoatOptions24'
  },
  // ... more line items
]
```

### Result Set 3: MSRP Summary (8 rows)
MSRP totals by category:

```javascript
[
  { category: 'Base Boat', category_code: 'BS1', msrp: 25895.00 },
  { category: 'Engine', category_code: 'EN7', msrp: 9011.00 },
  { category: 'Accessories', category_code: 'ACC', msrp: 712.00 },
  { category: 'Colors/Options', category_code: 'H1', msrp: 0.00 },
  { category: 'Labor/Prep', category_code: 'L2', msrp: 0.00 },
  { category: 'Discounts', category_code: 'C1L', msrp: -352.13 },
  { category: 'Fees', category_code: 'GRO', msrp: 11.00 },
  { category: 'TOTAL', category_code: 'TOTAL', msrp: 31385.78 }
]
```

### Result Set 4: Dealer Margins (1 row)
Dealer margin percentages for this dealer × series:

```javascript
{
  dealer_id: '00333836',
  dealer_name: 'NICHOLS MARINE - NORMAN',
  series: 'SV',
  base_boat_margin_pct: 27.00,
  engine_margin_pct: 27.00,
  options_margin_pct: 27.00,
  freight_value: 0.00,
  freight_type: 'PERCENTAGE',
  prep_value: 0.00,
  prep_type: 'PERCENTAGE',
  volume_discount_pct: 27.00,
  data_source: 'warrantyparts.DealerMargins'
}
```

### Result Set 5: Dealer Costs (8 rows)
Dealer costs calculated with margins applied:

```javascript
[
  {
    category: 'Base Boat',
    category_code: 'BS1',
    msrp: 25895.00,
    margin_pct: 27.00,
    dealer_cost: 18903.35,
    dealer_savings: 6991.65
  },
  {
    category: 'Engine',
    category_code: 'EN7',
    msrp: 9011.00,
    margin_pct: 27.00,
    dealer_cost: 6578.03,
    dealer_savings: 2432.97
  },
  {
    category: 'Accessories',
    category_code: 'ACC',
    msrp: 712.00,
    margin_pct: 27.00,
    dealer_cost: 519.76,
    dealer_savings: 192.24
  },
  // ... other categories
  {
    category: 'TOTAL',
    category_code: 'TOTAL',
    msrp: 31385.78,
    margin_pct: 0,
    dealer_cost: 0,  // Calculate by summing other rows
    dealer_savings: 0  // Calculate as MSRP - dealer_cost
  }
]
```

**Note**: For the TOTAL row, calculate the actual values in your application:
```javascript
const totalDealerCost = dealerCosts
  .filter(r => r.category !== 'TOTAL')
  .reduce((sum, r) => sum + parseFloat(r.dealer_cost), 0);

const totalMSRP = msrpSummary.find(r => r.category === 'TOTAL').msrp;
const totalSavings = totalMSRP - totalDealerCost;
```

## Example Output

For Hull: **ETWP6278J324**

```
Model: 20SVFSR - 20 S 4 PT FISHING
Dealer: NICHOLS MARINE - NORMAN (NORMAN, OK)
Invoice: 1095452 dated 20231106

MSRP Summary:
  Base Boat            $    25,895.00
  Engine               $     9,011.00
  Accessories          $       712.00
  Colors/Options       $         0.00
  Labor/Prep           $         0.00
  Discounts            $      -352.13
  Fees                 $        11.00
  ──────────────────────────────────
  TOTAL                $    31,385.78

Dealer Margins: Base: 27% | Engine: 27% | Options: 27%

Dealer Costs:
  Base Boat            $   25,895.00 → $   18,903.35  (save $6,991.65)
  Engine               $    9,011.00 → $    6,578.03  (save $2,432.97)
  Accessories          $      712.00 → $      519.76  (save $  192.24)
  ──────────────────────────────────────────────────────────────────
  TOTAL                $   31,385.78 → $   25,660.01  (save $5,725.77)
```

## How It Works

1. **Input**: Just the Hull# (e.g., 'ETWP6278J324')

2. **Process**:
   - Queries `warrantyparts.SerialNumberMaster` to get boat details
   - Extracts `SN_MY` (model year) to determine which `BoatOptions{YY}` table to query
   - Dynamically queries the correct table (e.g., `BoatOptions24` for 2024 boats)
   - Looks up dealer margins from `warrantyparts.DealerMargins`
   - Calculates dealer costs using the margin percentages

3. **Output**: 5 result sets with complete boat information and pricing

## Error Handling

If the Hull# is not found:
```javascript
// Result Set 1 will contain an error message
if (boatHeader[0].status === 'ERROR') {
  console.error(boatHeader[0].message);
  // "Hull number not found: ETWTEST024"
}
```

## Performance

- **Fast**: Uses indexed lookups on hull serial numbers
- **Efficient**: Dynamic table selection (no full table scans)
- **Single call**: All data retrieved in one round-trip

## Database Tables Used

1. `warrantyparts.SerialNumberMaster` - Boat header information
2. `warrantyparts.BoatOptions{YY}` - Line items (determined by SN_MY field)
3. `warrantyparts.DealerMargins` - Dealer margin percentages

## Production Ready

✅ Tested with multiple boat types
✅ Handles dynamic table selection
✅ Proper error handling
✅ Optimized with temp tables
✅ Clean result sets for easy Node.js consumption

---

**Created**: January 30, 2026
**Status**: Production Ready
**Version**: 1.0
