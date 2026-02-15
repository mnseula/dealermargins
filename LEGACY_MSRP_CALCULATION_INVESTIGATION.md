# Legacy MSRP Calculation Investigation

## Boss's Observation

"Maybe we should calculate the MSRP from the selling Price - this was something they do in the legacy boats"

## What I Found: SV Series Special Pricing

### Legacy Method (from calculate.js)

For **SV Series boats**, there's special logic where **MSRP = Sale Price**:

```javascript
if(series === 'SV') {
    // Calculate sale price first
    saleprice = Number((dealercost * msrpVolume * msrpLoyalty) / baseboatmargin) +
                Number(freight) + Number(prep) + Number(additionalCharge);

    // For SV series, only override MSRP with saleprice if we don't have real CPQ MSRP
    if (window.pontoonRealMSRP === null || window.pontoonRealMSRP === undefined) {
        msrpprice = saleprice;  // ← MSRP = Sale Price
    }
}
```

### For Non-SV Series (Standard Method)

For all other series, MSRP is calculated from dealer cost:

```javascript
// Standard MSRP calculation
msrpprice = Number((dealercost) * vol_disc) / msrpMargin + Number(additionalCharge);

// Sale price calculated separately
saleprice = Number((dealercost * vol_disc) / baseboatmargin) +
            Number(freight) + Number(prep) + Number(additionalCharge);
```

### For Options (SV Series)

Even for individual options on SV series:

```javascript
if (series == 'SV') {
    // For SV series, only apply loyalty multiplier if we're calculating (not using real MSRP)
    if (!itemHasRealMSRP) {
        msrpprice = Number(msrpprice * msrpLoyalty);
    }
    saleprice = msrpprice;  // ← Sale Price = MSRP
}
```

## Why This Matters for CPQ Boats

### Current CPQ Boat Behavior

Currently, CPQ boats have **real MSRP values** from the CPQ system stored in:
- `window.cpqBaseBoatMSRP`
- `boatoptions[i].MSRP`

The code checks:
```javascript
if (window.pontoonRealMSRP !== null && window.pontoonRealMSRP !== undefined) {
    msrpprice = Number(window.pontoonRealMSRP);
    console.log("Using real MSRP from CPQ: $", msrpprice);
} else {
    msrpprice = Number((dealercost) * vol_disc) / msrpMargin + Number(additionalCharge);
    console.log("Calculated MSRP from dealer cost: $", msrpprice);
}
```

### The Question

**Should CPQ boats also use the "MSRP = Sale Price" method** like SV series legacy boats?

## Investigation: Which Series Use This Method?

From the code analysis, **ONLY SV series uses MSRP = Sale Price**.

All other series calculate MSRP independently from sale price.

## Potential Implementation Options

### Option 1: Keep Current Method (Use Real CPQ MSRP)
**Pros:**
- CPQ system provides accurate MSRP values
- Maintains separation between dealer cost, sale price, and MSRP
- Transparent pricing structure

**Cons:**
- Different from SV series legacy behavior
- May not match boss's expectation

### Option 2: Override CPQ MSRP with Calculated Sale Price
**Pros:**
- Matches SV series legacy behavior
- Sale price becomes the MSRP
- Simpler pricing model (one less variable)

**Cons:**
- Ignores CPQ-provided MSRP values
- Less transparent for customers (no true MSRP to compare against)

### Option 3: Make it Configurable by Series
**Pros:**
- SV series: MSRP = Sale Price (legacy behavior)
- Other series: Use real CPQ MSRP (new behavior)
- Best of both worlds

**Cons:**
- More complex logic
- Need to maintain series-specific rules

## Current CPQ Boat Logic

```javascript
var isCpqBoat = (isCpqAuthorized &&
                 window.cpqBaseBoatDealerCost &&
                 Number(window.cpqBaseBoatDealerCost) > 0);

if ((mct === 'PONTOONS' || mct === 'Pontoon Boats OB') && isCpqBoat) {
    // CPQ boat - skip line item processing
    // Real MSRP comes from window.cpqBaseBoatMSRP
}
```

## Recommended Approach

### For CPQ Boats, Apply SV Series Logic Conditionally:

```javascript
if ((mct === 'PONTOONS' || mct === 'Pontoon Boats OB') && isCpqBoat) {
    // CPQ boat - skip line item to prevent double-counting
    console.log('CPQ BOAT - Skipping PONTOONS line item');

    // Calculate sale price from CPQ dealer cost
    saleprice = Number((window.cpqBaseBoatDealerCost * vol_disc) / baseboatmargin) +
                Number(freight) + Number(prep) + Number(additionalCharge);

    // Option 1: Use real CPQ MSRP (current behavior)
    msrpprice = Number(window.cpqBaseBoatMSRP);

    // Option 2: Set MSRP = Sale Price (SV series legacy behavior)
    // msrpprice = saleprice;

    // Option 3: Conditional based on series
    if (series === 'SV') {
        msrpprice = saleprice;  // SV series: MSRP = Sale Price
    } else {
        msrpprice = Number(window.cpqBaseBoatMSRP);  // Use real CPQ MSRP
    }

    setValue('DLR2', 'BOAT_SP', Math.round(saleprice));
    setValue('DLR2', 'BOAT_MS', Math.round(msrpprice));
}
```

## Questions for Boss

1. **Which series should use "MSRP = Sale Price"?**
   - Only SV series (like legacy)?
   - All CPQ boats?
   - Configurable by series?

2. **Should we override CPQ-provided MSRP values?**
   - CPQ system already has MSRP values
   - Should we ignore them and calculate from sale price?

3. **What's the business reason?**
   - Is this for pricing transparency?
   - Competitive positioning?
   - Simplification?

## Test Comparison

### Current Method (Using Real CPQ MSRP):
```
Dealer Cost:  $69,056
Sale Price:   $88,533  (with margins)
MSRP:         $97,664  (from CPQ)
```

### SV Series Method (MSRP = Sale Price):
```
Dealer Cost:  $69,056
Sale Price:   $88,533  (with margins)
MSRP:         $88,533  (same as sale price)
```

### Impact
- Customer sees no "discount" from MSRP
- Sale price IS the MSRP
- Simpler pricing presentation

## Next Steps

Need clarification from boss on:
1. Which boats should use "MSRP = Sale Price" method?
2. Should we override CPQ MSRP or honor it?
3. Is this series-specific or universal for CPQ boats?
