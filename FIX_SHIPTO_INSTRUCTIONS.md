# Syteline XML Fix Instructions

## Correct Approach (Updated 2026-03-26)

After testing, the following fixes were confirmed to work with Syteline:

---

## 1. Keep ShipTo `~0` Suffix

**IMPORTANT:** Do NOT remove the `~0` suffix from ShipToParty IDs. Syteline accepts them as-is.

```xml
<!-- CORRECT - Keep the ~0 suffix -->
<ShipToParty>
    <PartyIDs>
        <ID>559236~0</ID>
    </PartyIDs>
</ShipToParty>
```

---

## 2. Multiple Lines Per Order Are Allowed

You can have multiple `<Test_Verenia_BoatLine>` elements within a single `<Test_Verenia_Boat>`.

**Key Rule:** Set `ue_LastRecord` correctly:
- `ue_LastRecord=0` for all lines EXCEPT the last
- `ue_LastRecord=1` for the LAST line only

```xml
<Test_Verenia_Boat>
    <Test_Verenia_BoatHeader>
        ...
    </Test_Verenia_BoatHeader>
    <Test_Verenia_BoatLine>
        ...
        <ue_LastRecord>0</ue_LastRecord>  <!-- First line: 0 -->
    </Test_Verenia_BoatLine>
    <Test_Verenia_BoatLine>
        ...
        <ue_LastRecord>0</ue_LastRecord>  <!-- Middle line: 0 -->
    </Test_Verenia_BoatLine>
    <Test_Verenia_BoatLine>
        ...
        <ue_LastRecord>1</ue_LastRecord>  <!-- Last line: 1 -->
    </Test_Verenia_BoatLine>
</Test_Verenia_Boat>
```

---

## Complete Example

**Working XML Structure:**
```xml
<Test_Verenia_Boat>
    <Test_Verenia_BoatHeader>
        <AlternateDocumentID>
            <ID>WP0523443-S1</ID>
        </AlternateDocumentID>
        <ShipToParty>
            <PartyIDs>
                <ID>559236~0</ID>  <!-- Keep ~0 suffix -->
            </PartyIDs>
        </ShipToParty>
        ...
    </Test_Verenia_BoatHeader>
    <Test_Verenia_BoatLine>
        ...
        <ue_LastRecord>0</ue_LastRecord>  <!-- Not the last line -->
    </Test_Verenia_BoatLine>
    <Test_Verenia_BoatLine>
        ...
        <ue_LastRecord>1</ue_LastRecord>  <!-- Last line -->
    </Test_Verenia_BoatLine>
</Test_Verenia_Boat>
```

---

## 3. Orphaned Lines (Line Exported in Verenia but Missing in Syteline)

**Symptom:** A line shows up in `warrantyparts.PartsOrderLines` with `OrdLineStatus = 'Exported'` but `ERP_OrderNo` is empty. The other line(s) on the same order are already in Syteline.

**Cause:** The original XML split the order into multiple separate `<Test_Verenia_Boat>` elements (e.g., S1 and S2). Only one shipment made it into Syteline.

**Fix:** Re-process the full `PartsOrderID` through the Verenia "Create XML" button — not just the orphaned line. Syteline will receive all lines grouped together and add the missing one to the existing order.

**What NOT to do:**
- Do NOT change `ShipmentID` in MySQL to match line 1 — line 1 is already taken in Syteline and this risks a conflict or duplicate
- Do NOT submit just the orphaned line as a standalone XML — Syteline will create a new separate order instead of attaching to the existing one
- Do NOT manually craft an XML with the same `AlternateDocumentID` as the existing order — Syteline ignores it and still creates a new order

**MySQL query to find orphaned lines:**
```sql
SELECT * FROM warrantyparts.PartsOrderLines
WHERE OrdLineStatus = 'Exported'
AND (ERP_OrderNo IS NULL OR ERP_OrderNo = '')
AND OrdLineSttusLastUpd NOT LIKE '3/31/2026%';
```

---

## Summary Checklist

1. ✅ Keep `~0` suffix on ShipToParty IDs (do NOT remove)
2. ✅ Multiple lines per order are fine
3. ✅ Set `ue_LastRecord=0` for all lines except the last
4. ✅ Set `ue_LastRecord=1` for the last line only

---

## What to Do With a New XML

1. Verify `ShipToParty` ID keeps the `~0` (or `~N`) suffix — do NOT strip it
2. If multiple lines: set `ue_LastRecord=0` on all but the last, `ue_LastRecord=1` on the last
3. If single line: set `ue_LastRecord=1`
4. Save the file as `sytelineExport_YYYY-MM-DD.xml` (use today's date)
5. Commit and push to git

---

## History

- **2026-03-31**: Saved WP0523751 fix (charge parts, dealer 557300~0) — original XML split into S1/S2 as two separate `Test_Verenia_Boat` elements; S1 created Syteline order WP00945882 with line 1 (021650); S2 never created in Syteline; fix re-submits item 014220 as line 2 (WP0523751-02) under same WP0523751-S1 header to attach to WP00945882
- **2026-03-30**: Saved WP0523856 (charge parts, dealer 557300~0, 2 lines: item 021565 qty 2 @ $1190 + item 800001 qty 2 @ $30) — multi-line order, `ue_LastRecord=0` on first line, `ue_LastRecord=1` on last line
- **2026-04-01**: Saved WP0524059 (charge parts, dealer 559236~0 Wilson Marine, 2 lines: item 400303 qty 1 @ $2705 PT tube + item 400303 qty 1 @ $2705 STBD tube, boat ETWD7990H617 22GPDDL, PU carrier, est ship 2026-05-12) — XML was correct, no changes needed
- **2026-03-30**: Saved WN0523811 (no charge parts, dealer 559236~0, item 021665) — XML was already correct, single line with `ue_LastRecord=1`
- **2026-03-26**: Corrected instructions after successful Syteline acceptance
  - Multiple lines per order confirmed working
  - `~0` suffix should remain on ShipToParty IDs
