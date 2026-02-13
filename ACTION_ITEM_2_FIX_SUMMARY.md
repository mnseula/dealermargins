# Action Item 2 Fix Summary: Boat Item Double-Counting

## Problem

When calculating selling prices for CPQ boats, the boat line items were being counted twice, causing incorrect totals:

### Example (CPQTEST26 - 22MSB):
```
Line Item 1: "Base Boat" (MCT: PONTOONS) = $42,042.00
Line Item 2: "22MSB" (MCT: Pontoon Boats OB) = $51,156.00
---------------------------------------------------------
INCORRECT TOTAL: $93,198.00 (double-counted boat)
```

**Root Cause:** The JavaScript pricing logic was processing ALL line items with `MCTDesc = 'PONTOONS'` or `MCTDesc = 'Pontoon Boats OB'`, adding each to the `boatpackageprice` calculation. For CPQ boats, there are often multiple boat entries in the line items, causing the base boat to be counted multiple times.

## Solution

Modified `calculate.js` to:

1. **Detect CPQ boats** using the existing `window.cpqBaseBoatDealerCost` flag (set by `packagePricing.js`)
2. **Skip PONTOONS line items for CPQ boats** in three locations:
   - Line ~84: Skip adding PONTOONS to `boatpackageprice`
   - Line ~439: Skip processing PONTOONS for display values
   - Line ~522: Skip adding PONTOONS to `boattable` array

3. **Preserve legacy boat functionality** - Non-CPQ boats continue to process PONTOONS line items normally

## Key Code Changes

### Location 1: Boat Package Price Calculation
```javascript
// BEFORE:
if (mct === 'PONTOONS') {
    boatpackageprice = boatpackageprice + Number(dealercost);
    // ...
}

// AFTER:
var isCpqBoat = (isCpqAuthorized && window.cpqBaseBoatDealerCost && Number(window.cpqBaseBoatDealerCost) > 0);

if ((mct === 'PONTOONS' || mct === 'Pontoon Boats OB') && isCpqBoat) {
    console.log('CPQ BOAT - Skipping PONTOONS line item to prevent double-counting');
    // Store real MSRP if available
    if (hasRealMSRP) {
        window.pontoonRealMSRP = Number(realMSRP);
    }
} else if (mct === 'PONTOONS') {
    // Legacy boat - process normally
    boatpackageprice = boatpackageprice + Number(dealercost);
    // ...
}
```

### Location 2: Display Value Calculation
```javascript
// BEFORE:
if (mct == 'PONTOONS') {
    // Calculate msrpprice and saleprice
    // ...
}

// AFTER:
var isCpqBoat = (isCpqAuthorized && window.cpqBaseBoatDealerCost && Number(window.cpqBaseBoatDealerCost) > 0);

if ((mct == 'PONTOONS' || mct == 'Pontoon Boats OB') && isCpqBoat) {
    console.log("CPQ BOAT - Skipping PONTOONS line item display");
} else if (mct == 'PONTOONS') {
    // Legacy boat - process normally
    // Calculate msrpprice and saleprice
    // ...
}
```

### Location 3: Boat Table Population
```javascript
// BEFORE:
} else {
    boattable.push({
        'ItemDesc1': itemdesc,
        // ...
    });
}

// AFTER:
} else if ((mct === 'PONTOONS' || mct === 'Pontoon Boats OB') && isCpqBoat) {
    console.log("CPQ BOAT - Skipping boattable entry for PONTOONS item");
} else {
    boattable.push({
        'ItemDesc1': itemdesc,
        // ...
    });
}
```

## Result

For CPQ boats (like CPQTEST26):
- ✅ Boat items (PONTOONS) are excluded from line item calculations
- ✅ Base boat pricing comes from `window.cpqBaseBoatDealerCost` and `window.cpqBaseBoatMSRP`
- ✅ Accessories, engines, pre-rig, and other items are still included
- ✅ No more double-counting

For Legacy boats:
- ✅ PONTOONS line items continue to be processed normally
- ✅ No change in behavior

## Testing

Test using CPQ boat CPQTEST26:
```bash
# Check line items for the test boat
python3 check_mct_categories.py

# Expected output:
# - Shows "22MSB" and "Base Boat" as PONTOONS items ($93,198 total)
# - These should now be EXCLUDED from calculations
# - Other BS1 items (Performance Package, Pre-Rig, etc.) should still be INCLUDED
```

## Related Files Modified

1. **calculate.js** - Main pricing calculation logic (3 locations)
2. **stored_procedures.sql** - SQL procedures updated to exclude BS1/BOA (documentation)
3. **generate_complete_window_sticker.py** - Python script updated to skip BS1/BOA
4. **generate_window_sticker_26.py** - Python script updated to skip BS1/BOA

## Important Notes

- **MCTDesc field matters**: We check `mct === 'PONTOONS'` OR `mct === 'Pontoon Boats OB'`
- **Product Category (BS1/BOA) is NOT sufficient**: BS1 is used for many items (Performance Packages, Pre-Rig, Accessories), not just boats
- **Authorization check**: CPQ boat processing only happens for authorized users (`WEB@BENNINGTONMARINE.COM`)
- **Backwards compatible**: Legacy boats (without `window.cpqBaseBoatDealerCost`) continue to work as before

## Action Items Completed

✅ **Action Item 2**: Fix selling price math - remove boat line item double-counting while keeping engines etc.

## Remaining Action Items

- [ ] Action Item 3: Standard features need to pull all features (Interior, Exterior, Console, Warranty)
- [ ] Action Item 4: Boat information and performance package specs tweaking
- [ ] Action Item 5: Bring in panel color, production number, etc. from SerialNumberMaster
