# Liquifire Image Processing

## What is Liquifire?

Liquifire (LiquidPixels) is a dynamic image rendering service at `polarismarine.liquifire.com`. Boat images are **not static files** — they are generated on the fly from parameters embedded in the URL. Every color, option, and angle is encoded in the URL and rendered server-side into a JPEG.

Images are fetched from CPQ's `OrderLine.LastConfigurationImageLink` field and stored in `warrantyparts.SerialNumberMaster.LiquifireImageUrl`.

---

## URL Structure

```
https://polarismarine.liquifire.com/polarismarine
  ?set=cat[pon],asset[23MSB],view[side],tube[std],tubeC1[3b3b3b],...
  &call=url[file:PS/main]
  &sink
```

### Key Parameters

| Param | Purpose | Valid values |
|---|---|---|
| `cat[]` | Render category | `pon` (full boat side), `orthographic` (alt angle) |
| `asset[]` | Boat model template | Must exist in Liquifire library (e.g. `23MSB`, `24LXSFB`) |
| `view[]` | Camera angle | Always use `side` — other values render partial boat |
| `tube[]` / `tubeC1[]` | Tube style / color | hex color code |
| `ppn[]` / `ppnC1[]` | Panel color | hex color code |
| `ap1[]` / `ap1C1[]` | Accent panel | hex color code |
| `arch[]` / `archC1[]` | Arch color | hex color code |
| `bim[]` / `bimC1[]` | Bimini style / color | hex color code |
| `furn[]` | Furniture style | `furn_s_std`, `furn_lxs_dstch`, etc. |
| `furn*[]` | Furniture colors | furnPrime, furnAccnt, furnRoto, etc. |

### Hull vs. Furniture Params
- **Hull color params** (`ppn`, `ap1`, `tube`, `arch`, `bim`) — control the physical boat structure
- **Furniture params** (`furn*`) — control seat/cushion colors only
- A URL with **only** `furn*` params and no hull params renders a **transparent hull** (tubes only visible)

---

## Where the Code Lives

All Liquifire logic is in `import_daily_boats.py`:

| Function | Purpose |
|---|---|
| `fetch_cpq_image_urls(so_numbers, config_id_map, itemno_map)` | Fetches raw URLs from CPQ `OrderLine.LastConfigurationImageLink` |
| `_is_valid_liquifire_image(url)` | Validates a URL returns a real boat JPEG |
| `_normalize_liquifire_url(url, item_no)` | Fixes/normalizes a CPQ URL through a fallback chain |

---

## Fetch Pipeline

1. **Auth** — POST to CPQ PRD token endpoint
2. **Lookup by ExternalId** — `GET /Entities/Order?$filter=ExternalId eq 'SO00936xxx'`
   - ExternalId = `ERP_OrderNo` (Syteline `co_num`, format `SO00936xxx`)
   - **NOT** `external_confirmation_ref` (CPQ-generated ref like `SONVU000005`)
3. **Get OrderLine** — `GET /Entities/OrderLine?$filter=Order eq '{order_guid}'`
4. **Read** `LastConfigurationImageLink` from the line
5. **Fallback** — if ExternalId lookup returns nothing, query by `ConfigurationId`

---

## Normalization Pipeline (`_normalize_liquifire_url`)

Called on every URL returned by CPQ before storing. Fixes known bad patterns:

### Pre-processing (always applied)
1. **Non-Liquifire URL** (e.g. `configurator.inforcloudsuite.com/HighRes2026_24MSB.png`) — extract model name, reset to blank Liquifire base URL
2. **`view[3qtr]` or any non-side view** → `view[side]` (otherwise only deck/rails/bimini render)
3. **`furn[furn_*]` swatch param** → stripped (conflicts with hull rendering, causes GIF response)

### Validation (`_is_valid_liquifire_image`)
Rejects a URL if:
- Response is not a JPEG
- Response is < 10KB (Liquifire returns a ~3-4KB GIF for invalid asset/param combos)
- URL has `furn*` params but no hull color params (`ppn`, `ap1`, `tube`) — hull would be transparent

### Fallback Chain (tried in order)
1. `cat[orthographic]` with original asset + `view[side]`
2. `cat[pon]` with original asset + `view[side]`
3. `cat[pon]`, `asset[{item_no}]`, all original color params preserved
4. `cat[pon]`, `asset[{item_no}]`, `view[side]` — bare hull
5. `cat[pon]`, `asset[{item_no}]`, `view[]` — last bare attempt
6. Stripped item_no variant (e.g. `23M1SB` → `23MSB`, strips middle digit)
7. CPQ model name from configurator URL filename
8. **Year-walk** — if asset year doesn't exist in Liquifire, try ±1, ±2, ±3 years
   - e.g. `20SL` → tries `21SL`, `19SL`, `22SL`, `18SL`, `23SL`, `17SL`
   - e.g. `24MSB` → tries `23MSB` ✓
   - Logs a WARNING in JAMS output when substitution is made
