# Session Context - February 2, 2026
## MAJOR BREAKTHROUGH: Pricing Formulas Discovered! 🎉

---

## What We Accomplished Today

### 1. ✅ Loaded Previous Context
- Reviewed January 30th session where we built `GetCompleteBoatInformation` stored procedure
- The procedure returned dealer cost from BoatOptions tables
- **Mystery**: Window sticker showed MSRP of $38,569 but BoatOptions showed $30,557

### 2. ✅ SOLVED THE MYSTERY!
**You provided the JavaScript code (`Calculate2021.js`) that revealed EVERYTHING!**

The MSRP is **CALCULATED**, not stored anywhere!

## The THREE Price Points

```javascript
// From Calculate2021.js

var dealercost = boatoptions[j].ExtSalesAmount;  // From BoatOptions table

// SALE PRICE (what dealer sells for)
saleprice = (dealercost * vol_disc) / baseboatmargin;

// MSRP (manufacturer's suggested retail)
msrpprice = (dealercost * msrpVolume) / msrpMargin;

// For SV series special case:
if (series == 'SV') {
    msrpprice = msrpprice * msrpLoyalty;
    saleprice = msrpprice;  // SV series uses MSRP as sale price
}
```

## The Complete Pricing Formula

### Base Boat:
- **Dealer Cost**: From BoatOptions{YY}.ExtSalesAmount
- **Sale Price**: `(dealer_cost * vol_disc) / baseboatmargin`
- **MSRP**: `(dealer_cost * msrpVolume) / msrpMargin`

### Engine:
- **Dealer Cost**: From BoatOptions{YY}.ExtSalesAmount
- **Sale Price**: `(dealer_cost * vol_disc) / enginemargin`
- **MSRP**: `(dealer_cost * msrpVolume) / msrpMargin`

### Options/Pre-Rig:
- **Dealer Cost**: From BoatOptions{YY}.ExtSalesAmount
- **Sale Price**: `(dealer_cost * vol_disc) / optionmargin`
- **MSRP**: `(dealer_cost * msrpVolume) / msrpMargin`

### Discounts/Fees:
- Pass through (no margin calculation)

## Where Variables Come From

### ✅ From DealerMargins Table (warrantyparts):
- `baseboatmargin` → `{SERIES}_BASE_BOAT` column (e.g., SV_23_BASE_BOAT = 27%)
- `enginemargin` → `{SERIES}_ENGINE` column (e.g., SV_23_ENGINE = 27%)
- `optionmargin` → `{SERIES}_OPTIONS` column (e.g., SV_23_OPTIONS = 27%)
- `vol_disc` → `{SERIES}_VOL_DISC` column (e.g., SV_23_VOL_DISC = 27%)

**Note**: These are stored as percentages (27.0 = 27%)

### ❓ UNKNOWN - Need to Find:
- `msrpMargin` - MSRP margin divisor (probably 0.75 or similar)
- `msrpVolume` - MSRP volume multiplier (probably 1.0)
- `msrpLoyalty` - SV series loyalty multiplier

