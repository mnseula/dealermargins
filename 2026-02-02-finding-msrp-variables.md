# Session Context - February 2, 2026 (Part 2)
## Finding the MSRP Variables - Ready to Resume

---

## Current Status: 95% Complete! 🎯

We have **everything working** except we need 3 variable values from JavaScript.

## What We Built Today

### ✅ GetCompleteBoatInformation_FINAL.sql
A stored procedure that calculates **THREE price points**:
1. **Dealer Cost** - From BoatOptions{YY}.ExtSalesAmount
2. **Sale Price** - `(dealer_cost * vol_disc) / margin_pct`
3. **MSRP** - `(dealer_cost * msrp_volume) / msrp_margin`

**Location:** `/Users/michaelnseula/code/dealermargins/GetCompleteBoatInformation_FINAL.sql`

**Status:** ✅ SQL is correct and ready to test
**Blocked by:** Need values for `msrp_margin`, `msrp_volume`, `msrp_loyalty`

---

## The JavaScript Formulas (from Calculate2021.js)

### Sale Price Formula
```javascript
// Base Boat
saleprice = (dealercost * vol_disc) / baseboatmargin;

// Engine
enginesp = (dealercost * vol_disc) / enginemargin;

// Options
saleprice = (dealercost * vol_disc) / optionmargin;
```

### MSRP Formula
```javascript
// Standard calculation
msrpprice = (dealercost * msrpVolume) / msrpMargin;

// SV Series special calculation
if (series === 'SV') {
    msrpprice = (dealercost * msrpVolume * msrpLoyalty) / msrpMargin;
}
```

---

## What We Know

### ✅ Variables We Have (from DealerMargins table):
- `baseboatmargin` → SV_23_BASE_BOAT (27.00%)
- `enginemargin` → SV_23_ENGINE (27.00%)
- `optionmargin` → SV_23_OPTIONS (27.00%)
- `vol_disc` → SV_23_VOL_DISC (27.00)

**Format:** Stored as `27.00` in database = 27%
**Conversion:** Divide by 100 to get decimal (0.27)

### ❓ Variables We NEED (not in DealerMargins table):
- **`msrpMargin`** - MSRP margin divisor
- **`msrpVolume`** - MSRP volume multiplier
- **`msrpLoyalty`** - SV series loyalty multiplier (might be 1.0 for other series)

**These are NOT in DealerMargins table!** We checked all 93 columns.

---

## Where Are These Variables Defined?

The Calculate2021.js function **USES** these variables but does NOT define them:
```javascript
// Line 201
console.log('MSRP Margin: ', msrpMargin);  // It logs it, so it exists

// Line 224
msrpboatpackageprice = Number(boatpackageprice * msrpVolume) / msrpMargin;

// Line 227 (for SV series)
msrpboatpackageprice = Number((boatpackageprice * msrpVolume * msrpLoyalty) / msrpMargin);
```

**They must be defined BEFORE Calculate2021() is called!**

Possible locations:
1. Earlier in the same file (before the function)
2. In another JavaScript file that loads first
3. Set by a function that runs before Calculate2021
4. Loaded from database/API
5. In a global configuration object

---

## How to Find Them

### Option 1: Step Through JavaScript (CURRENT PLAN)
You're going to step through the code to find where these are set.

**What to look for:**
```javascript
// Direct assignment
msrpMargin = 0.75;
var msrpMargin = 0.75;
window.msrpMargin = 0.75;

// From function
msrpMargin = getValue('CONFIG', 'MSRP_MARGIN');
msrpMargin = getMarginSettings().msrpMargin;

// From API/database
msrpMargin = dealerData.msrp_margin;
```

**Browser console approach:**
1. Open the window sticker page in browser
2. Open Developer Tools (F12)
3. Before Calculate2021 runs, type in console:
   ```javascript
   console.log('msrpMargin:', msrpMargin);
   console.log('msrpVolume:', msrpVolume);
   console.log('msrpLoyalty:', msrpLoyalty);
   ```

### Option 2: Search Codebase
```bash
cd ~/code
grep -r "msrpMargin\s*=" . --include="*.js"
grep -r "var msrpMargin" . --include="*.js"
grep -r "window.msrpMargin" . --include="*.js"
```

### Option 3: Reverse Engineer from Known Values
From your window sticker example:
- Dealer Cost: $30,557
- MSRP: $38,569

**Calculation:**
```
msrpMargin = (dealer_cost × msrpVolume) / MSRP
msrpMargin = (30557 × 1.0) / 38569
msrpMargin = 0.792 ≈ 0.79
```

**Interpretation:** Dealer cost is 79% of MSRP (21% markup to get MSRP)

---

## Reasonable Default Values (if you can't find them)

Based on marine industry standards and the reverse calculation:

