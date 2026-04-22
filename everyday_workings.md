# Everyday Workings — Common DB Tasks

Quick reference for recurring manual tasks against the Bennington MySQL databases.

**Databases:**
- `warrantyparts` — production (SerialNumberMaster, PartsOrderHeader, DealerAddr, etc.)
- `Eos` — EOS platform data (dealers, dealer_forecast_new, etc.)
- `warrantyparts_test` — CPQ catalog tables (Models, Dealers, ModelPerformance, etc.)

---

## 1. Look Up a Boat by Serial Number (HIN)

```sql
SELECT
    Boat_SerialNo, BoatItemNo, SerialModelYear,
    DealerNumber, DealerName, DealerCity, DealerState,
    ParentRepName, InvoiceNo, InvoiceDateYYYYMMDD,
    ERP_OrderNo, WebOrderNo, Presold, LiquifireImageUrl
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = 'ETWS0644I425';
```

**Key fields:**
- `DealerNumber` — zero-padded dealer number (e.g. `00000050`)
- `ERP_OrderNo` — Syteline order (e.g. `SO00922818`)
- `WebOrderNo` — EOS web order number
- `LiquifireImageUrl` — boat rendering URL (NULL if not yet populated)

---

## 2. Change a Dealer on a Boat

Use when a boat needs to be reassigned to a different dealer.

### Step 1 — Look up the new dealer in Eos
```sql
SELECT DlrNo, DealerName, DealerDBA, Add1, City, State, Zip, Country
FROM Eos.dealers
WHERE DlrNo LIKE '%50'          -- search by number
   OR DealerName LIKE '%pontoon%'; -- or by name
```

### Step 2 — Preview the change
```sql
SELECT Boat_SerialNo, DealerNumber, DealerName, DealerCity, DealerState, DealerZip
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = 'ETWS0644I425';
```

### Step 3 — Apply the update (get approval before running)
```sql
UPDATE warrantyparts.SerialNumberMaster SET
    DealerNumber  = '00000050',
    DealerName    = 'PONTOON BOAT, LLC',
    DealerCity    = 'ELKHART',
    DealerState   = 'IN',
    DealerZip     = '46517',
    DealerCountry = 'USA'
WHERE Boat_SerialNo = 'ETWS0644I425';
```

### Step 4 — Verify
```sql
SELECT Boat_SerialNo, DealerNumber, DealerName, DealerCity, DealerState
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = 'ETWS0644I425';
```

### To reverse
```sql
UPDATE warrantyparts.SerialNumberMaster SET
    DealerNumber  = '80459',
    DealerName    = 'DBA: REEDER TRAUSCH MARINE INDY HURLESS ANDERSON, CORP',
    DealerCity    = 'INDIANAPOLIS',
    DealerState   = 'IN',
    DealerZip     = '46217',
    DealerCountry = 'USA'
WHERE Boat_SerialNo = 'ETWS0644I425';
```

---

## 3. Fix a Dealer Ship-To Address Error in Syteline XML (~1 vs ~0)

**Symptom:** Syteline rejects a parts order XML with a `~1` ship-to party ID.
**Cause:** The dealer's `DealerAddr` table has `isDefault = 1` on a non-zero `Cust_Seq` row
instead of `Cust_Seq = 0`. The XML generator reads `isDefault` and produces `~1`.
Most dealers have `isDefault = 1` on `Cust_Seq = 0`, which correctly generates `~0`.

### Step 1 — Find the dealer number
```sql
SELECT DlrNo, DealerName, Add1, City, State
FROM Eos.dealers
WHERE DealerName LIKE '%wilson%';
```

### Step 2 — Inspect their DealerAddr rows
```sql
SELECT Cust_Num, Cust_Seq, Addr_Name, Addr1, City, State, isDefault
FROM warrantyparts.DealerAddr
WHERE TRIM(Cust_Num) = '559236'
ORDER BY Cust_Seq;
```

Look for which `Cust_Seq` has `isDefault = 1`. If it is not `Cust_Seq = 0`, that is the problem.

### Step 3 — Confirm the correct default address with the business, then fix
```sql
-- Set Seq 0 as default
UPDATE warrantyparts.DealerAddr
SET isDefault = 1
WHERE TRIM(Cust_Num) = '559236' AND Cust_Seq = '0';

-- Remove default from the wrong row
UPDATE warrantyparts.DealerAddr
SET isDefault = 0
WHERE TRIM(Cust_Num) = '559236' AND Cust_Seq = '7';
```

### To reverse
```sql
UPDATE warrantyparts.DealerAddr SET isDefault = 1 WHERE TRIM(Cust_Num) = '559236' AND Cust_Seq = '7';
UPDATE warrantyparts.DealerAddr SET isDefault = 0 WHERE TRIM(Cust_Num) = '559236' AND Cust_Seq = '0';
```

