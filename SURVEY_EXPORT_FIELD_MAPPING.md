# Survey Export - Rollick/Aimbase Field Mapping

## Quick Reference: Where Each Field Comes From

This document shows exactly which database table and field is used for each Rollick/Aimbase CSV field.

---

## ✅ REQUIRED FIELDS (Per Rollick Spec)

| Aimbase Field | Database Source | Example Value | Coverage |
|---------------|----------------|---------------|----------|
| **CFSTNAME** | `OwnerRegistrations.OwnerFirstName` | "Sherry" | 100% |
| **CLSTNAME** | `OwnerRegistrations.OwnerLastName` | "Quinlan" | 100% |
| **HIN** | `WarrantyClaimOrderHeaders.OrdHdrBoatSerialNo` | "ETWC8433A121" | 100% |
| **CLAIMNO** | `WarrantyClaimOrderHeaders.PartsOrderID` | "281554" | 100% |
| **CLAIMDT** | `WarrantyClaimOrderHeaders.OrdHdrStatusLastUpd` | "20260127" | 100% |
| **DLRNUMBR** | `WarrantyClaimOrderHeaders.OrdHdrDealerNo` | "226170" | 100% |
| **MODELBRD** | `SerialNumberMaster.Series` | "S" | High |
| **MODELCOD** | `SerialNumberMaster.BoatDesc1` | "20 S STERN RADIUS" | High |
| **CADDRES1** | `OwnerRegistrations.OwnerAddress1` | "4579 Se Rocky Point Way" | High |
| **CCITY** | `OwnerRegistrations.OwnerCity` | "Stuart" | High |
| **CSTATE** | `OwnerRegistrations.OwnerState` | "FL" | High |
| **CCOUNTRY** | `OwnerRegistrations.OwnerCountry` | "US" | High |

---

## ✅ OPTIONAL BUT IMPORTANT FIELDS

| Aimbase Field | Database Source | Example Value | Coverage |
|---------------|----------------|---------------|----------|
| **CPSTCODE** (Zipcode) | `OwnerRegistrations.OwnerZip` | "34997" | 99.9% |
| **CEMAIL** | `OwnerRegistrations.OwnerEmail` | "rquinlan@hitechprofiles.com" | 96.7% |
| **CHMPHONE** | `OwnerRegistrations.OwnerDayPhone` | "(239) 281-1928" | High |
| **MODELYER** | `SerialNumberMaster.SerialModelYear` | "2025" | High |

---

## ✅ OTHER FIELDS (Static or Calculated)

| Aimbase Field | Value | Description |
|---------------|-------|-------------|
| **ACTION** | "A" | Add new record (static) |
| **LANGCODE** | "EN" | English (static) |
| **SRVYTYPE** | "W" | Warranty survey (static) |
| **PRODTYPE** | "PONTOON" | Product type (static) |
| **SENDSRVY** | "true" / "false" | Based on `OrdOptOut` flag |
| **CEXTERNALID** | Same as `PartsOrderID` | External reference |
| **CNOEMAIL** | "NO" | Email preference (static) |

---

## 🔴 DEPRECATED/UNUSED FIELDS

These fields from `WarrantyClaimOrderHeaders` are **NO LONGER USED** because they have poor data quality:

| Field | Why Not Used | Coverage | Better Alternative |
|-------|-------------|----------|-------------------|
| `OrdHdrEmail` | Contains **dealer** emails, not customer | N/A | `OwnerRegistrations.OwnerEmail` |
| `OrdHdrOwnerName` | Full name needs splitting | 100% | Use separate First/Last from OwnerRegistrations |
| `OrdHdrOwnerZip` | Only 0.3% populated! | 0.3% | `OwnerRegistrations.OwnerZip` (99.9%) |
| `OrdHdrOwnerAddress` | Lower quality data | Low | `OwnerRegistrations.OwnerAddress1` |
| `OrdHdrOwnerCity` | Lower quality data | Low | `OwnerRegistrations.OwnerCity` |
| `OrdHdrOwnerState` | Lower quality data | Low | `OwnerRegistrations.OwnerState` |
| `OrdHdrOwnerCountry` | Lower quality data | Low | `OwnerRegistrations.OwnerCountry` |
| `OrdHdrOwnerPhone` | Lower quality data | Low | `OwnerRegistrations.OwnerDayPhone` |

---

## 📊 Data Quality Summary

| Data Source | Purpose | Data Quality |
|------------|---------|--------------|
| **OwnerRegistrations** | Customer contact info | ⭐⭐⭐⭐⭐ Excellent (96-100% coverage) |
| **WarrantyClaimOrderHeaders** | Claim metadata | ⭐⭐⭐ Good (for claim info only) |
| **SerialNumberMaster** | Boat model info | ⭐⭐⭐⭐ Very Good |

---

## 🔄 Join Logic

```sql
FROM WarrantyClaimOrderHeaders wc
LEFT JOIN SerialNumberMaster sn
  ON wc.OrdHdrBoatSerialNo = sn.Boat_SerialNo
LEFT JOIN OwnerRegistrations owner
  ON wc.OrdHdrBoatSerialNo = owner.Boat_SerialNo
WHERE wc.OrdHdrPublicStatus IN ('Approved', 'Completed')
GROUP BY wc.PartsOrderID  -- Handle multiple owners per boat
```

**Key Points:**
- Join on HIN (Boat Serial Number)
- Use `GROUP BY` to handle boats with multiple registration records
- Use most recent owner registration when multiple exist

---

## ✅ Validation Rules

The script applies these validation rules before sending to Rollick/Aimbase:

1. **Email Validation:**
   - Must contain `@` and `.`
   - Cannot be: `na@na.com`, `N/A`, `none`, `noemail`
   - Claims without valid emails are **SKIPPED**

2. **Zipcode Cleaning:**
   - US: Removes non-digits, truncates to 5 digits if longer
   - Canada: Validates postal code format (A1A 1A1)
   - Empty zipcodes are allowed (some records incomplete)

3. **Opt-Out Handling:**
   - `OrdOptOut = 0` → `SENDSRVY = "true"` (send surveys)
   - `OrdOptOut = 1` → `SENDSRVY = "false"` (DON'T send surveys)
   - Opt-out file created separately (not uploaded to FTP)

---

## 📝 Notes

- **Why OwnerRegistrations?** It's the customer registration database with direct customer contact info
- **Why not WarrantyClaimOrderHeaders?** That table contains dealer contact info, not customer contact info
- **Multiple Owners:** Some boats have multiple registration records (previous owners). Script uses most recent.
- **Coverage:** 96.7% of approved claims have valid customer emails (126,546 out of 130,615)

---

## 📞 Questions?

Contact: Michael Nseula (mnseula@benningtonmarine.com)

Database: `ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com/warrantyparts`
