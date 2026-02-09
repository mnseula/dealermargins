# Complete Guide: Working with Unregistered Invoiced Boats

## What Are Unregistered Invoiced Boats?

**Unregistered Invoiced Boats** are boats that have been:
- ✅ **Invoiced** in the ERP system (have an invoice number)
- ❌ **NOT yet sold/registered** to a customer (still available for window stickers)

These are the boats you use for generating window stickers and dealer quotes.

---

## How to Identify Unregistered Invoiced Boats

Use **TWO tables** together:

### Table 1: `SerialNumberMaster`
Master table with boat details, dealer, and invoice information.

**Key Fields:**
- `Boat_SerialNo` - Hull Identification Number (HIN)
- `InvoiceNo` - Invoice number (NOT NULL if invoiced)
- `Active` - Registration status (0 = unregistered, 1 = registered/sold)
- `BoatItemNo` - Model (e.g., "23ML" for CPQ, "20SF-SPSSR" for legacy)
- `Series` - Boat series (M, S, Q, etc.)
- `DealerNumber` - Dealer ID
- `WebOrderNo` - Order number
- `ERP_OrderNo` - ERP order number

### Table 2: `SerialNumberRegistrationStatus`
Registration and inventory status tracking.

**Key Fields:**
- `Boat_SerialNo` - Hull Identification Number (HIN)
- `Registered` - Registration flag (0 = not registered, 1 = registered)
- `FieldInventory` - Field inventory status (0 = not in field)
- `BenningtonOwned` - Owned by Bennington flag

---

## The Formula: SQL Query to Get Unregistered Invoiced Boats

```sql
SELECT
    sm.Boat_SerialNo,
    sm.BoatItemNo,
    sm.Series,
    sm.BoatDesc1,
    sm.InvoiceNo,
    sm.DealerNumber,
    sm.DealerName,
    sm.WebOrderNo,
    sm.ERP_OrderNo,
    sm.SerialModelYear,
    rs.Registered,
    rs.FieldInventory
FROM warrantyparts.SerialNumberMaster sm
JOIN warrantyparts.SerialNumberRegistrationStatus rs
    ON sm.Boat_SerialNo = rs.Boat_SerialNo
WHERE sm.InvoiceNo IS NOT NULL          -- Must be invoiced
  AND sm.Active = 0                     -- Not registered in SerialNumberMaster
  AND rs.Registered = 0                 -- Not registered in RegistrationStatus
ORDER BY sm.InvoiceNo DESC;
```

**This query returns:**
- All boats that HAVE been invoiced (`InvoiceNo IS NOT NULL`)
- But have NOT been sold/registered (`Active = 0` AND `Registered = 0`)

---

## Example: Two Unregistered Invoiced Boats

### ETWTEST26 (2026 CPQ Boat)
```
Boat_SerialNo:     ETWTEST26
BoatItemNo:        23ML (CPQ format)
InvoiceNo:         25217358 ✅
Active:            0 (unregistered) ✅
Registered:        0 (not sold) ✅
DealerNumber:      50
WebOrderNo:        SOBHO00707 (CPQ format - starts with "SO")
```

### ETWTEST024 (2024 Legacy Boat)
```
Boat_SerialNo:     ETWTEST024
BoatItemNo:        20SF-SPSSR (legacy format)
InvoiceNo:         999999 ✅
Active:            0 (unregistered) ✅
Registered:        0 (not sold) ✅
DealerNumber:      50
WebOrderNo:        264615 (legacy format - number)
```

---

## How Boats Get Into the System

### Step 1: Boat Gets Invoiced in ERP (CSI)
- Order is created and invoiced in the ERP system
- Must have invoice number and `qty_invoiced > 0`

### Step 2: Run Import Script
```bash
python3 import_boatoptions_production.py
```

**What it does:**
- Extracts invoiced boats from ERP (MSSQL) → MySQL `warrantyparts` database
- Routes to `BoatOptions26`, `BoatOptions25`, etc. based on model year
- For CPQ boats: Scrapes configuration attributes (`CfgName`, `CfgValue`, MSRP)
- For legacy boats: Imports standard line items

### Step 3: Boat Appears in Both Tables
- `SerialNumberMaster` - Gets created/updated with invoice and dealer info
- `SerialNumberRegistrationStatus` - Tracks as unregistered (`Registered = 0`)

---

## How to Use Unregistered Invoiced Boats

### For Window Stickers:

1. **Query unregistered boats** using the formula above
2. **Load boat configuration** from `BoatOptions26` (or BoatOptions25, etc.)
3. **Load CPQ data** using sStatements:
   - `GET_CPQ_LHS_DATA` - specs and performance
   - `GET_CPQ_STANDARD_FEATURES` - standard features
4. **Generate window sticker** in EOS JavaScript

### For Dealer Quotes:

1. Query unregistered boat
2. Get dealer margins from `DealerMargins` table
3. Calculate pricing using `CalculateDealerQuote` stored procedure

---

## When Boats Become "Registered"

When a boat is **sold to a customer**:
- `SerialNumberMaster.Active` changes from **0 → 1**
- `SerialNumberRegistrationStatus.Registered` changes from **0 → 1**
- Boat is **NO LONGER** available for new window stickers
- Boat is considered **SOLD**

---

## Key Differences: CPQ vs Legacy Boats

| Field | CPQ Boat (2026) | Legacy Boat (2024) |
|-------|----------------|-------------------|
| `BoatItemNo` | 23ML | 20SF-SPSSR |
| `WebOrderNo` | SOBHO00707 (starts with "SO") | 264615 (number) |
| `PanelColor` | NULL (in config) | METALLIC WHITE |
| `AccentPanel` | NULL (in config) | ACC PNL MET SORREL SMOOTH |
| `TrimAccent` | NULL (in config) | ANTHRACITE SV S |
| Configuration | In `BoatOptions26.CfgName/CfgValue` | In `SerialNumberMaster` columns |

---

## Quick Reference: Table Relationships

```
ERP (CSI/MSSQL)
    ↓ (import_boatoptions_production.py)
MySQL warrantyparts
    ├── SerialNumberMaster (boat details + invoice)
    ├── SerialNumberRegistrationStatus (registration status)
    └── BoatOptions26/25/etc. (configuration + line items)
        ↓ (sStatements: GET_CPQ_LHS_DATA, GET_CPQ_STANDARD_FEATURES)
EOS JavaScript (Window Stickers)
```

---

## Summary: The Formula

**To get unregistered invoiced boats:**

```sql
WHERE InvoiceNo IS NOT NULL   -- Has been invoiced
  AND Active = 0              -- Not registered (SerialNumberMaster)
  AND Registered = 0          -- Not registered (RegistrationStatus)
```

**These are the boats available for:**
- ✅ Window stickers
- ✅ Dealer quotes
- ✅ Dealer inventory management

**These boats are NOT:**
- ❌ Sold to customers
- ❌ Registered
- ❌ In the field

---

**Last Updated:** 2026-02-09
