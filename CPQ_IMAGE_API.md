# CPQ Image API — Research & Integration Notes

## Background

Bennington is building out a new image pipeline via the Infor CPQ `EQ_BuildImages` integration
template. When fully implemented, this will replace the current Liquifire URL construction
approach with direct API calls that return four rendered image links per configured boat.

CPQ ruleset action (ID 2433, Ruleset: Boat):
- Caption: "Pass All Images to EQ"
- Template: `EQ_BuildImages`
- Status: **Not yet fully implemented** — template exists, future configurations will populate it

---

## Image Types Returned

| Attribute | CPQ Formula | Description |
|-----------|-------------|-------------|
| `side` | `=ExteriorImageLink` | Side exterior view |
| `threeQuarter` | `=ElevatedThreeQuarterImageLink` | Elevated 3/4 view |
| `interior` | `=InteriorImageLink` | Interior view |
| `floorplan` | `=model.value.ImageLinkHighRes` | High-res floorplan |

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

Returns an array of `IntegrationOutputDto`:

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
configured before the template was set up).

---

## How to Retrieve headerId and detailId

The two required IDs come from the CPQEQ OrderLine — the **same API already used in
`fetch_cpq_image_urls()` in `import_daily_boats.py`** to retrieve `LastConfigurationImageLink`.

### Existing pipeline (lines 810–825 of `import_daily_boats.py`)

```python
# Step 1 — get Order by SO number → yields headerId
r = requests.get(f"{eq_base}/Order",
                 params={'$filter': f"ExternalId eq '{so}'", '$top': 1}, ...)
order_id = r.json()['items'][0]['Id']   # <-- this is the headerId

# Step 2 — get OrderLine by Order GUID → yields detailId
r2 = requests.get(f"{eq_base}/OrderLine",
                  params={'$filter': f"Order eq '{order_id}'", '$top': 50}, ...)
for line in r2.json()['items']:
    url = line.get('LastConfigurationImageLink')   # currently used
    detail_id = line.get('SourceDetailId')         # <-- this is the detailId
```

The `headerId` is `order_id` (already retrieved on line 816).
The `detailId` is `line['SourceDetailId']` on the same `OrderLine` response (line 821).

Adding support for `LoadIntegrationOutputData` requires **one additional field read**
from the OrderLine response — `SourceDetailId` — with no extra API calls.

A fallback path via `ConfigurationId` already exists for non-standard SO numbers
(SOORE*, SONKF*, etc.) and can be extended the same way.

---

## Current State vs Future State

### Current (Liquifire URL Construction)
- `build_liquifire_url.py` builds Liquifire URLs from CPQ config attributes stored in
  `BoatOptions26` (CfgName/CfgValue rows)
- Only produces a **side view**
- Requires asset normalization, year-walking, and fallback logic for missing assets
- Stored in `SerialNumberMaster.LiquifireImageUrl` + `LiquifireMethod`
- Nightly sweep via `sweep_liquifire_urls.py --today --no-verify` (JAMS job at 9 PM)

### Future (EQ_BuildImages API)
- Call `LoadIntegrationOutputData` with the boat's EQ Order GUID + SourceDetailId
- Returns **4 image types** directly (side, three-quarter, interior, floorplan)
- No asset normalization needed — images rendered by CPQ at configuration time
- Same CPQEQ lookup pipeline already in place
- Will need new DB columns for the additional image types

---

## Migration Path

When the `EQ_BuildImages` template goes live:

1. Add columns to `SerialNumberMaster`:
   - `LiquifireThreeQuarterUrl VARCHAR(2000)`
   - `LiquifireInteriorUrl VARCHAR(2000)`
   - `LiquifireFloorplanUrl VARCHAR(2000)`

2. Update `import_daily_boats.py` Step 2 (serial master import):
   - After fetching `LastConfigurationImageLink`, also call `LoadIntegrationOutputData`
   - Store all 4 image URLs if the template returns data
   - Fall back to existing `build_liquifire_url.py` logic if it returns `[]`

3. Update `sweep_liquifire_urls.py` to also retry boats where the new columns are empty.

---

## Verification

Confirmed working endpoint call (returns 200, empty until template fires):

```python
import requests

token = get_prd_token()
r = requests.get(
    'https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD'
    '/CPQ/api/v4/ProductConfigurator/LoadIntegrationOutputData',
    params={
        'applicationInstance': 'QA2FNBZCKUAUH7QB_PRD',
        'applicationName':     'default',
        'headerId':            '<EQ Order GUID>',
        'detailId':            '<OrderLine.SourceDetailId>',
        'templateId':          'EQ_BuildImages',
    },
    headers={'Authorization': f'Bearer {token}'},
    timeout=30
)
# r.status_code == 200
# r.json() == []  (until template is live)
```
