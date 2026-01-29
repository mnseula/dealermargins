# Dealer Margin Calculation - Correct Data Flow

## 🎯 Question: Should we use SerialNumberMaster in calculations?

**Answer: YES - as the STARTING POINT**, but each table has a specific role:

---

## 📊 Table Roles

### 1. **SerialNumberMaster** - Boat Header & Dealer Info
**Role:** Starting point for boat identification and dealer lookup

**Contains:**
- ✅ Boat identification (hull, model, series)
- ✅ Dealer information (number, name, location)
- ✅ Order/invoice details (ERP_OrderNo, InvoiceNo, dates)
- ✅ Colors and configuration
- ❌ NO pricing data
- ❌ NO line item details

**Use for:**
- Identifying the boat
- Getting dealer information
- Linking to other tables via `ERP_OrderNo` and `DealerNumber`

---

### 2. **BoatOptions26** - Line Items & MSRP Pricing
**Role:** Source of actual pricing data

**Contains:**
- ✅ Line items with descriptions
- ✅ **MSRP pricing** (ExtSalesAmount)
- ✅ Product categories (BOA, ENG, ACY, PPR, etc.)
- ✅ Quantities sold
- ❌ NO dealer cost (needs calculation)
- ❌ NO margin percentages

**Use for:**
- MSRP pricing (ExtSalesAmount)
- Product categorization for different margin rates
- Line item details for window sticker

---

### 3. **DealerMargins** - Margin Percentages
**Role:** Margin rates per dealer per series

**Contains:**
- ✅ Margin percentages by dealer
- ✅ Margin percentages by series (Q, QX, S, R, etc.)
- ✅ Different margins for: base boat, engine, options, freight, prep
- ❌ NO pricing data

**Use for:**
- Getting margin percentages for calculations
- Dealer-specific and series-specific margins

---

## 🔄 Correct Data Flow for Window Sticker with Pricing

```
Step 1: Get Boat Header
┌─────────────────────────────────────────────────────────┐
│ warrantyparts.SerialNumberMaster                        │
│ WHERE Boat_SerialNo = 'ETWXXXX'                         │
├─────────────────────────────────────────────────────────┤
│ Returns:                                                 │
│   - Boat info (model, series, serial)                   │
│   - Dealer info (DealerNumber, DealerName)              │
│   - Order info (ERP_OrderNo)                            │
│   - Colors (PanelColor, AccentPanel, etc.)              │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓ Use ERP_OrderNo
Step 2: Get Line Items & MSRP
┌─────────────────────────────────────────────────────────┐
│ warrantyparts.BoatOptions26                             │
│ WHERE ERP_OrderNo = 'SO00931835'                        │
├─────────────────────────────────────────────────────────┤
│ Returns:                                                 │
│   - Line items (ItemNo, ItemDesc1)                      │
│   - Product categories (ItemMasterProdCat)              │
│   - MSRP pricing (ExtSalesAmount)                       │
│                                                          │
│ Calculate totals by category:                           │
│   - Base Boat (BOA): $85,000                            │
│   - Engine (ENG):    $15,000                            │
│   - Accessories (ACY): $12,000                          │
│   - Prep (PPR):      $2,500                             │
│   - Freight (FRE):   $1,500                             │
│   TOTAL MSRP: $116,000                                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓ Use DealerNumber + Series
Step 3: Get Dealer Margins
┌─────────────────────────────────────────────────────────┐
│ warrantyparts_test.DealerMargins                        │
│ WHERE dealer_id = '50' AND series_id = 'S'             │
├─────────────────────────────────────────────────────────┤
│ Returns:                                                 │
│   - base_boat_margin: 27%                               │
│   - engine_margin: 27%                                   │
│   - options_margin: 27%                                  │
│   - freight_margin: 27%                                  │
│   - prep_margin: 27%                                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓ Apply margins
Step 4: Calculate Dealer Cost
┌─────────────────────────────────────────────────────────┐
│ DEALER COST CALCULATION                                 │
├─────────────────────────────────────────────────────────┤
│ Base Boat:                                              │
│   MSRP: $85,000 × (1 - 27%) = $62,050                  │
│                                                          │
│ Engine:                                                  │
│   MSRP: $15,000 × (1 - 27%) = $10,950                  │
│                                                          │
│ Accessories:                                             │
│   MSRP: $12,000 × (1 - 27%) = $8,760                   │
│                                                          │
│ Prep:                                                    │
│   MSRP: $2,500 × (1 - 27%) = $1,825                    │
│                                                          │
│ Freight:                                                 │
│   MSRP: $1,500 × (1 - 27%) = $1,095                    │
│                                                          │
│ TOTAL DEALER COST: $84,680                              │
│ DEALER SAVINGS: $31,320 (27%)                           │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 SQL Query Example

```sql
-- Complete query joining all three sources
SELECT
    -- Boat header from SerialNumberMaster
    snm.Boat_SerialNo,
    snm.BoatItemNo,
    snm.Series,
    snm.DealerNumber,
    snm.DealerName,
    snm.ERP_OrderNo,

    -- Line items from BoatOptions26
    bo.ItemMasterProdCat,
    SUM(bo.ExtSalesAmount) as category_msrp,

    -- Margins from DealerMargins
    dm.base_boat_margin,
    dm.engine_margin,
    dm.options_margin,

    -- Calculate dealer cost
    CASE bo.ItemMasterProdCat
        WHEN 'BOA' THEN SUM(bo.ExtSalesAmount) * (1 - dm.base_boat_margin/100)
        WHEN 'ENG' THEN SUM(bo.ExtSalesAmount) * (1 - dm.engine_margin/100)
        WHEN 'ACY' THEN SUM(bo.ExtSalesAmount) * (1 - dm.options_margin/100)
        WHEN 'PPR' THEN SUM(bo.ExtSalesAmount) * (1 - dm.prep_margin/100)
        WHEN 'FRE' THEN SUM(bo.ExtSalesAmount) * (1 - dm.freight_margin/100)
        ELSE SUM(bo.ExtSalesAmount)
    END as category_dealer_cost

