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

## 3. Update BennTermsCode

Change `BennTermsCode` from `NK` to `N3`:

```xml
<!-- Before -->
<BennTermsCode>NK</BennTermsCode>

<!-- After -->
<BennTermsCode>N3</BennTermsCode>
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
        <BennTermsCode>N3</BennTermsCode>  <!-- Use N3, not NK -->
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

## Summary Checklist

1. ✅ Keep `~0` suffix on ShipToParty IDs (do NOT remove)
2. ✅ Multiple lines per order are fine
3. ✅ Set `ue_LastRecord=0` for all lines except the last
4. ✅ Set `ue_LastRecord=1` for the last line only
5. ✅ Change `BennTermsCode` from `NK` to `N3`

---

## History

- **2026-03-26**: Corrected instructions after successful Syteline acceptance
  - Multiple lines per order confirmed working
  - `~0` suffix should remain on ShipToParty IDs
  - BennTermsCode should be `N3`
