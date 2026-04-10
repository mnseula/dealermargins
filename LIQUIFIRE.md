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

## Backfill Script Notes

`backfill_snm_by_serials.py` uses the same `fetch_cpq_image_urls` and `_normalize_liquifire_url` functions.

**Important:** Pass `ERP_OrderNo` (not `SoNumber`/`external_confirmation_ref`) as the key for `so_numbers`, `config_id_map`, and `itemno_map`. The CPQ API's `ExternalId` field matches `ERP_OrderNo`.
