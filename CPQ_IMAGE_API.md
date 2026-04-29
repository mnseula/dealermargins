# CPQ Image API — Research & Integration Notes

## Background

Bennington is building out a new image pipeline via the Infor CPQ `EQ_BuildImages` integration
template. When fully implemented, this will replace the current Liquifire URL construction
approach with direct API calls that return four complete Liquifire URLs per configured boat —
the same URLs CPQ already generates at configuration time, just all 4 views at once.

CPQ ruleset action (ID 2433, Ruleset: Boat):
- Caption: "Pass All Images to EQ"
- Template: `EQ_BuildImages`
- Status: **Not yet fully implemented** — template exists, future configurations will populate it

**Endpoint is reachable and returning clean 200s today.** Data will flow as soon as
Bennington activates the template on their end.

---

## Image Types Returned

All 4 values are complete, ready-to-use Liquifire URLs — no construction or normalization needed.

| Attribute | CPQ Formula | DB Column (target) |
|-----------|-------------|-------------------|
| `side` | `=ExteriorImageLink` | `LiquifireImageUrl` *(existing)* |
| `threeQuarter` | `=ElevatedThreeQuarterImageLink` | `LiquifireThreeQuarterUrl` *(new)* |
| `interior` | `=InteriorImageLink` | `LiquifireInteriorUrl` *(new)* |
| `floorplan` | `=model.value.ImageLinkHighRes` | `LiquifireFloorplanUrl` *(new)* |

---

## API Endpoint

```
GET https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/api/v4
    /ProductConfigurator/LoadIntegrationOutputData
```

### Authentication

OAuth2 password grant using PRD service credentials (see CLAUDE.md).

### Required Parameters

| Parameter | Value | How to Obtain |
|-----------|-------|---------------|
| `applicationInstance` | `QA2FNBZCKUAUH7QB_PRD` | Fixed — PRD tenant ID |
| `applicationName` | `default` | Fixed — CPQ workspace name |
| `headerId` | EQ Order GUID | `OrderLine.Order` from CPQEQ API |
| `detailId` | EQ OrderLine SourceDetailId UUID | `OrderLine.SourceDetailId` from CPQEQ API |
| `templateId` | `EQ_BuildImages` | Fixed |

### Response Schema

Returns an array of `IntegrationOutputDto`. Each attribute value is a complete Liquifire URL,
ready to insert directly into the database.

```json
[
  {
    "templateName": "EQ_BuildImages",
    "integrationOutputId": "<id EQ uses to reference this data>",
    "attributes": [
      { "name": "side",         "value": "https://polarismarine.liquifire.com/..." },
      { "name": "threeQuarter", "value": "https://polarismarine.liquifire.com/..." },
      { "name": "interior",     "value": "https://polarismarine.liquifire.com/..." },
      { "name": "floorplan",    "value": "https://polarismarine.liquifire.com/..." }
    ]
  }
]
```

Returns `[]` if the template has not yet fired for the given configuration (e.g. boats
configured before the template was activated). Fall back to existing `build_liquifire_url.py`
logic in that case.

---

## How to Retrieve headerId and detailId

The two required IDs come from the CPQEQ OrderLine — the **same API already used in
`fetch_cpq_image_urls()` in `import_daily_boats.py`** to retrieve `LastConfigurationImageLink`.
No new API calls are needed — just read one additional field from the existing response.

### Existing pipeline (`import_daily_boats.py` lines 810–825)

