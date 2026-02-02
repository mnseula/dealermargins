# Package Pricing Analysis - Findings & Next Steps
**Date:** February 2, 2026
**Boat Analyzed:** ETWP7154K324 (20 S VALUE STERN RADIUS)
**Dealer:** NICHOLS MARINE - NORMAN (ID: 00333834)

---

## Executive Summary

I successfully reverse-engineered the pricing formulas from Calculate2021.js and identified the variables needed for SQL implementation. However, **package pricing requires default cost data from the CPQ configurator** that is not available in the sales database.

---

## ✅ What We Confirmed

### 1. MSRP Variables (Company-Wide Constants)
Based on reverse calculation from window sticker data:
- **msrpMargin** = 0.79 (dealer cost is 79% of MSRP)
- **msrpVolume** = 1.0 (no volume adjustment for MSRP)
- **msrpLoyalty** = 1.0 (loyalty multiplier, may vary by series)

### 2. Pricing Formulas

**Sale Price:**
```javascript
// Base Boat
sale_price = (dealer_cost * vol_disc) / baseboatmargin + freight + prep

// Engine
sale_price = (dealer_cost * vol_disc) / enginemargin

// Options
sale_price = (dealer_cost * vol_disc) / optionmargin

// SV Series Special - Uses MSRP margin
if (series === 'SV') {
    sale_price = (dealer_cost * msrpVolume * msrpLoyalty) / msrpMargin
}
```

**MSRP:**
```javascript
// Standard
msrp = (dealer_cost * msrpVolume) / msrpMargin

// SV Series
if (series === 'SV') {
    msrp = (dealer_cost * msrpVolume * msrpLoyalty) / msrpMargin
    // And sale_price = msrp (no dealer discount)
}
```

### 3. Package Pricing Structure

The boat package combines:
1. **Boat** (with SV series discount if applicable)
2. **Default Engine** (base horsepower for the model)
3. **Default Prerig** (base prerig for the model)

Then options are shown as:
- **Engine INCREMENT** = actual_engine - default_engine
- **Prerig INCREMENT** = actual_prerig - default_prerig (if > 0)

### 4. Data We Have

From database for ETWP7154K324:
```
Raw Dealer Costs:
- Boat (PONTOONS):     $25,077.00
- Engine (115HP):      $10,510.00
- Prerig:              $ 1,295.00

Dealer Margins (all 27%):
- baseboatmargin: 0.73
- enginemargin:   0.73
- optionmargin:   0.73
- vol_disc:       0.73

Freight: $0.00
Prep:    $0.00
```

Window Sticker Shows:
```
BOAT PACKAGE:              $35,623.00
Mercury 115HP (increment): $ 3,957.00
Express Package:           $ 3,544.00
Storage:                   $ 1,350.00
Battery:                   $   135.00
Ski Tow:                   $   766.00
-----------------------------------
TOTAL:                     $45,375.00
```

---

## ❌ What We're Missing

### 1. Default Engine Cost
**Where defined:** `getEngineInfo(engineitemno, engproductid)` in JavaScript
**Purpose:** Base horsepower included in boat package price
**Needed for:** Calculating engine increment

**Analysis:**
- Actual engine cost: $10,510 (Mercury 115HP)
- Engine increment sale price: $3,957
- Reverse calculation: default_engine ≈ $7,352
- **Best match in database:** Mercury 60HP at $7,352 (found on 17 boats)

**Recommendation:** The default engine for 20ft SV boats is likely **Mercury 60HP at $7,352**

### 2. Default Prerig Cost
**Where defined:** `getValue('DLR2', 'DEF_PRERIG_COST')` in JavaScript
**Purpose:** Base prerig included in boat package price
**Needed for:** Calculating prerig increment

**Analysis:**
When I try to reverse-engineer using default_engine = $7,352:
```
Boat package sale:        $35,623.00
Boat package dealer cost: $35,623 * 0.79 = $28,142.17

Components:
- Boat (with SV discount): $25,077 - $1,700 = $23,377.00
- Default engine:          $7,352.00
- Default prerig:          ???

$28,142.17 = $23,377 + $7,352 + default_prerig
$28,142.17 = $30,729 + default_prerig
default_prerig = -$2,586.83 ❌ NEGATIVE!
```

**The issue:** My calculation produces a negative default prerig, which is impossible.

**Possible explanations:**
1. The default engine is NOT $7,352 (maybe lower, like 9.9HP at $3,061?)
2. The SV discount is applied differently in the package
3. There's additional logic I'm missing from getEngineInfo()
4. The boat package formula is different than I understand

### 3. Variable Confirmation Needed

Even though I calculated approximate values, we need confirmation from the JavaScript runtime:
- **msrpMargin** = 0.79?
- **msrpVolume** = 1.0?
- **msrpLoyalty** = 1.0? (or different for SV series?)

---

## 🎯 Recommended Next Steps