FROM warrantyparts.SerialNumberMaster snm

-- Join line items
LEFT JOIN warrantyparts.BoatOptions26 bo
    ON snm.ERP_OrderNo = bo.ERP_OrderNo

-- Join dealer margins
LEFT JOIN warrantyparts_test.DealerMargins dm
    ON snm.DealerNumber = dm.dealer_id
    AND snm.Series = dm.series_id
    AND dm.enabled = 1
    AND CURDATE() BETWEEN dm.effective_date AND COALESCE(dm.end_date, '9999-12-31')

WHERE snm.Boat_SerialNo = 'ETWTEST024'

GROUP BY
    snm.Boat_SerialNo,
    snm.BoatItemNo,
    snm.Series,
    snm.DealerNumber,
    snm.DealerName,
    snm.ERP_OrderNo,
    bo.ItemMasterProdCat,
    dm.base_boat_margin,
    dm.engine_margin,
    dm.options_margin;
```

---

## ⚠️ Special Cases

### Case 1: Display/Test Boats (like ETWTEST024)
```
SerialNumberMaster: ✅ EXISTS (SO009999)
BoatOptions26:      ❌ NO LINE ITEMS (test order)
DealerMargins:      ✅ CAN LOOKUP (dealer 50)

Result: Show boat info and dealer, but NO PRICING
Display: "NO PRICES - DISPLAY MODEL"
```

### Case 2: Production Boats with Pricing
```
SerialNumberMaster: ✅ EXISTS (SO00931835)
BoatOptions26:      ✅ HAS LINE ITEMS
DealerMargins:      ✅ HAS MARGINS

Result: Full window sticker with MSRP and Dealer Cost
```

### Case 3: Dealer Not in DealerMargins Table
```
SerialNumberMaster: ✅ EXISTS
BoatOptions26:      ✅ HAS LINE ITEMS
DealerMargins:      ❌ NO MARGIN RECORD

Result: Show MSRP only, no dealer cost
Display: "Dealer pricing available upon request"
```

---

## 🎯 Recommendation

### **YES - Use SerialNumberMaster as the primary source:**

1. **Always start with SerialNumberMaster** to get:
   - Boat identification
   - Dealer information
   - Order number for joining

2. **Join to BoatOptions26** to get:
   - MSRP pricing
   - Line item details
   - Product categories

3. **Join to DealerMargins** to get:
   - Margin percentages
   - Calculate dealer cost

4. **For boats without line items:**
   - Still show boat header from SerialNumberMaster
   - Display "NO PRICES" message
   - Don't attempt margin calculations

---

## 📋 Updated Window Sticker Query

```sql
-- Stored procedure: GetWindowStickerWithDealerCost
-- Input: @Boat_SerialNo

-- Step 1: Get boat header
SELECT * FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = @Boat_SerialNo;

-- Step 2: Get line items with MSRP
SELECT * FROM warrantyparts.BoatOptions26
WHERE ERP_OrderNo = (
    SELECT ERP_OrderNo FROM warrantyparts.SerialNumberMaster
    WHERE Boat_SerialNo = @Boat_SerialNo
);

-- Step 3: Get dealer margins
SELECT * FROM warrantyparts_test.DealerMargins
WHERE dealer_id = (
    SELECT DealerNumber FROM warrantyparts.SerialNumberMaster
    WHERE Boat_SerialNo = @Boat_SerialNo
)
AND series_id = (
    SELECT Series FROM warrantyparts.SerialNumberMaster
    WHERE Boat_SerialNo = @Boat_SerialNo
)
AND enabled = 1;

-- Step 4: Calculate dealer cost (in application or stored procedure)
```

---

## ✅ Summary

| Table | Role | Contains Pricing? | Use For |
|-------|------|------------------|---------|
| **SerialNumberMaster** | Boat Header | ❌ No | Starting point, boat ID, dealer lookup |
| **BoatOptions26** | Line Items | ✅ Yes (MSRP) | MSRP pricing, line item details |
| **DealerMargins** | Margin Rates | ❌ No | Margin %, calculate dealer cost |

**Data Flow:** SerialNumberMaster → BoatOptions26 → DealerMargins → Calculate Dealer Cost