```python
# Step 1 — get Order by SO number → yields headerId
r = requests.get(f"{eq_base}/Order",
                 params={'$filter': f"ExternalId eq '{so}'", '$top': 1}, ...)
order_id = r.json()['items'][0]['Id']       # <-- headerId

# Step 2 — get OrderLine by Order GUID → yields detailId
r2 = requests.get(f"{eq_base}/OrderLine",
                  params={'$filter': f"Order eq '{order_id}'", '$top': 50}, ...)
for line in r2.json()['items']:
    url       = line.get('LastConfigurationImageLink')  # currently stored as side view
    detail_id = line.get('SourceDetailId')              # <-- detailId (add this read)

# Step 3 — call LoadIntegrationOutputData (add this block)
r3 = requests.get(f"{cpq_base}/ProductConfigurator/LoadIntegrationOutputData",
                  params={
                      'applicationInstance': 'QA2FNBZCKUAUH7QB_PRD',
                      'applicationName':     'default',
                      'headerId':            order_id,
                      'detailId':            detail_id,
                      'templateId':          'EQ_BuildImages',
                  }, ...)
outputs = {a['name']: a['value'] for a in r3.json()[0]['attributes']} if r3.json() else {}
# outputs = {'side': '...', 'threeQuarter': '...', 'interior': '...', 'floorplan': '...'}
```

A fallback path via `ConfigurationId` already exists for non-standard SO numbers
(SOORE*, SONKF*, etc.) and can be extended the same way.

---

## Current State vs Future State

### Current (Liquifire URL Construction)
- `build_liquifire_url.py` builds Liquifire URLs from CPQ config attributes in `BoatOptions26`
- Only produces a **side view**
- Requires asset normalization, year-walking, and fallback logic for missing assets
- Stored in `SerialNumberMaster.LiquifireImageUrl` + `LiquifireMethod`
- Nightly sweep via `sweep_liquifire_urls.py --today --no-verify` (JAMS job at 9 PM)
- Legacy/non-CPQ boats (BoatOptions25, SNM color fallback) will **continue using this path**

### Future (EQ_BuildImages API) — CPQ boats only
- Call `LoadIntegrationOutputData` with Order GUID + SourceDetailId
- Returns **4 complete Liquifire URLs** — no construction or normalization needed
- Same CPQEQ lookup already in place — one extra field read + one extra API call
- Store all 4 URLs in `SerialNumberMaster`

---

## Implementation Checklist

When Bennington confirms the `EQ_BuildImages` template is live in PRD:

- [ ] **Add 3 columns** to `SerialNumberMaster` (both `warrantyparts` and `warrantyparts_test`):
  ```sql
  ALTER TABLE SerialNumberMaster ADD COLUMN LiquifireThreeQuarterUrl VARCHAR(2000) NOT NULL DEFAULT '';
  ALTER TABLE SerialNumberMaster ADD COLUMN LiquifireInteriorUrl      VARCHAR(2000) NOT NULL DEFAULT '';
  ALTER TABLE SerialNumberMaster ADD COLUMN LiquifireFloorplanUrl     VARCHAR(2000) NOT NULL DEFAULT '';
  ```

- [ ] **Update `fetch_cpq_image_urls()`** in `import_daily_boats.py`:
  - Read `SourceDetailId` from the OrderLine response (line ~821)
  - Call `LoadIntegrationOutputData` after getting the OrderLine
  - Store all 4 URLs; fall back to `LastConfigurationImageLink` + `build_liquifire_url.py` if `[]`

- [ ] **Update `sweep_liquifire_urls.py`**:
  - Include boats where any of the 4 URL columns are empty
  - On a successful API response, write all 4 columns

- [ ] **Verify first live boat** end-to-end — confirm all 4 URLs render valid JPEGs

- [ ] **Front end** — wire up the 3 new image views (three-quarter, interior, floorplan)
  in the EOS dealer interface

---

## Verification

Confirmed working endpoint call today (2026-04-29). Returns 200 with empty array
because template not yet activated — no data issue, purely a template timing issue.

```python
import requests

token = get_prd_token()
r = requests.get(
    'https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD'
    '/CPQ/api/v4/ProductConfigurator/LoadIntegrationOutputData',
    params={
        'applicationInstance': 'QA2FNBZCKUAUH7QB_PRD',
        'applicationName':     'default',
        'headerId':            '<order_id from OrderLine.Order>',
        'detailId':            '<OrderLine.SourceDetailId>',
        'templateId':          'EQ_BuildImages',
    },
    headers={'Authorization': f'Bearer {token}'},
    timeout=30
)
# r.status_code == 200  ✓
# r.json() == []        (will populate once template is live)
```
