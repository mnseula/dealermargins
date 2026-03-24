# Fix ShipTo Party ID ~0 Suffix

## Problem
Syteline rejects orders where the ShipTo Party ID contains a `~0` suffix (e.g., `559236~0`).

## Error Pattern
```xml
<ShipToParty>
    <PartyIDs>
        <ID>559236~0</ID>  <!-- INVALID - contains ~0 -->
    </PartyIDs>
</ShipToParty>
```

## Solution
Remove the `~0` suffix from the ShipTo Party ID.

```xml
<ShipToParty>
    <PartyIDs>
        <ID>559236</ID>  <!-- FIXED - removed ~0 -->
    </PartyIDs>
</ShipToParty>
```

## Instructions for LLM

1. Find all `<ShipToParty><PartyIDs><ID>` elements in the XML
2. Check if the ID value ends with `~0`
3. If it does, remove the `~0` suffix, keeping only the numeric portion before it
4. Leave all other elements unchanged

## Example Fix

**Before:**
```xml
<ShipToParty>
    <PartyIDs>
        <ID>559236~0</ID>
    </PartyIDs>
</ShipToParty>
```

**After:**
```xml
<ShipToParty>
    <PartyIDs>
        <ID>559236</ID>
    </PartyIDs>
</ShipToParty>
```

## Notes
- Only modify ShipToParty IDs
- Do NOT modify CarrierParty or other Party IDs
- The fix is a simple string replacement: remove trailing `~0`

---

# Fix Multi-Line Orders Not Accepted by Syteline

## Problem
Syteline only accepted the first 2 orders (S1 and S2). Orders with multiple line items may not process correctly.

## Original Structure (Problem)
```xml
<Test_Verenia_Boat>
    <Test_Verenia_BoatHeader>
        <AlternateDocumentID><ID>WP0523359-S1</ID></AlternateDocumentID>
        ...
    </Test_Verenia_BoatHeader>
    <Test_Verenia_BoatLine>...line -01...</Test_Verenia_BoatLine>
    <Test_Verenia_BoatLine>...line -02...</Test_Verenia_BoatLine>  <!-- Multiple lines in one order -->
</Test_Verenia_Boat>
```

## Solution
Separate each line item into its own `<Test_Verenia_Boat>` wrapper with a unique order suffix (S1, S2, S3, etc.).

## Instructions for LLM

1. Identify all `<Test_Verenia_BoatLine>` elements
2. For each line, create a separate `<Test_Verenia_Boat>` block
3. Increment the order suffix (S1, S2, S3, S4, etc.)
4. Update `<AlternateDocumentID><ID>` to match (e.g., `WP0523359-S3`)
5. Copy the `<Test_Verenia_BoatHeader>` for each new order
6. Include only ONE `<Test_Verenia_BoatLine>` per order
7. Set `ue_LastRecord` to `1` for each line (since it's now the only line)

## Example Fix

**Before (Order S2 with 4 lines):**
```xml
<Test_Verenia_Boat>
    <Test_Verenia_BoatHeader>
        <AlternateDocumentID><ID>WP0523359-S2</ID></AlternateDocumentID>
        ...
    </Test_Verenia_BoatHeader>
    <Test_Verenia_BoatLine>...line -03...</Test_Verenia_BoatLine>
    <Test_Verenia_BoatLine>...line -04...</Test_Verenia_BoatLine>
    <Test_Verenia_BoatLine>...line -05...</Test_Verenia_BoatLine>
    <Test_Verenia_BoatLine>...line -06...</Test_Verenia_BoatLine>
</Test_Verenia_Boat>
```

**After (4 separate orders):**
```xml
<Test_Verenia_Boat>
    <Test_Verenia_BoatHeader>
        <AlternateDocumentID><ID>WP0523359-S3</ID></AlternateDocumentID>
        ...
    </Test_Verenia_BoatHeader>
    <Test_Verenia_BoatLine>...line -03...</Test_Verenia_BoatLine>
</Test_Verenia_Boat>

<Test_Verenia_Boat>
    <Test_Verenia_BoatHeader>
        <AlternateDocumentID><ID>WP0523359-S4</ID></AlternateDocumentID>
        ...
    </Test_Verenia_BoatHeader>
    <Test_Verenia_BoatLine>...line -04...</Test_Verenia_BoatLine>
</Test_Verenia_Boat>

<Test_Verenia_Boat>
    <Test_Verenia_BoatHeader>
        <AlternateDocumentID><ID>WP0523359-S5</ID></AlternateDocumentID>
        ...
    </Test_Verenia_BoatHeader>
    <Test_Verenia_BoatLine>...line -05...</Test_Verenia_BoatLine>
</Test_Verenia_Boat>

<Test_Verenia_Boat>
    <Test_Verenia_BoatHeader>
        <AlternateDocumentID><ID>WP0523359-S6</ID></AlternateDocumentID>
        ...
    </Test_Verenia_BoatHeader>
    <Test_Verenia_BoatLine>...line -06...</Test_Verenia_BoatLine>
</Test_Verenia_Boat>
```

## What Was Fixed (2026-03-24)
- Original file: `sytelineExport_2026_3_24 13_56.xml`
- Lines -01 and -02 were already separate (S1, S2)
- Lines -03 through -06 were grouped under S2
- Split lines -03, -04, -05, -06 into separate orders S3, S4, S5, S6
- Each order now contains exactly one line item
- All headers preserved with updated AlternateDocumentID
