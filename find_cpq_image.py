#!/usr/bin/env python3
"""
Probe CPQ API for boat image serving endpoints.

We know:
- Models.image_link stores filenames like "HighRes2025 25LTFB.png"
- CPQ/Assets/* and CPQ/Media/* → WS-Fed redirect (browser only)
- CPQ/api/v4 accepts OAuth bearer tokens (loadconfiguration works)
- DataImport v1 /values/{id}/image was tried and failed (status unknown)

Goal: Find the URL pattern that serves the actual image bytes.

Usage:
    python3 find_cpq_image.py [model_id]
    python3 find_cpq_image.py 25LTFB
"""

import sys
import json
import requests
import urllib.parse
import urllib3

urllib3.disable_warnings()

# ── PRD credentials ───────────────────────────────────────────────────────────
PRD_CLIENT_ID     = 'QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo'
PRD_CLIENT_SECRET = '4O7OIZ64sukP1N6YeGZ6IpzsFTG4T6RFkcTZgq6ZwAetb4VoNOOJ1qMkGQAlvnOqqcgaZDlXKux6YEQNvoZQgg'
PRD_SERVICE_KEY   = 'QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9xuXKp_iYp49_M7JuB7UaEo0xjWDqTAE1Q15rQhxojw'
PRD_SERVICE_SECR  = 'IZq8wArFnHi4rESTZ-3SQT5zMgiCQfre8aLM6KirsVmvBhXmGDZS_4TXvCZlD40AjpXX6igL7y8A3svCHV-glg'
PRD_TOKEN_URL     = 'https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2'
PRD_TENANT        = 'QA2FNBZCKUAUH7QB_PRD'
PRD_BASE          = f'https://mingle-ionapi.inforcloudsuite.com/{PRD_TENANT}'

# ── TRN credentials ───────────────────────────────────────────────────────────
TRN_CLIENT_ID     = 'QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8'
TRN_CLIENT_SECRET = 'CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAnyArDH3ZebqYTKAoMq37_aQ'
TRN_SERVICE_KEY   = 'QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw'
TRN_SERVICE_SECR  = 'pAze3yNlj8r6dbcTv-Fn8AiGvhIcs2x-yEgJaMiuoraAJdkFB6iLQFKaFQCP_17KZIYoroUoF_CeEoslHWlXug'
TRN_TOKEN_URL     = 'https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2'
TRN_TENANT        = 'QA2FNBZCKUAUH7QB_TRN'
TRN_BASE          = f'https://mingle-ionapi.inforcloudsuite.com/{TRN_TENANT}'

# ── OptionList ID (model prices list in PRD — contains images) ────────────────
OPTLIST_ID = 'bb38d84e-6493-40c7-b282-9cb9c0df26ae'

TARGET_MODEL = sys.argv[1] if len(sys.argv) > 1 else '25LTFB'


def get_token(token_url, client_id, client_secret, service_key, service_secr):
    resp = requests.post(token_url, data={
        'grant_type':    'password',
        'client_id':     client_id,
        'client_secret': client_secret,
        'username':      service_key,
        'password':      service_secr,
    }, verify=False, timeout=30)
    resp.raise_for_status()
    return resp.json()['access_token']


def probe(session, url, label, method='GET', accept='*/*'):
    headers_override = dict(session.headers)
    headers_override['Accept'] = accept
    try:
        if method == 'GET':
            resp = session.get(url, headers=headers_override, timeout=15, verify=False,
                               allow_redirects=False)
        else:
            resp = session.request(method, url, headers=headers_override, timeout=15, verify=False,
                                   allow_redirects=False)

        ct = resp.headers.get('Content-Type', '')
        loc = resp.headers.get('Location', '')
        is_image = 'image' in ct or resp.status_code == 200 and len(resp.content) > 1000

        sym = '✅' if resp.status_code == 200 and is_image else \
              '📄' if resp.status_code == 200 else \
              '🔀' if resp.status_code in (301, 302, 307, 308) else \
              '❌'

        print(f"\n  {sym} [{resp.status_code}] {label}")
        print(f"     URL: {url}")
        if resp.status_code == 200:
            print(f"     Content-Type: {ct}")
            print(f"     Content-Length: {len(resp.content)} bytes")
            if 'image' in ct:
                print(f"     *** IMAGE FOUND! ***")
            elif len(resp.content) < 500:
                print(f"     Body: {resp.text[:300]}")
        elif resp.status_code in (301, 302, 307, 308):
            if 'wsfed' in loc.lower() or 'sso' in loc.lower():
                print(f"     → WS-Fed redirect (browser auth required)")
            else:
                print(f"     → Redirect to: {loc[:200]}")
        else:
            body = resp.text[:200] if resp.text else '(empty)'
            print(f"     Body: {body}")

        return resp
    except Exception as e:
        print(f"\n  ❌ [ERR] {label}: {e}")
        return None


