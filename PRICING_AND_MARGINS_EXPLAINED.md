# Pricing and Dealer Margins - How It Works

## Your Question

> "How do we determine the price and the dealer margins, discounts etc. Is all the information derived from the BoatOptions table?"

## Short Answer

**NO** - The BoatOptions table provides the **dealer cost** (what the dealer paid), but **dealer margins, volume discounts, freight, and prep** come from **other sources** in the Infor CPQ system (stored in CPQ variables/lists).

---

## Data Sources

### 1. BoatOptions Table (MySQL)
**Source:** Imported from MSSQL ERP system via `import_boatoptions_test.py`

**What it provides:**
- `ExtSalesAmount` → **Dealer Cost** (what dealer paid for each item)
- `ItemNo` → Item/attribute name
- `ItemDesc1` → Item/attribute description
- `MCTDesc` → Material Cost Type (PONTOONS, ENGINES, PRE-RIG, etc.)
- `QuantitySold` → Quantity
- `BoatModelNo` → Model number
- `BoatSerialNo` → Serial number
- `InvoiceNo` → Invoice number

**What it does NOT provide:**
- ❌ Dealer margin percentages
- ❌ Volume discounts
- ❌ Freight costs
- ❌ Prep costs
- ❌ MSRP calculations
- ❌ Sale price calculations

### 2. Infor CPQ System (External Variables/Lists)
**Source:** Loaded from Infor CPQ database at runtime

**What it provides:**
- `baseboatmargin` → Base boat margin percentage (e.g., 0.73 = 27% margin)
- `enginemargin` → Engine margin percentage (e.g., 0.90 = 10% margin)
- `optionmargin` → Options/accessories margin percentage (e.g., 0.80 = 20% margin)
- `msrpMargin` → MSRP margin percentage
- `vol_disc` → Volume discount multiplier (e.g., 1.0 = no discount, 0.95 = 5% discount)
- `msrpVolume` → MSRP volume multiplier
- `msrpLoyalty` → Loyalty discount for certain series (e.g., SV series)
- `freight` → Freight cost to add
- `prep` → Prep cost to add
- `additionalCharge` → Any additional charges

**Key CPQ Lists:**
- `Product List` → Product IDs for different model years
- `Boat_Package_Pricing_20XX` → Package pricing tables
- `Boats_ListOrder_20XX` → Boat list order and series info
- `Price Descriptions` → Price description data
- `standards_matrix_20XX` → Standards matrix
- `options_matrix_20XX` → Options matrix for item lookups

---

## Calculation Flow

### Step 1: Load Data from BoatOptions Table
```javascript
// Load from MySQL BoatOptions table (line 35 in packagePricing.js)
window.boatoptions = loadByListName('BoatOptions' + serialYear, "WHERE...");
```

**Gets:** Dealer costs for all items on the boat

### Step 2: Load Margins from CPQ System
```javascript
// These variables come from Infor CPQ system (NOT from BoatOptions)
// They are loaded elsewhere in the CPQ configuration
window.baseboatmargin  // Base boat margin (e.g., 0.73 = 27% margin)
window.enginemargin    // Engine margin (e.g., 0.90 = 10% margin)
window.optionmargin    // Options margin (e.g., 0.80 = 20% margin)
window.msrpMargin      // MSRP margin
window.vol_disc        // Volume discount (e.g., 1.0 or 0.95)
window.freight         // Freight cost
window.prep            // Prep cost
```

**Source:** Infor CPQ system variables (loaded from CPQ database/configuration)

### Step 3: Calculate Prices Using Margins
**File:** `Calculate2021.js`

#### For PONTOONS (Base Boat):
```javascript
// Line 36: Get dealer cost from BoatOptions
var dealercost = boatoptions[j].ExtSalesAmount;  // e.g., $22,000

// Line 180: Calculate sale price
boatsp = (Number(dealercost) / baseboatmargin) * vol_disc + Number(additionalCharge);

// Example calculation:
// dealercost = $22,000
// baseboatmargin = 0.73 (27% margin)
// vol_disc = 1.0 (no volume discount)
// additionalCharge = $500
// boatsp = ($22,000 / 0.73) * 1.0 + $500 = $30,137 + $500 = $30,637

// Line 189: Add freight and prep
saleboatpackageprice += ((dealercost * vol_disc) / baseboatmargin) + Number(freight) + Number(prep) + Number(additionalCharge);
```

**Formula:**
```
Sale Price = (Dealer Cost / Margin) × Volume Discount + Freight + Prep + Additional Charges
```

#### For ENGINES:
```javascript
// Line 232: Calculate engine sale price with margin
setValue('DLR2', 'ENG_FULL_W_MARGIN_SALE', Math.round(defaultengineprice / enginemargin) * vol_disc);

// Example:
// defaultengineprice = $9,000 (dealer cost)
// enginemargin = 0.90 (10% margin)
// vol_disc = 1.0
// Sale price = ($9,000 / 0.90) * 1.0 = $10,000
```

