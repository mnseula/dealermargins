# CPQ Pricing Fix - MSRP and Dealer Cost Not Loading

**Date:** 2026-02-12
**Issue:** CPQ boats showing wrong MSRP and dealer cost (using $46,915 instead of CPQ values $58,171 MSRP / $41,131 dealer cost)

## Problem Description

For CPQ boat **ETWINVTEST0226** (23ML, M Series), the system was displaying:
- Base Boat: $46,915.00 / $46,915.00
- Total MSRP: $52,708.00
- Total Sale: $51,011.00

But the **CPQ database** shows the boat should have:
- **CPQ MSRP:** $58,171.00 (from API)
- **CPQ Dealer Cost:** $41,131.00 (from API)

These CPQ values were **NOT being used** by the JavaScript pricing calculations.

## Root Cause

The BoatOptions table contains **TWO boat line items** for CPQ boats:

1. **"Base Boat, 23ML"** (ItemDesc1 contains "Base Boat")
   - ExtSalesAmount: $41,131.00 ✅ **CPQ dealer cost**
   - MSRP: $58,171.00 ✅ **CPQ MSRP**
   - This line has the real pricing from the Infor CPQ API

2. **"23ML, 23 M CRUISE"** (ItemDesc1 = "23 M CRUISE")
   - ExtSalesAmount: $46,915.00 ❌ **Wrong value**
   - MSRP: $0.00 ❌ **No MSRP**
   - This appears to be a duplicate or legacy line

### Code Flow (BEFORE Fix)

1. **packagePricing.js** (lines 116-144):
   - Loads ALL boat records including both lines
   - Filters OUT "Base Boat" records to avoid duplicates
   - **Result:** Only the "$46,915" line remains in `window.boatmodel`

2. **Calculate2021.js** (lines 33-82):
   - Loops through `boatoptions` array
   - Extracts `dealercost` from `ExtSalesAmount` → Gets $46,915 ❌
   - Extracts `realMSRP` from `MSRP` field → Gets $0 ❌
   - Sets `window.pontoonRealMSRP = null` (no MSRP found)

3. **Result:**
   - CPQ MSRP is ignored (calculated from dealer cost instead)
   - Wrong dealer cost is used ($46,915 instead of $41,131)
   - Margin calculations are incorrect

## Solution

Extract CPQ pricing from "Base Boat" line **BEFORE** filtering it out, and store in window variables.

### Changes Made

#### 1. **packagePricing.js** (lines 135-144)

**BEFORE:**
```javascript
// CPQ LOGIC: Filter out "Base Boat" records if multiple boat records exist
if (boatmodel.length > 1) {
    var nonBaseBoats = $.grep(boatmodel, function (rec) {
        return rec.ItemNo !== 'Base Boat' && rec.BoatModelNo !== 'Base Boat' && rec.ItemDesc1 !== 'Base Boat';
    });
    if (nonBaseBoats.length > 0) {
        window.boatmodel = nonBaseBoats;  // ❌ CPQ pricing lost!
    }
}
```

**AFTER:**
```javascript
// CPQ LOGIC: Extract CPQ pricing from "Base Boat" record before filtering
window.cpqBaseBoatMSRP = null;
window.cpqBaseBoatDealerCost = null;

if (boatmodel.length > 1) {
    // Look for "Base Boat" record - it has the CPQ pricing
    var baseBoatRec = $.grep(boatmodel, function (rec) {
        return (rec.ItemNo === 'Base Boat' || rec.BoatModelNo === 'Base Boat' || rec.ItemDesc1 === 'Base Boat')
            && rec.MSRP && Number(rec.MSRP) > 0;
    });

    if (baseBoatRec.length > 0) {
        // ✅ Extract CPQ pricing before filtering
        window.cpqBaseBoatMSRP = Number(baseBoatRec[0].MSRP);
        window.cpqBaseBoatDealerCost = Number(baseBoatRec[0].ExtSalesAmount);
        console.log('✅ CPQ Base Boat pricing extracted:');
        console.log('   MSRP: $' + window.cpqBaseBoatMSRP);
        console.log('   Dealer Cost: $' + window.cpqBaseBoatDealerCost);
    }

    // Now filter out "Base Boat" to use configured boat line
    var nonBaseBoats = $.grep(boatmodel, function (rec) {
        return rec.ItemNo !== 'Base Boat' && rec.BoatModelNo !== 'Base Boat' && rec.ItemDesc1 !== 'Base Boat';
    });
    if (nonBaseBoats.length > 0) {
        window.boatmodel = nonBaseBoats;
    }
}
```

#### 2. **Calculate2021.js** (lines 33-50)

**Extract dealer cost from CPQ data:**
```javascript
$.each(boatoptions, function (j) {
    var mct = boatoptions[j].MCTDesc;
    var mctType = boatoptions[j].ItemMasterMCT;
    // ✅ Use CPQ dealer cost for PONTOONS if available
    var dealercost = (mct === 'PONTOONS' && window.cpqBaseBoatDealerCost)
        ? window.cpqBaseBoatDealerCost
        : boatoptions[j].ExtSalesAmount;
```

**Extract MSRP from CPQ data:**
```javascript
    // ✅ Use extracted CPQ MSRP first, fallback to item MSRP
    var realMSRP = window.cpqBaseBoatMSRP || boatoptions[j].MSRP;
    var hasRealMSRP = (realMSRP !== undefined && realMSRP !== null && Number(realMSRP) > 0);
```

#### 3. **calculate.js** (Same changes for boats before 2021)

Applied identical fixes to `calculate.js` for consistency.

## Expected Results (AFTER Fix)

For boat **ETWINVTEST0226**:

**Base Boat Pricing:**
- **MSRP:** $58,171.00 (from CPQ) ✅
- **CPQ Dealer Cost:** $41,131.00 (from CPQ) ✅

**With 37% margins applied:**
- Sale Price: $41,131 × (1 - 0.37) = ~$25,912.53
- MSRP: $58,171.00 (never changes)

**With 0% margins:**
- Sale Price: $41,131.00 (equals CPQ dealer cost) ✅
- MSRP: $58,171.00 (never changes) ✅

## Files Modified

1. **packagePricing.js** - Extract CPQ pricing before filtering
2. **Calculate2021.js** - Use extracted CPQ pricing for dealer cost and MSRP
3. **calculate.js** - Same fixes for pre-2021 boats

## Backups Created

- `old_packagePricing_before_cpq_pricing_fix.js`
- `old_Calculate2021_before_cpq_pricing_fix.js`
- `old_calculate_before_cpq_pricing_fix.js`

## Testing

1. Load boat ETWINVTEST0226 in EOS
2. Check console logs for:
   ```
   ✅ CPQ Base Boat pricing extracted:
      MSRP: $58171
      Dealer Cost: $41131
   ```
3. Verify line items show:
   - Base Boat MSRP: $58,171.00
   - Base Boat Dealer Cost: $41,131.00
4. Set margins to 0% and verify sale price = $41,131.00
5. Set margins to 37% and verify calculations use $41,131 as base

## Key Points

- **MSRP from CPQ should NEVER change** - always $58,171 for this boat
- **Dealer Cost from CPQ** ($41,131) is the base for margin calculations
- **Margins are applied to dealer cost** to get sale price
- **"Base Boat" line must be preserved** until pricing is extracted
- **Filtering is still safe** - we just extract data first before removing the duplicate