def main():
    print(f"Getting PRD token...")
    prd_token = get_token(PRD_TOKEN_URL, PRD_CLIENT_ID, PRD_CLIENT_SECRET,
                          PRD_SERVICE_KEY, PRD_SERVICE_SECR)
    print("PRD token OK")

    print(f"Getting TRN token...")
    trn_token = get_token(TRN_TOKEN_URL, TRN_CLIENT_ID, TRN_CLIENT_SECRET,
                          TRN_SERVICE_KEY, TRN_SERVICE_SECR)
    print("TRN token OK")

    prd = requests.Session()
    prd.headers.update({'Authorization': f'Bearer {prd_token}', 'Accept': 'application/json'})

    trn = requests.Session()
    trn.headers.update({'Authorization': f'Bearer {trn_token}', 'Accept': 'application/json'})

    # ── Step 1: Get the OptionList value record for our target model ──────────
    print(f"\n{'='*60}")
    print(f"STEP 1: Fetch OptionList value for model {TARGET_MODEL}")
    print(f"{'='*60}")

    ol_url = (f"{PRD_BASE}/CPQ/DataImport/{PRD_TENANT}/v1/OptionLists"
              f"/{OPTLIST_ID}/values")
    resp = prd.get(ol_url, params={'$filter': f"value eq '{TARGET_MODEL}'",
                                   '$top': 1},
                   verify=False, timeout=30)
    print(f"  OptionList query: {resp.status_code}")

    value_id = None
    image_filename = None
    image_hi_res = None

    if resp.status_code == 200:
        items = resp.json().get('result', [])
        if items:
            item = items[0]
            value_id = item.get('id')
            image_filename = item.get('imageLink') or item.get('image_link')
            custom = item.get('customProperties', {})
            image_hi_res = custom.get('ImageLinkHighRes') or custom.get('imagelinkhighres')
            print(f"  Value ID:    {value_id}")
            print(f"  imageLink:   {image_filename}")
            print(f"  HighRes:     {image_hi_res}")
            print(f"  Full item keys: {list(item.keys())}")
        else:
            print(f"  No results for {TARGET_MODEL}")
            print(f"  Response: {json.dumps(resp.json(), indent=2)[:400]}")
    else:
        print(f"  Failed: {resp.text[:300]}")

    # Fallback: use known values from previous session
    if not value_id:
        value_id = 'b24a266c-b5a7-4b0d-9d95-cf7f040e7a39'
        print(f"  Using fallback value_id: {value_id}")
    if not image_filename:
        image_filename = f'HighRes2025 {TARGET_MODEL}.png'
        print(f"  Using fallback filename: {image_filename}")
    if not image_hi_res:
        image_hi_res = image_filename

    filename_encoded = urllib.parse.quote(image_filename, safe='')
    hi_res_encoded   = urllib.parse.quote(image_hi_res, safe='') if image_hi_res else filename_encoded

    print(f"\n  Probing with:")
    print(f"    value_id = {value_id}")
    print(f"    filename = {image_filename}")
    print(f"    filename (URL encoded) = {filename_encoded}")

    # ── Step 2: Probe DataImport v1 image endpoint ────────────────────────────
    print(f"\n{'='*60}")
    print(f"STEP 2: DataImport v1 image endpoint (PRD)")
    print(f"{'='*60}")

    probe(prd,
          f"{PRD_BASE}/CPQ/DataImport/{PRD_TENANT}/v1/OptionLists/{OPTLIST_ID}/values/{value_id}/image",
          "DataImport v1 /values/{id}/image (PRD)", accept='image/*,*/*')

    # ── Step 3: Probe DataImport v2 image endpoints ───────────────────────────
    print(f"\n{'='*60}")
    print(f"STEP 3: DataImport v2 image endpoints")
    print(f"{'='*60}")

    probe(prd,
          f"{PRD_BASE}/CPQ/DataImport/v2/OptionLists/{OPTLIST_ID}/values/{value_id}/image",
          "DataImport v2 /values/{id}/image (PRD)", accept='image/*,*/*')

    probe(trn,
          f"{TRN_BASE}/CPQ/DataImport/v2/OptionLists/{OPTLIST_ID}/values/{value_id}/image",
          "DataImport v2 /values/{id}/image (TRN)", accept='image/*,*/*')

    # ── Step 4: Probe CPQ api/v4 image endpoints ──────────────────────────────
    print(f"\n{'='*60}")
    print(f"STEP 4: CPQ api/v4 image endpoints (TRN)")
    print(f"{'='*60}")

    apiv4_base = f"{TRN_BASE}/CPQ/api/v4"

    # Common api/v4 asset patterns
    patterns = [
        (f"{apiv4_base}/assets/{filename_encoded}",                      "api/v4 /assets/{filename}"),
        (f"{apiv4_base}/assets/{hi_res_encoded}",                        "api/v4 /assets/{hi_res_filename}"),
        (f"{apiv4_base}/media/{filename_encoded}",                       "api/v4 /media/{filename}"),
        (f"{apiv4_base}/images/{filename_encoded}",                      "api/v4 /images/{filename}"),
        (f"{apiv4_base}/parts/Default/Boat/image",                       "api/v4 /parts/Default/Boat/image"),
        (f"{apiv4_base}/parts/Default/Boat/assets",                      "api/v4 /parts/Default/Boat/assets"),
        (f"{apiv4_base}/valuelist/{OPTLIST_ID}/values/{value_id}/image", "api/v4 /valuelist/{listId}/values/{id}/image"),
        (f"{apiv4_base}/optionlists/{OPTLIST_ID}/values/{value_id}/image","api/v4 /optionlists/{listId}/values/{id}/image"),
        (f"{apiv4_base}/documents/{filename_encoded}",                   "api/v4 /documents/{filename}"),
        (f"{apiv4_base}/documents/{hi_res_encoded}",                     "api/v4 /documents/{hi_res_filename}"),
    ]

    for url, label in patterns:
        probe(trn, url, label, accept='image/*,*/*')

    # Also try PRD variants of api/v4
    print(f"\n{'='*60}")
    print(f"STEP 5: CPQ api/v4 image endpoints (PRD)")
    print(f"{'='*60}")

    apiv4_prd = f"{PRD_BASE}/CPQ/api/v4"
    for suffix, label in [
        (f"/assets/{filename_encoded}",                       "api/v4 /assets/{filename}"),
        (f"/assets/{hi_res_encoded}",                         "api/v4 /assets/{hi_res_filename}"),
        (f"/valuelist/{OPTLIST_ID}/values/{value_id}/image",  "api/v4 /valuelist/{listId}/values/{id}/image"),
        (f"/optionlists/{OPTLIST_ID}/values/{value_id}/image","api/v4 /optionlists/{listId}/values/{id}/image"),
    ]:
        probe(prd, apiv4_prd + suffix, f"(PRD) {label}", accept='image/*,*/*')

    # ── Step 6: Check if api/v4 has a discovery endpoint ─────────────────────
    print(f"\n{'='*60}")
    print(f"STEP 6: Explore api/v4 root for documentation")
    print(f"{'='*60}")

    for url, label in [
        (f"{apiv4_base}",          "api/v4 root"),
        (f"{apiv4_base}/",         "api/v4 root /"),
        (f"{apiv4_base}/swagger",  "api/v4 /swagger"),
        (f"{apiv4_base}/openapi",  "api/v4 /openapi"),
        (f"{apiv4_base}/help",     "api/v4 /help"),
        (f"{apiv4_base}/metadata", "api/v4 /metadata"),
    ]:
        probe(trn, url, label)

    print(f"\n{'='*60}")
    print(f"DONE")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