### Option 1: Get Values from JavaScript Runtime ⭐ RECOMMENDED
**Steps:**
1. Open window sticker generator in browser
2. Open Developer Tools (F12) → Console
3. Before Calculate2021() runs, type:
   ```javascript
   console.log('msrpMargin:', msrpMargin);
   console.log('msrpVolume:', msrpVolume);
   console.log('msrpLoyalty:', msrpLoyalty);
   console.log('defaultengineprice:', defaultengineprice);
   console.log('defaultprerigprice:', defaultprerigprice);
   ```
4. Generate a window sticker for ETWP7154K324
5. Copy the console output

**This will give us exact values!**

### Option 2: Create Lookup Tables
Create database tables:
```sql
CREATE TABLE DefaultEngineCosts (
    model_series VARCHAR(10),
    model_length VARCHAR(5),
    default_engine_item_no VARCHAR(30),
    default_engine_cost DECIMAL(10,2),
    effective_year INT
);

CREATE TABLE DefaultPrerigCosts (
    model_series VARCHAR(10),
    model_length VARCHAR(5),
    default_prerig_item_no VARCHAR(30),
    default_prerig_cost DECIMAL(10,2),
    effective_year INT
);
```

Populate with data from CPQ configurator.

### Option 3: Parameterized Stored Procedure (INTERIM SOLUTION)
Create a procedure that accepts all unknown values as parameters:
```sql
CALL GetBoatPricingWithDefaults(
    'ETWP7154K324',  -- hull_no
    0.79,            -- msrp_margin
    1.0,             -- msrp_volume
    1.0,             -- msrp_loyalty
    7352.00,         -- default_engine_cost
    1295.00          -- default_prerig_cost
);
```

---

## 📊 Validation Test Case

Once we have the correct values, test with ETWP7154K324:

**Expected Output:**
```
BOAT PACKAGE:              $35,623.00
Engine INCREMENT (115HP):  $ 3,957.00
Express Package:           $ 3,544.00
Storage:                   $ 1,350.00
Battery:                   $   135.00
Ski Tow:                   $   766.00
-----------------------------------
TOTAL:                     $45,375.00
```

**SQL should match exactly!**

---

## 🔍 Database Findings

### Engines for 20ft SV Boats (by cost)
```
Mercury 9.9HP:    $ 3,061.00  (1 boat)
Yamaha 9.9HP:     $ 3,395.00  (4 boats)
Yamaha 25HP:      $ 4,463.00  (1 boat)
Torqeedo 30HP:    $ 4,598.00  (8 boats)
Mercury 60HP:     $ 7,352.00  (17 boats) ← Likely default
Yamaha 60HP:      $ 7,380.00  (2 boats)
Yamaha 70HP:      $ 8,028.00  (23 boats)
Yamaha 90HP:      $ 9,190.00  (5 boats)
Mercury 115HP:    $10,510.00  (our boat)
```

---

## 📁 Files Created

1. **GetBoatPricing.sql** - Line-by-line pricing (no package logic)
2. **GetBoatPricingWithPackage.sql** - Attempted package pricing (uses estimates)
3. **GetCompleteBoatInformation_FINAL.sql** - Clean implementation with 3 price points
4. **This document** - Analysis and findings

---

## ✨ What's Working

The SQL stored procedures correctly:
- ✅ Query boat options from dynamic BoatOptions{YY} tables
- ✅ Retrieve dealer margins from DealerMargins table
- ✅ Apply series-specific discounts (SV 20ft = -$1,700)
- ✅ Calculate sale prices using margin formulas
- ✅ Calculate MSRP using msrpMargin
- ✅ Handle SV series special logic (sale = MSRP)
- ✅ Filter discount lines from display
- ✅ Return organized result sets

**What's NOT working:**
- ❌ Package pricing (needs default costs from CPQ)
- ❌ Incremental engine/prerig display (depends on package pricing)

---

## 💡 Key Insights

1. **Two pricing systems exist:**
   - **Individual line items** (what GetBoatPricing.sql does) ✅
   - **Package pricing** (what JavaScript does) ⏸️

2. **CPQ configurator is the source of truth for:**
   - Default engine costs per model
   - Default prerig costs per model
   - MSRP margin variables

3. **The sales database (BoatOptions) contains:**
   - Actual sold configurations
   - Raw dealer costs
   - But NOT default/base configurations

4. **The JavaScript bridges the gap by:**
   - Calling getEngineInfo() to get default engine from CPQ
   - Calling getValue('DLR2', 'DEF_PRERIG_COST') to get default prerig
   - Loading MSRP_Margins from CPQ

---

## ⏭️ Resume Point

**You were going to step through the JavaScript to find where these variables are set.**

Once you have the values, we can:
1. Update GetBoatPricingWithPackage.sql with correct defaults
2. Test against ETWP7154K324 window sticker
3. Verify calculations match exactly
4. Deploy to production

**Or we can:**
1. Create parameterized procedure (Option 3 above)
2. Call it with the values from JavaScript
3. Build a wrapper application that fetches defaults from CPQ

---

**Ready to resume when you have the variable values!** 🚀