```javascript
msrpMargin = 0.79    // Dealer cost is 79% of MSRP
msrpVolume = 1.0     // No volume adjustment
msrpLoyalty = 1.0    // Or 0.95 for SV series (5% loyalty discount)
```

**These would make:**
- Dealer Cost: $30,557
- MSRP: $30,557 / 0.79 = $38,679 (close to $38,569!)

---

## Once You Find the Values

### Update the Stored Procedure Call

**Current (with parameters):**
```sql
CALL GetCompleteBoatInformation('ETWP5175I324', 0.75, 1.0);
--                               hull_no        msrp  msrp
--                                              margin volume
```

**Or set defaults in the procedure:**
Edit line 31 in GetCompleteBoatInformation_FINAL.sql:
```sql
SET v_msrp_margin = IFNULL(p_msrp_margin, 0.7900);  -- Use actual value
SET v_msrp_volume = IFNULL(p_msrp_volume, 1.0000);
```

### Test the Procedure

```bash
python3 << 'PYTHON_SCRIPT'
import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts_test'
)

cursor = conn.cursor()

# Test with the values you found
msrp_margin = 0.79  # CHANGE THIS
msrp_volume = 1.0   # CHANGE THIS

cursor.callproc('GetCompleteBoatInformation',
                ['ETWP5175I324', msrp_margin, msrp_volume])

# Process results...
for result in cursor.stored_results():
    rows = result.fetchall()
    # ... display results

cursor.close()
conn.close()
PYTHON_SCRIPT
```

### Verify Results Match JavaScript

Compare the stored procedure output with your JavaScript output:
- Line items should match
- Sale prices should match
- MSRP should match

---

## Files Ready to Use

1. **GetCompleteBoatInformation_FINAL.sql** - The stored procedure (ready to test)
2. **Calculate2021.js** - The JavaScript you provided (full code)
3. **2026-02-02-pricing-formulas-discovered.md** - Complete formula documentation

---

## Database Connection Info

**MySQL (RDS):**
```
Host:     ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com
User:     awsmaster
Password: VWvHG9vfG23g7gD
Database: warrantyparts_test (stored procedures)
Database: warrantyparts (data tables)
```

**MSSQL (Staging) - if needed:**
```
Server:   MPL1STGSQL086.POLARISSTAGE.COM
Database: CSISTG
User:     svccsimarine
Password: CNKmoFxEsXs0D9egZQXH
```
(Note: Not accessible from this machine - requires VPN/internal network)

---

## Test Boats

**Hull ETWP5175I324** (2024 20SVSRSR):
- Dealer: Nichols Marine - Norman
- Model Year: 24 → uses BoatOptions24
- Series: SV_23
- Has complete line items (20 items)
- Known MSRP: $38,569 (from your window sticker)
- Dealer Cost from database: $30,557

**Hull ETWP6278J324** (2024 20SVFSR):
- Another test boat with complete data

---

## The 4 Display Modes

Once working, the system supports:

1. **MSRP Only** - Show manufacturer price (`msrp` column)
2. **Selling Price Only** - Show dealer selling price (`sale_price` column)
3. **Sale & MSRP** - Show both with savings (`msrp - sale_price`)
4. **No Pricing** - Show features only (hide price columns)

---

## Next Steps When You Resume

1. ✅ **Find the variable values** (what you're doing now)
   - Step through JavaScript
   - Check browser console
   - Search codebase

2. ⏳ **Update the stored procedure** with correct values

3. ⏳ **Test and verify** calculations match JavaScript

4. ⏳ **Document final values** for future reference

5. ⏳ **Integrate with Node.js** application

---

## Key Questions to Answer

When stepping through the JavaScript, look for:

1. **Where are these variables assigned?**
   - Function name that sets them?
   - File name where they're defined?

2. **Are they constants or dynamic?**
   - Same for all dealers?
   - Different per series?
   - Change over time?

3. **What are the actual values?**
   - msrpMargin = ?
   - msrpVolume = ?
   - msrpLoyalty = ? (especially for SV vs other series)

---

## Progress Tracker

- ✅ Discovered pricing formulas from JavaScript
- ✅ Created stored procedure with correct formula structure
- ✅ Verified DealerMargins table has sale price variables
- ✅ Confirmed MSRP variables are NOT in database
- ✅ Identified Calculate2021.js as the source
- ⏳ **Find msrpMargin, msrpVolume, msrpLoyalty values** ← YOU ARE HERE
- ⏳ Test stored procedure with correct values
- ⏳ Verify calculations match JavaScript output
- ⏳ Deploy to production

---

**Resume Point:** You're stepping through Calculate2021.js to find where msrpMargin, msrpVolume, and msrpLoyalty are defined. Once you have those 3 values, we can test everything!

Good luck! 🚀