**These might be:**
- Hardcoded constants in the JavaScript
- In a configuration table
- In DealerMargins (different columns we didn't see)
- Company-wide constants

## Example Calculation

**For Hull ETWP5175I324:**

### From BoatOptions24:
- Base Boat (20SVSRSR): $25,077.00 (dealer cost)
- Engine (F90LB): $9,011.00 (dealer cost)
- Accessories: $600.00 (dealer cost)

### From DealerMargins:
- Nichols Marine - Norman (SV_23 series)
- Base margin: 27%
- Engine margin: 27%
- Options margin: 27%
- Vol disc: 27%

### If we assume msrpMargin = 0.75, msrpVolume = 1.0:

**Base Boat:**
- Dealer Cost: $25,077.00
- Sale Price: `($25,077 * 1.27) / 0.27` = **$117,913** (that's wrong, margins are stored as percentages not decimals!)

**Need to convert**: 27% stored as 27.0, should divide by 100 first!

**Corrected:**
- Sale Price: `($25,077 * 1.27) / (27/100)` = $117,913 (still seems high)

**Actually from JavaScript**: `(dealercost * vol_disc) / baseboatmargin`
- Where vol_disc and margin are decimals (0.27 format)
- Need to check if DealerMargins stores as 27.0 or 0.27!

## What We Were Building

### GetCompleteBoatInformation_FINAL.sql

A stored procedure that:
1. Takes `p_hull_no`, `p_msrp_margin`, `p_msrp_volume` as parameters
2. Gets boat header from SerialNumberMaster
3. Dynamically queries BoatOptions{YY} table based on model year
4. Gets dealer margins from DealerMargins table
5. Calculates all 3 price points for each line item
6. Returns 5 result sets:
   - Result Set 1: Boat Header
   - Result Set 2: Line Items (with dealer_cost, sale_price, msrp columns)
   - Result Set 3: Pricing Summary by Category
   - Result Set 4: Dealer Margins Used
   - Result Set 5: Grand Totals

### Status: 90% Complete

**What Works:**
- ✅ Boat header retrieval
- ✅ Dynamic table selection (BoatOptions24/25/26)
- ✅ Dealer margin lookup
- ✅ Result set structure

**What's Broken:**
- ❌ SQL syntax error in dynamic query (quote escaping issue)
- ❌ Need to verify margin percentage format (27.0 vs 0.27)
- ❌ Need actual values for msrpMargin and msrpVolume

## Next Steps (When You Return)

### 1. Find MSRP Calculation Constants
**Search the JavaScript codebase for:**
- `msrpMargin =`
- `msrpVolume =`
- `msrpLoyalty =`

These are likely defined at the top of a file or in a configuration.

### 2. Fix the SQL Syntax
The issue is in the dynamic SQL PREPARE statement. The quote escaping for string literals inside the CONCAT needs fixing.

**Current error:**
```
near 'p_hull_no;
    DEALLOCATE PREPARE stmt;
```

**Problem area:**
```sql
SET @query = CONCAT('
    INSERT INTO tmp_line_items
    SELECT ItemNo, ItemDesc1, ...
    WHERE MCTDesc = ''PONTOONS''  -- Double quotes for escaping
    ...
');
```

### 3. Verify Margin Storage Format
**Run this query:**
```sql
SELECT
    SV_23_BASE_BOAT,
    SV_23_VOL_DISC
FROM warrantyparts.DealerMargins
WHERE DealerID = '00333836';
```

If it returns `27.00`, we need to divide by 100 in calculations.
If it returns `0.27`, we use it directly.

### 4. Test the Complete System
Once fixed, test with:
- `CALL GetCompleteBoatInformation('ETWP5175I324', 0.75, 1.0);`

Should return all 5 result sets with correct pricing.

### 5. Compare Results
Compare the stored procedure output with the JavaScript output to verify:
- Sale Price matches
- MSRP matches
- All line items included

## Files Created Today

1. **GetCompleteBoatInformation_FINAL.sql** - The stored procedure (has syntax error to fix)
2. **2026-02-02-pricing-formulas-discovered.md** - This context file

## Files From Previous Sessions

1. **GetCompleteBoatInformation.sql** - Original version (returns only dealer cost)
2. **NODE_JS_USAGE.md** - Usage documentation
3. **2026-01-30-pricing-source-mystery.txt** - Previous session context

## Key JavaScript Code Reference

```javascript
// From Calculate2021.js (lines ~50-100)

$.each(boatoptions, function (j) {
    var dealercost = boatoptions[j].ExtSalesAmount;
    var mct = boatoptions[j].MCTDesc;
    var prodCategory = boatoptions[j].ItemMasterProdCat;

    if (mct === 'PONTOONS') {
        // Base boat calculation
        boatsp = (Number(dealercost) / baseboatmargin) * vol_disc;
        msrpprice = Number((dealercost) * vol_disc) / msrpMargin;

        // For SV series special handling
        if (series === 'SV') {
            saleprice = Number((dealercost * msrpVolume * msrpLoyalty) / baseboatmargin);
            msrpprice = saleprice;
        }
    }

    if (mct === 'ENGINES' || mct === 'ENGINES I/O') {
        enginesp = (Number(dealercost) / enginemargin) * vol_disc;
        msrp = Math.round(Number((dealercost * msrpVolume) / msrpMargin));
    }

    // For all other options
    if (dealercost > 0) {
        saleprice = (Number(dealercost / optionmargin) * vol_disc);
        msrpprice = Number((dealercost * msrpVolume) / msrpMargin);
    }
});
```

## Display Modes (User Requirements)

The system needs to support 4 display modes:

1. **MSRP Only** - Show manufacturer suggested retail price
2. **Selling Price Only** - Show dealer's selling price (Sale Price)
3. **Sale & MSRP** - Show both with savings calculation
4. **No Pricing** - Show features only, no prices

## Database Info

**RDS MySQL:**
- Host: ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com
- User: awsmaster
- Password: VWvHG9vfG23g7gD
- Database: warrantyparts_test (stored procedures)
- Database: warrantyparts (data tables)

**Key Tables:**
- `warrantyparts.SerialNumberMaster` - Boat headers
- `warrantyparts.BoatOptions24` / `BoatOptions25` / `BoatOptions26` - Line items
- `warrantyparts.DealerMargins` - Margin percentages per dealer/series

## Questions for Next Session

1. **Where are msrpMargin, msrpVolume, msrpLoyalty defined?**
   - Search the JavaScript files
   - Check if they're in a config file
   - Check if they're hardcoded constants

2. **What's the format of margin storage?**
   - Is 27% stored as 27.0 or 0.27?
   - Do we need to divide by 100?

3. **Should we handle special cases?**
   - SV series has special MSRP calculation
   - Package discounts (lines 40-140 in JavaScript)
   - Engine increments vs. full engine price

4. **Node.js integration**
   - Once working, how will this be called from Node?
   - What format should the result sets be?

## Success Criteria

When we're done, the stored procedure should:
- ✅ Take only Hull# as input (plus optional MSRP params)
- ✅ Return 3 price points for every line item
- ✅ Match the JavaScript calculation results
- ✅ Work for boats from any year (24, 25, 26)
- ✅ Work for any dealer/series combination
- ✅ Be callable from Node.js

---

**Resume Point**: Fix the SQL syntax error in GetCompleteBoatInformation_FINAL.sql and find the MSRP constants.
