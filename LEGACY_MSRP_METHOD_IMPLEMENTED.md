# Legacy MSRP Method Implementation Complete

## Boss's Request: "Old Habits" (Legacy SV Method)

**Implemented: MSRP = Sale Price for all CPQ boats**

## What Was Changed

### For CPQ Boats, All Items Now Use: `MSRP = Sale Price`

This matches the legacy SV series behavior where customers see:
- Sale Price: $94,597
- MSRP: $94,597
- Savings: $0 (no discount from MSRP)

## Code Changes in calculate.js

### 1. Base Boat (PONTOONS) - Line ~455
```javascript
if ((mct == 'PONTOONS' || mct == 'Pontoon Boats OB') && isCpqBoat) {
    // Calculate sale price from CPQ dealer cost
    saleprice = Number((window.cpqBaseBoatDealerCost * vol_disc) / baseboatmargin) +
                Number(freight) + Number(prep) + Number(additionalCharge);

    // LEGACY SV METHOD: Set MSRP = Sale Price
    msrpprice = saleprice;
    console.log("CPQ BOAT - Using legacy method: MSRP = Sale Price = $" + Math.round(msrpprice));

    setValue('DLR2', 'BOAT_SP', Math.round(saleprice));
    setValue('DLR2', 'BOAT_MS', Math.round(msrpprice));
}
```

### 2. Options/Accessories - Line ~492
```javascript
else if (mct !== 'ENGINES' && mct !== 'ENGINES I/O' && mct != 'Lower Unit Eng' && mct != 'PRE-RIG') {
    // Calculate sale price first
    if (dealercost > 0) {
        saleprice = (Number(dealercost / optionmargin) * vol_disc);
    } else {
        saleprice = Number(dealercost);
    }

    // LEGACY SV METHOD for all CPQ boats: MSRP = Sale Price
    if (isCpqBoat) {
        msrpprice = saleprice;
        console.log("CPQ BOAT option - Using legacy method: MSRP = Sale Price = $" + msrpprice);
    } else if (series == 'SV') {
        // Legacy SV series boats
        msrpprice = saleprice;
    } else {
        // Standard calculation for non-CPQ, non-SV boats
        // ... calculate MSRP from dealer cost ...
    }
}
```

### 3. Engines - Line ~586
```javascript
if (dealercost == 0) { saleprice = 0; }
else { saleprice = Math.round(Number(dealercost / enginemargin) * vol_disc); }

// LEGACY SV METHOD for CPQ boats: MSRP = Sale Price
if (isCpqBoat) {
    msrp = saleprice.toFixed(2);
    console.log("CPQ BOAT engine - Using legacy method: MSRP = Sale Price = $" + msrp);
} else if(series === 'SV') {
    msrp = Math.round(Number((dealercost * msrpVolume * msrpLoyalty)/ msrpMargin)).toFixed(2);
    saleprice = msrp;
} else {
    msrp = Math.round(Number((dealercost * msrpVolume)/ msrpMargin)).toFixed(2);
}
```

### 4. Pre-Rig - Line ~630
```javascript
// LEGACY SV METHOD for CPQ boats: MSRP = Sale Price
if (isCpqBoat) {
    msrp = Math.round(saleprice).toFixed(2);
    console.log("CPQ BOAT prerig - Using legacy method: MSRP = Sale Price = $" + msrp);
} else if(series === 'SV') {
    msrp = Math.round(Number((dealercost * msrpVolume * msrpLoyalty )/ msrpMargin)).toFixed(2);
} else {
    msrp = Math.round(Number((dealercost * msrpVolume)/ msrpMargin)).toFixed(2);
}
```

## How It Works

### CPQ Boat Detection
```javascript
var isCpqBoat = (isCpqAuthorized &&
                 window.cpqBaseBoatDealerCost &&
                 Number(window.cpqBaseBoatDealerCost) > 0);
```

### For CPQ Boats:
1. Calculate sale price from dealer cost using margins
2. Set MSRP = Sale Price (no separate MSRP calculation)
3. Customer sees no "discount" from MSRP
4. Simpler pricing presentation

### For Legacy Boats:
- Non-CPQ boats continue to work as before
- SV series still uses MSRP = Sale Price (unchanged)
- Other series calculate MSRP independently (unchanged)

## Example (Using PDF Numbers)

**Dealer Cost: $69,056**

### Before (Using CPQ MSRP):
```
Sale Price:  $94,597
MSRP:        $97,664  (from CPQ system)
Savings:     $3,067
```

### After (Legacy Method - IMPLEMENTED):
```
Sale Price:  $94,597
MSRP:        $94,597  (= Sale Price)
Savings:     $0
```

## Benefits

✅ **Simpler Pricing** - One price point, no confusing "discounts"
✅ **Matches Legacy** - Same as SV series "old habits"
✅ **Consistent** - All CPQ boat items use same method
✅ **Backward Compatible** - Legacy boats unaffected

## Impact

### CPQ Boats (2026+):
- ✅ MSRP = Sale Price (legacy method)
- ✅ Base boat, engines, pre-rig, accessories all use same logic
- ✅ No more separate MSRP from CPQ system

### Legacy Boats (2025-):
- ✅ No change in behavior
- ✅ Fully backward compatible
- ✅ SV series still uses MSRP = Sale Price
- ✅ Other series still calculate MSRP independently

## Testing

To test, use any CPQ boat:
```bash
# The console logs will show:
"CPQ BOAT - Using legacy method: MSRP = Sale Price = $..."
```

All items on CPQ boats will now have `MSRP = Sale Price`.

## Files Modified

1. **calculate.js** - 4 locations updated:
   - Base boat calculation (~line 455)
   - Options/accessories calculation (~line 492)
   - Engine calculation (~line 586)
   - Pre-rig calculation (~line 630)

## Complete ✅

The legacy SV method (MSRP = Sale Price) is now implemented for all CPQ boats, matching your boss's "old habits" preference.
