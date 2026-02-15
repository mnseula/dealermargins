# Comparison of Three PDFs - SQBHO001654 (2026 22MSB)

## Build Summary Comparison

| Item | Dealer Cost | MSRP | Sales Price (22%) |
|------|-------------|------|-------------------|
| **Base Boat** | $42,042.00 | $59,459.00 | $53,900.00 |
| **Engine & Prerig** | $20,338.00 | $28,763.00 | $26,074.36 |
| **Additional Option** | $7,426.00 | $10,503.00 | $9,520.49 |
| **Total Boat MSRP** | $97,664.00 | $97,664.00 | $97,664.00 |
| **Total Boat Sale Price** | $69,806.00 | $98,725.00 | $89,494.85 |
| **Discounts** | $(750.00) | $(1,061.00) | $(961.54) |
| **Full Deal Sale Price** | $69,056.00 | $97,664.00 | $88,533.31 |

## Key Observations

### 1. MSRP is Constant
All three PDFs show the same **Total Boat MSRP: $97,664.00**

### 2. Pricing Levels
- **Dealer Cost**: $69,056 (dealer's actual cost)
- **MSRP**: $97,664 (manufacturer's suggested retail price)
- **Sales Price (22% margin)**: $88,533 (dealer's selling price with 22% margin)

### 3. Margin Calculation
```
MSRP:         $97,664.00   (100%)
Sales Price:  $88,533.31   (90.6%)
Margin:       $9,130.69    (9.4%)

Wait, that's not 22%... Let me recalculate:

Dealer Cost:  $69,056.00
Sales Price:  $88,533.31
Markup:       $19,477.31
Margin %:     28.2% markup from dealer cost
```

### 4. Component Breakdown

**Base Boat:**
- Dealer Cost: $42,042 (base cost)
- MSRP: $59,459 (141% of dealer cost)
- Sales Price: $53,900 (128% of dealer cost)

**Engine & Prerig:**
- Dealer Cost: $20,338 (base cost)
- MSRP: $28,763 (141% of dealer cost)
- Sales Price: $26,074 (128% of dealer cost)

**Additional Option (Accessories):**
- Dealer Cost: $7,426 (base cost)
- MSRP: $10,503 (141% of dealer cost)
- Sales Price: $9,520 (128% of dealer cost)

## Zero Margins Test Verification

### Expected Behavior with 0% Margins

When margins are set to **0%**, the selling price should equal the **sum of ExtSalesAmount** (dealer cost) for included items.

From our CPQTEST26 test:
```
✅ Included items (accessories + pre-rig): $9,114.00
🚫 Excluded items (boat items):           $93,198.00

With 0% margins:
  Expected selling price = $9,114.00 ✅
```

### Comparison with PDF

The PDF shows "Additional Option" (accessories):
- Dealer Cost: **$7,426.00**
- Our test shows accessories: **$7,426.00** ✅ **EXACT MATCH!**

Plus pre-rig:
- Our test shows pre-rig: $1,688.00
- Total included: $7,426 + $1,688 = $9,114.00 ✅

## Action Item 2 Fix Validation

### OLD BEHAVIOR (BROKEN):
```
Boat items:    $93,198  (INCLUDED - wrong!)
Accessories:   $7,426
Pre-rig:       $1,688
-----------------------------------------
Total:         $102,312  ❌ DOUBLE-COUNTED
```

### NEW BEHAVIOR (FIXED):
```
Boat items:    $93,198  (EXCLUDED for CPQ boats)
Accessories:   $7,426
Pre-rig:       $1,688
-----------------------------------------
Total:         $9,114   ✅ CORRECT

Base boat pricing comes separately from:
  - window.cpqBaseBoatDealerCost
  - window.cpqBaseBoatMSRP
```

## Summary

✅ **The fix is working correctly:**
1. Boat items ($93,198) are excluded from line item calculations for CPQ boats
2. Accessories ($7,426) match the PDF exactly
3. With 0% margins, the total correctly sums only included items ($9,114)
4. Base boat pricing comes from CPQ configuration, not line items

✅ **The three PDFs show:**
1. **Dealer Cost**: What the dealer pays ($69,056)
2. **MSRP**: What the manufacturer suggests as retail ($97,664)
3. **Sales Price (22%)**: What the dealer sells for with margins applied ($88,533)

✅ **Margin calculations:**
- Base boat: 28% markup from dealer cost to sales price
- Engine/Prerig: 28% markup from dealer cost to sales price
- Accessories: 28% markup from dealer cost to sales price
- MSRP: 41% markup from dealer cost

The fix ensures that when calculating totals, the base boat is not double-counted from line items, since it comes from the CPQ configuration.