9. **Stock image** — if everything fails, store the generic EOS stock image and log WARNING

### Stock Image URL
```
https://s3.amazonaws.com/eosstatic/images/0/5880c9a7a9d29ae43164c78f/Generic-01.jpg
```

---

## Known CPQ URL Problems (and fixes)

| Problem | Symptom | Cause | Fix |
|---|---|---|---|
| `asset[]` blank | No image | CPQ returned configurator PNG, not Liquifire URL | Extract model from filename, try in Liquifire |
| Asset doesn't exist (e.g. `20SL`, `24MSB`) | No image or GIF | Liquifire library only has certain model years | Year-walk fallback |
| `view[3qtr]` | Only deck/rails/bimini visible | CPQ set wrong camera angle | Normalize to `view[side]` |
| `asset[furn_*]` | Furniture swatch image, not boat | CPQ returned furniture URL | Substitute `item_no` as asset |
| `furn[furn_*]` in hull URL | Transparent hull, tubes only | Furniture swatch param conflicts with hull rendering | Strip `furn[furn_*]` param |
| Only `furn*` params, no hull params | Transparent hull, tubes only | CPQ returned furn-only URL | Rejected by `_is_valid_liquifire_image`, fallback continues |
| Model ends in "SF" suffix | GIF (no asset) | SF = Special Fishing, not in Liquifire | Strip "SF" suffix, try year-walk |

---

## Asset Naming Convention

Liquifire assets follow a `{2-digit-year}{series}{body}` pattern:

```
23MSB   = 2023 M-series, Stern B
24LXSFB = 2024 LXS-series, Fastback
22SSR   = 2022 S-series, Sport R
22SL    = 2022 S-series, L
```

Not all model years exist for every model. Liquifire returns a tiny GIF (~3-4KB) for invalid asset names — use `_is_valid_liquifire_image` to detect this.

---

## Backfill Scripts

### `backfill_snm_by_serials.py`
Uses the same `fetch_cpq_image_urls` and `_normalize_liquifire_url` functions.

**Important:** Pass `ERP_OrderNo` (not `SoNumber`/`external_confirmation_ref`) as the key for `so_numbers`, `config_id_map`, and `itemno_map`. The CPQ API's `ExternalId` field matches `ERP_OrderNo`.

### `backfill_stock_images.py`
Fixes boats that have the generic stock image URL and SO order numbers.

**Usage:**
```bash
python3 backfill_stock_images.py [--dry-run]
```

**What it does:**
1. Queries `SerialNumberMaster` for boats with stock image URL and `WebOrderNo LIKE '%SO%'`
2. Calls `fetch_cpq_image_urls()` to get real URLs from CPQ PRD
3. Updates `LiquifireImageUrl` for boats that got valid URLs

---

## Stock Image Batch Fix (April 2026)

### SF Suffix Pattern Discovery

Found 40 boats with stock images. Root cause: `BoatItemNo` values ending in "SF" (Special Fishing package) don't exist in Liquifire. The SF suffix is a Syteline/EOS code, not used by Liquifire.

**Solution:** Strip "SF" suffix and apply year-walk fallback.

### Asset Mappings Applied

| BoatItemNo | Liquifire Asset | Method |
|------------|-----------------|--------|
| 20SFSF | 20SF | Strip SF |
| 20SLSF | 22SL | Strip SF + year-walk |
| 22MFBSF | 24MFB | Strip SF + year-walk |
| 22MSBSF | 23MSB | Strip SF + year-walk |
| 22SSRSF | 22SSR | Strip SF |
| 23MSBSF | 23MSB | Strip SF |
| 23MSLSF | 24MSL | Strip SF + year-walk |
| 23SSBSF | 22SSB | Strip SF + year-walk |
| 23SSRSF | 22SSR | Strip SF + year-walk |
| 24MSLSF | 24MSL | Strip SF |
| 25QSBWASF | 25QSBW | Strip SF |
| 25QXFBWASF | 25QXFBW | Strip SF |
| 25QXSBWASF | 25QXSBW | Strip SF |
| 25RFBSF | 23RFB | Strip SF + year-walk |
| 25RSRSF | 25RSR | Strip SF |

**Result:** Fixed 26 boats. 14 remain with stock image (no Liquifire asset exists).

### Other Manual Fixes

| Serial | BoatItemNo | Description | Fix Applied |
|--------|------------|-------------|-------------|
| ETWS2208C626 | 22S1SR | 22 S1 STERN RADIUS | `22S1SR` → `23SSR` (S1 → S series + year-walk) |
| ETWS1410B626 | 25QSBA | 25 Q SWINGBACK ARCH | `25QSBA` → `25QSB` (strip 'A' for Arch) |
| ETWS1976C626 | 21SFC | 21 S FISH AND CRUISE | `21SFC` → `22SFC` (year-walk) |