#### For OPTIONS/ACCESSORIES:
```javascript
// Line 421: Calculate option sale price
saleprice = (Number(dealercost / optionmargin) * vol_disc);

// Example:
// dealercost = $400
// optionmargin = 0.80 (20% margin)
// vol_disc = 1.0
// Sale price = ($400 / 0.80) * 1.0 = $500
```

#### For MSRP:
```javascript
// Line 414: Calculate MSRP
var msrpprice = Number((dealercost * msrpVolume) / msrpMargin);

// Example:
// dealercost = $400
// msrpVolume = 1.0
// msrpMargin = 0.70
// MSRP = ($400 * 1.0) / 0.70 = $571
```

---

## Special Discounts

### 1. Package Discounts (Hardcoded)
**File:** `Calculate2021.js` lines 56-178

These are **hardcoded** based on series and boat length:

```javascript
// Example: SV Series discounts (lines 57-66)
if(series === "SV" && boatModel.match(/188.*/)) {
    boatpackageprice = boatpackageprice - 1650;  // $1,650 discount for 18' SV
} else if (series === "SV" && boatModel.match(/20.*/)) {
    boatpackageprice = boatpackageprice - 1700;  // $1,700 discount for 20' SV
} else if (series === "SV" && boatModel.match(/22.*/)) {
    boatpackageprice = boatpackageprice - 750;   // $750 discount for 22' SV
}
```

**Discount Table:**

| Series | Length | Discount |
|--------|--------|----------|
| SV     | 18'    | $1,650   |
| SV     | 20'    | $1,700   |
| SV     | 22'    | $750     |
| S      | 18'    | $1,650   |
| S      | 20'    | $1,700   |
| S      | 22'    | $750     |
| SX     | 16'    | $1,300   |
| SX     | 18'-26'| $750-$1,700 |
| L      | 18'-26'| $750-$1,700 |
| LT     | All    | $750     |
| LX     | All    | $750     |

### 2. Value Series Discounts (From BoatOptions)
**MCT Types:** `DIS`, `DIV`, `ENZ`

```javascript
// Lines 45-46: Accumulate engine discounts
if (mctType === 'DIS' || mctType === 'DIV') {
    EngineDiscountAdditions = Number(dealercost) + Number(EngineDiscountAdditions);
}

// Line 432: Apply discount to sale price
saleprice = Number((EngineDiscountAdditions * vol_disc) / baseboatmargin);
```

These discounts **DO come from BoatOptions** table with specific MCT types.

### 3. SV Series Special Pricing (Loyalty)
```javascript
// Line 344: SV series gets additional loyalty multiplier
if (series == 'SV') {
    msrpboatpackageprice = Number((boatpackageprice * msrpVolume * msrpLoyalty) / msrpMargin) + Number(additionalCharge);
    saleboatpackageprice = Math.round(msrpboatpackageprice);
}
```

---

## Complete Example Calculation

### Scenario: 22' SV Series Boat

**From BoatOptions Table:**
- Pontoon dealer cost: $22,000
- Engine dealer cost: $9,000
- Pre-rig dealer cost: $1,500
- Accessories dealer cost: $800
- Value series discount: -$500 (MCT = DIS)

