# Legacy Boat Verification - Calculate2021.js Changes

## How CPQ Detection Works

```javascript
var isCpqBoat = (isCpqAuthorized && window.cpqBaseBoatDealerCost && Number(window.cpqBaseBoatDealerCost) > 0);
```

### For CPQ Boats (like CPQTEST26):
1. **packagePricing.js** finds "Base Boat" record with MSRP > 0
2. Sets `window.cpqBaseBoatDealerCost = $42,042` (from "Base Boat" ExtSalesAmount)
3. Sets `window.cpqBaseBoatMSRP = $59,459` (from "Base Boat" MSRP)
4. **isCpqBoat = TRUE** (authorized user + cpqBaseBoatDealerCost set)
5. Uses CPQ logic: skip PONTOONS line items, use window.cpqBaseBoatDealerCost

### For Legacy Boats (pre-2026, no CPQ):
1. **packagePricing.js** does NOT find "Base Boat" record
2. `window.cpqBaseBoatDealerCost` remains **null** or **undefined**
3. `window.cpqBaseBoatMSRP` remains **null** or **undefined**
4. **isCpqBoat = FALSE** (cpqBaseBoatDealerCost is null/undefined)
5. Falls through to `else if (mct === 'PONTOONS')` - **ORIGINAL LEGACY LOGIC**

## Code Flow for Legacy Boats

### First Loop (Building Package Price):

```javascript
var isCpqBoat = (isCpqAuthorized && window.cpqBaseBoatDealerCost && Number(window.cpqBaseBoatDealerCost) > 0);

if ((mct === 'PONTOONS' || mct === 'Pontoon Boats OB') && isCpqBoat) {
    // ❌ SKIPPED for legacy boats (isCpqBoat = false)
    // CPQ boat logic here
} else if (mct === 'PONTOONS') {
    // ✅ EXECUTES for legacy boats
    // ORIGINAL LEGACY LOGIC (unchanged):
    boatpackageprice = boatpackageprice + Number(dealercost);
    
    // Package discounts (SV, S, etc.) - unchanged
    // ... all the original legacy code ...
}
```

### Display Values Loop:

```javascript
var isCpqBoat = (isCpqAuthorized && window.cpqBaseBoatDealerCost && Number(window.cpqBaseBoatDealerCost) > 0);

if ((mct == 'PONTOONS' || mct == 'Pontoon Boats OB') && isCpqBoat) {
    // ❌ SKIPPED for legacy boats (isCpqBoat = false)
    // CPQ boat logic here
} else if (mct == 'PONTOONS') {
    // ✅ EXECUTES for legacy boats
    // ORIGINAL LEGACY LOGIC (unchanged):
    
    // Use real MSRP if available (from window.pontoonRealMSRP)
    if (window.pontoonRealMSRP !== null && window.pontoonRealMSRP !== undefined) {
        msrpprice = Number(window.pontoonRealMSRP);
    } else {
        msrpprice = Number((dealercost) * vol_disc) / msrpMargin + Number(additionalCharge);
    }
    
    saleprice = Number((dealercost * vol_disc) / baseboatmargin) + Number(freight) + Number(prep) + Number(additionalCharge);
    
    // SV series special handling - unchanged
    if(series === 'SV') {
        saleprice = Number((dealercost * msrpVolume * msrpLoyalty) / baseboatmargin) + Number(freight) + Number(prep) + Number(additionalCharge);
        if (window.pontoonRealMSRP === null || window.pontoonRealMSRP === undefined) {
            msrpprice = saleprice;
        }
    }
}
```

## Why Legacy Boats Are Safe

### 1. Detection is Explicit
- Legacy boats will NEVER have `window.cpqBaseBoatDealerCost` set
- The CPQ if-block requires this to be set AND > 0
- Without it, `isCpqBoat = false`, code falls through to legacy logic

### 2. Uses if-else Structure
```javascript
if (CPQ_CONDITION) {
    // CPQ logic
} else if (mct === 'PONTOONS') {
    // Legacy logic - EXECUTES for legacy boats
}
```

The `else if` ensures that when the CPQ condition is false, the legacy code runs.

### 3. No Changes to Legacy Code
- All the original legacy boat code is preserved in the `else if` blocks
- Package discounts for SV, S series - unchanged
- MSRP calculation - unchanged  
- Sale price calculation - unchanged
- SV series special handling (MSRP = Sale Price) - unchanged

## Test Cases

### Legacy Boat (2025 and earlier):
```
Serial: SQBHO001234 (example)
- No "Base Boat" record in database ✅
- window.cpqBaseBoatDealerCost = null ✅
- isCpqBoat = false ✅
- Uses legacy PONTOONS logic ✅
- Calculates from ExtSalesAmount of PONTOONS record ✅
- Package discounts apply (SV, S series) ✅
```

### CPQ Boat (2026+):
```
Serial: CPQTEST26
- Has "Base Boat" record in database ✅
- window.cpqBaseBoatDealerCost = $42,042 ✅
- isCpqBoat = true ✅
- Skips PONTOONS line items ✅
- Uses window.cpqBaseBoatDealerCost ✅
- Prevents double-counting ✅
```

## Conclusion

✅ **Legacy boats are completely safe** because:
1. CPQ detection explicitly checks for `window.cpqBaseBoatDealerCost`
2. Legacy boats won't have this set (no "Base Boat" record)
3. All original legacy code preserved in `else if` blocks
4. No changes to legacy calculation logic
5. Package discounts, SV series handling - all unchanged

The changes ONLY affect boats with:
- "Base Boat" record in database
- Authorized user (WEB@BENNINGTONMARINE.COM)
- window.cpqBaseBoatDealerCost > 0

All other boats use the exact same logic as before.