### Manual Fix Process

When the year-walk fallback doesn't find an asset, test variations manually:

```python
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = 'https://polarismarine.liquifire.com/polarismarine'

# Test asset variations
models = ['25QSBA', '25QSB', '24QSBA', '24QSB']  # Try with/without trailing letters

for model in models:
    url = f"{base_url}?set=cat[pon],asset[{model}],view[side]&call=url[file:PS/main]&sink"
    r = requests.get(url, verify=False, timeout=10)
    is_jpeg = 'jpeg' in r.headers.get('Content-Type', '')
    size = len(r.content)
    if is_jpeg and size > 10000:
        print(f'{model}: VALID JPEG, {size:,} bytes')
```

**Common patterns:**
- Remove trailing body code: `25QSBA` → `25QSB` (Swingback Arch → Swingback)
- Year-walk to older year: `21SFC` → `20SF` (Fish and Cruise)
- Some models simply don't exist in Liquifire library — stock image is correct

### SQL to Update Manually

```sql
UPDATE SerialNumberMaster 
SET LiquifireImageUrl = 'https://polarismarine.liquifire.com/polarismarine?set=cat[pon],asset[25QSB],view[side]&call=url[file:PS/main]&sink'
WHERE Boat_SerialNo = 'ETWS1410B626';
```

---

## "Tubes Only" Issue (April 2026)

Some boats were rendering as tubes-only (no deck/panels visible). Root cause: the original URLs from CPQ fallback were missing color parameters.

**Fix:** Rebuild URL with full color config from CPQ matrices using `build_liquifire_url.py`:

```bash
python3 build_liquifire_url.py ETWS1410B626
```

This pulls the boat's `CfgName/CfgValue` from `BoatOptions26`, looks up hex colors in CPQ matrices, and builds a complete URL with:
- `ppn[type],ppnC1[color],ppnOPC1[opacity]` — main panel
- `ap1[type],ap1C1[color],ap1OPC1[opacity]` — accent panel
- `furn[pkg],furnPrime[color],furnAccnt[color]` — furniture colors
- `arch[],archC1[color]` — arch color
- `bim[style],bimC2[color]` — bimini color

### Asset Name Mismatches

Sometimes the `BoatItemNo` doesn't match the Liquifire asset name. Known mappings:

| BoatItemNo | Liquifire Asset | Reason |
|------------|-----------------|--------|
| 25QSBA | 25QSB | Remove trailing 'A' (Arch) |
| 21SFC | 22SFC | Year-walk to newer asset |
| 22S1SR | 23SSR | S1 → S series mapping, year-walk |

### Empty Panel Color (Tubes-Only Render)

If `ppnC1[]` is empty or has wrong hex code, panels won't render. Check:

```sql
SELECT CfgName, CfgValue FROM BoatOptions26 
WHERE BoatSerialNo = 'ETWS...' AND CfgName IN ('panelColor', 'panelType');
```

Then verify the hex mapping in CPQ matrix (e.g., `S1_PanelColors_2026` for S1 series).

**Note:** Dark colors at 80% opacity can appear nearly invisible on certain backgrounds. The CPQ matrix defines these mappings — they are correct per spec even if visually subtle.

### Browser/EOS Caching

If images still show tubes-only after fixing, clear cache:
1. **Hard refresh** in browser (Ctrl+Shift+R or Cmd+Shift+R)
2. Open URL in incognito/private window
3. Clear EOS cache if viewing in EOS portal

---

## Known Missing Liquifire Assets

These BoatItemNo values have no Liquifire asset (as of April 2026):

| Model | Description | Count |
|-------|-------------|-------|
| 20SXSSF | 20 SX Stern Fishing | 1 |
| 22SFCSF | 22 S Fish and Cruise | 1 |
| 23LTSBA | 23 L Bowrider Fastback Arch | 1 |
| 23RSBASF | 23 R Swingback Arch | 1 |
| 23RXFBASF | 23 RX Fastback Arch | 1 |
| 23SXSAPGSF | 23 SX Stern Fishing Ext Aft Pt GT | 1 |
| 24SXSRSF | 24 SX Stern Radius | 1 |
| 25SXSRCSF | 25 SX Stern Radius | 1 |
| 26LXSSBASF | 26 LXS Swingback Arch | 1 |
| 27QXFBWAX2SF | 27 QX Fastback Wind Arch Twin 10'W | 1 |
| 27RXSBWAT2SF | 27 RX Swingback Wind Arch Twin 8'W | 1 |
| 30QXFBWAX2SF | 30 QX Fastback Wind Arch Twin 10'W | 2 |
| 30QXSBWAX2SF | 30 QX Swingback Wind Arch Twin 10'W | 2 |

**Total:** 14 boats with no Liquifire asset. Stock image is the correct fallback.

When new models are added to Liquifire, re-run `backfill_stock_images.py` or test manually.