**From CPQ System:**
- baseboatmargin: 0.73 (27% margin)
- enginemargin: 0.90 (10% margin)
- optionmargin: 0.80 (20% margin)
- vol_disc: 1.0 (no volume discount)
- freight: $1,200
- prep: $800
- Series discount: -$750 (22' SV boat, hardcoded)

**Calculation:**

1. **Base Boat:**
   ```
   Dealer Cost: $22,000 - $750 (series discount) = $21,250
   Sale Price: ($21,250 / 0.73) * 1.0 + $1,200 (freight) + $800 (prep)
             = $29,109 + $1,200 + $800
             = $31,109
   ```

2. **Engine:**
   ```
   Dealer Cost: $9,000
   Sale Price: ($9,000 / 0.90) * 1.0 = $10,000
   ```

3. **Pre-rig:**
   ```
   Dealer Cost: $1,500
   Sale Price: ($1,500 / 0.80) * 1.0 = $1,875
   ```

4. **Accessories:**
   ```
   Dealer Cost: $800
   Sale Price: ($800 / 0.80) * 1.0 = $1,000
   ```

5. **Value Series Discount:**
   ```
   Dealer Cost: -$500
   Sale Price: (-$500 * 1.0) / 0.73 = -$685
   ```

**Total Sale Price:** $31,109 + $10,000 + $1,875 + $1,000 - $685 = **$43,299**

---

## Where Are Margins Stored?

### Dealer-Specific Margins
**Database:** `warrantyparts_test`
**Tables:**
- `DealerMargins` → Dealer margin percentages per dealer × series
- `Dealers` → Dealer information

**Example Query:**
```sql
SELECT
    dealer_name,
    series_id,
    base_boat_margin,
    engine_margin,
    options_margin,
    freight_margin,
    prep_margin
FROM DealerMargins
WHERE dealer_id = '00333836'  -- Nichols Marine
  AND series_id = 'QX'
  AND is_active = TRUE;
```

**Result:**
```
dealer_name: NICHOLS MARINE - NORMAN
series_id: QX
base_boat_margin: 27.00
engine_margin: 27.00
options_margin: 27.00
freight_margin: 27.00
prep_margin: 27.00
```

**NOTE:** These margins are stored in the MySQL database for CPQ boats, but the JavaScript calculation code currently uses **variables loaded from Infor CPQ**, not directly from these tables.

### How Margins Get Into JavaScript
The margins flow into JavaScript through Infor CPQ's variable system:

1. **CPQ Configuration** → Sets dealer-specific margins
2. **CPQ Runtime** → Loads margins into JavaScript window variables
3. **Calculate2021.js** → Uses margins in calculations
4. **BoatOptions table** → Provides dealer costs only

---

## Summary: Data Sources

| Data Element | Source | Example |
|--------------|--------|---------|
| **Dealer Cost** | BoatOptions table (ExtSalesAmount) | $22,000 |
| **Base Boat Margin** | CPQ system variables | 0.73 (27%) |
| **Engine Margin** | CPQ system variables | 0.90 (10%) |
| **Options Margin** | CPQ system variables | 0.80 (20%) |
| **Volume Discount** | CPQ system variables | 1.0 (none) |
| **Freight** | CPQ system variables | $1,200 |
| **Prep** | CPQ system variables | $800 |
| **Series Discounts** | Hardcoded in Calculate2021.js | $750 for 22' SV |
| **Value Discounts** | BoatOptions table (MCT = DIS/DIV/ENZ) | -$500 |
| **MSRP Margin** | CPQ system variables | 0.70 |

---

## Key Formulas

### Sale Price (General):
```
Sale Price = (Dealer Cost / Margin Percentage) × Volume Discount + Fixed Costs
```

### Margin Percentage Conversion:
```
Margin % = (1 - Margin Decimal) × 100
Examples:
  0.73 = 27% margin (dealer pays 73%, makes 27%)
  0.90 = 10% margin (dealer pays 90%, makes 10%)
  0.80 = 20% margin (dealer pays 80%, makes 20%)
```

### Dealer Savings:
```
Savings = Sale Price - Dealer Cost
Savings % = ((Sale Price - Dealer Cost) / Sale Price) × 100
```

---

## What This Means for CPQ Integration

### Challenge:
Currently, the system has **two separate margin sources**:
1. **DealerMargins table in MySQL** (from CPQ API import) - NEW
2. **CPQ runtime variables** (from Infor CPQ system) - EXISTING

### Current State:
- ✅ **DealerMargins table** is populated from CPQ API
- ❌ **JavaScript calculations** still use CPQ runtime variables (not DealerMargins table)

### Future Integration Options:

#### Option 1: Load from DealerMargins Table
Modify JavaScript to query DealerMargins table at runtime:
```javascript
// Load dealer margins from MySQL instead of CPQ variables
window.dealerMargins = loadByListName('CurrentDealerMargins',
    "WHERE dealer_name = '" + dealerName + "' AND series_id = '" + series + "'");

if (dealerMargins.length > 0) {
    window.baseboatmargin = 1 - (dealerMargins[0].base_boat_margin / 100);
    window.enginemargin = 1 - (dealerMargins[0].engine_margin / 100);
    window.optionmargin = 1 - (dealerMargins[0].options_margin / 100);
}
```

#### Option 2: Keep CPQ as Source of Truth
Continue using CPQ runtime variables and treat DealerMargins table as informational only.

#### Option 3: Hybrid Approach
Use CPQ variables for active quoting, use DealerMargins table for reporting/window stickers.

---

## Questions to Answer

1. **Where do CPQ runtime variables (baseboatmargin, etc.) come from?**
   - Loaded from Infor CPQ system configuration
   - Not directly visible in this codebase
   - Need to check CPQ admin console or configuration

2. **Should we migrate JavaScript to use DealerMargins table?**
   - Pros: Single source of truth, easier to manage
   - Cons: Requires JavaScript refactoring, potential performance impact

3. **How do we ensure BoatOptions table and DealerMargins stay in sync?**
   - Both import from same CPQ API
   - Run imports on same schedule
   - Add validation checks

4. **What about freight and prep costs?**
   - Currently hardcoded or from CPQ variables
   - Not in DealerMargins table
   - May need additional tables or fields

---

## Related Documentation

- `DATABASE_ARCHITECTURE.md` → Complete database architecture
- `CLAUDE.md` → Project overview and API credentials
- `dealer_margins_schema.sql` → DealerMargins table schema
- `stored_procedures.sql` → SQL procedures for quotes and window stickers

---

## Last Updated
2026-02-05 - Initial documentation of pricing and margin calculation flow