**Note:** `DealerAddr.Cust_Num` is stored with leading spaces — always use `TRIM(Cust_Num)` in WHERE clauses.

---

## 4. Populate Liquifire Image URL for a Boat

### For 2026 model year boats (in BoatOptions26)
```bash
python3 build_liquifire_url.py ETWS0644I425
```
This queries CPQ TRN color matrices, builds a parameterized Liquifire URL, tests it,
and writes it to `warrantyparts.SerialNumberMaster.LiquifireImageUrl`.

### Check which BoatOptions table a boat is in
```sql
-- Check BoatOptions26 (2026 MY boats)
SELECT BoatSerialNo, BoatModelNo FROM warrantyparts.BoatOptions26
WHERE BoatSerialNo = 'ETWS0644I425' LIMIT 1;

-- Check BoatOptions25 (2025 MY boats — use BoatSerialNo not Boat_SerialNo)
SELECT BoatSerialNo, BoatModelNo FROM warrantyparts.BoatOptions25
WHERE BoatSerialNo = 'ETWS0644I425' LIMIT 1;
```

**Note:** `build_liquifire_url.py` only reads `BoatOptions26`. Boats invoiced in the 2025
model year (InvoiceDateYYYYMMDD starting with `2025`) will be in `BoatOptions25` and will
show `SKIP — no model in BoatOptions26`. These need manual URL construction or a script
update to support BoatOptions25.

### Check if a URL is already populated
```sql
SELECT Boat_SerialNo, BoatItemNo, LiquifireImageUrl
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = 'ETWS0644I425';
```

---

## 5. Look Up All Ship-To Addresses for a Dealer

```sql
SELECT Cust_Num, Cust_Seq, Addr_Name, Addr1, City, State, Zip, isDefault
FROM warrantyparts.DealerAddr
WHERE TRIM(Cust_Num) = '559236'
ORDER BY Cust_Seq;
```

- `Cust_Seq = 0` with `isDefault = 1` = normal primary address
- `Cust_Seq >= 1` = additional ship-to locations
- `isDefault = 1` = the address the XML generator uses for Syteline

---

## 6. Find a Dealer's Info

### By name
```sql
SELECT DlrNo, DealerName, DealerDBA, Add1, City, State, Zip,
       SalesPerson, Default_Terms_Code, CustomerTypeDesc
FROM Eos.dealers
WHERE DealerName LIKE '%wilson%';
```

### By dealer number
```sql
SELECT * FROM Eos.dealers WHERE DlrNo = '00559236';
```

**Note:** `DlrNo` is stored zero-padded to 8 characters (e.g. `00559236`). Search with
`LIKE '%559236'` if you only have the short number.

---

## 7. Check Parts Orders for a Dealer

```sql
SELECT PartsOrderID, OrdHdrDealerNo, OrdHdrDealer,
       OrdHdrAddress, OrdHdrCity, OrdHdrState,
       OrdHdrPublicStatus, OrdHdrStatus, HdrCreateDate
FROM warrantyparts.PartsOrderHeader
WHERE OrdHdrDealerNo LIKE '%559236%'
ORDER BY HdrCreateDate DESC
LIMIT 20;
```

---

## Key Tables Quick Reference

| Table | Database | What It Holds |
|---|---|---|
| `SerialNumberMaster` | `warrantyparts` | Master HIN registry — one row per boat |
| `DealerAddr` | `warrantyparts` | All ship-to addresses per dealer (keyed by Cust_Num + Cust_Seq) |
| `PartsOrderHeader` | `warrantyparts` | Parts order headers from EOS portal |
| `PartsOrderLines` | `warrantyparts` | Line items for each parts order |
| `dealers` | `Eos` | Active dealer list with contact info, rep, terms |
| `dealer_forecast_new` | `Eos` | Monthly dealer forecast data (12 period columns) |
| `BoatOptions26` | `warrantyparts` | 2026 MY boat line items and CPQ config attributes |
| `BoatOptions25` | `warrantyparts` | 2025 MY boat line items (column = `BoatSerialNo`, not `Boat_SerialNo`) |
| `Dealers` | `warrantyparts_test` | CPQ-sourced dealer list (2,342 rows, updated by load_cpq_data.py) |

---

## Notes

- Always use `TRIM(Cust_Num)` when querying `DealerAddr` — values have leading spaces.
- `BoatOptions25` uses `BoatSerialNo`; `SerialNumberMaster` uses `Boat_SerialNo` (with underscore).
- Never run UPDATE or DELETE without previewing with a SELECT first.
- `warrantyparts` is production — changes are immediate and live.
- The `dealermaster - use the one in eos` table in `warrantyparts` is legacy/stale. Use `Eos.dealers` instead.
