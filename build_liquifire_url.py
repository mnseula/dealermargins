#!/usr/bin/env python3
"""
build_liquifire_url.py

Automatically builds and stores Liquifire image URLs for CPQ boats that are
missing LiquifireImageUrl in SerialNumberMaster.

Data sources:
  - BoatOptions26: CfgName/CfgValue config for each CPQ boat
  - CPQ TRN matrices: LP color/asset mappings
  - SerialNumberMaster: where the URL is stored

Run:
    python3 build_liquifire_url.py              # process missing URLs only
    python3 build_liquifire_url.py --all        # rebuild all CPQ boat URLs
    python3 build_liquifire_url.py --dry-run    # build but don't store
    python3 build_liquifire_url.py ETWXXXX626   # specific serial(s)
"""

import sys
import requests
import mysql.connector
from snm_color_map import snm_to_config

# ── Auth ─────────────────────────────────────────────────────────────────────

TRN_TOKEN_URL = 'https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2'
TRN_CREDS = dict(
    grant_type='password',
    client_id='QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8',
    client_secret='CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAnyArDH3ZebqYTKAoMq37_aQ',
    username='QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw',
    password='pAze3yNlj8r6dbcTv-Fn8AiGvhIcs2x-yEgJaMiuoraAJdkFB6iLQFKaFQCP_17KZIYoroUoF_CeEoslHWlXug',
)
TRN_BASE = 'https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN'

DB = dict(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
)

LIQUIFIRE_BASE = 'https://polarismarine.liquifire.com/polarismarine'

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_trn_token():
    r = requests.post(TRN_TOKEN_URL, data=TRN_CREDS, timeout=15)
    r.raise_for_status()
    return r.json()['access_token']


def fetch_matrix(token, name):
    """Return list of detail rows for a CPQ matrix."""
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.get(f'{TRN_BASE}/CPQ/DataImport/v2/Matrices/{name}/values',
                     headers=headers, timeout=15)
    if r.status_code == 204:
        return []
    r.raise_for_status()
    return r.json()['result']['details']


def build_lookup(rows, key_field):
    """Index matrix rows by a key field (case-insensitive)."""
    return {str(row.get(key_field, '')).upper(): row for row in rows if row.get(key_field)}


def g(row, *fields, default=''):
    """Get first non-empty value from a row dict."""
    for f in fields:
        v = row.get(f, '')
        if v:
            return str(v)
    return default


# ── Matrix loading ────────────────────────────────────────────────────────────

def load_matrices(token):
    print('Loading CPQ color matrices...')
    matrices = {}

    # Base vinyl → furniture LP colors
    rows = fetch_matrix(token, 'OPTMTX_BaseVinyl')
    matrices['base_vinyl'] = build_lookup(rows, 'Item')

    # Furniture accents → accent LP colors
    rows = fetch_matrix(token, 'OPTMTX_FurnitureAccents')
    matrices['furn_accent'] = build_lookup(rows, 'Item')

    # Furniture upgrades → furn LPAsset
    rows = fetch_matrix(token, 'OPTMTX_FurnitureUpgrades')
    matrices['furn_upgrades'] = build_lookup(rows, 'Item')

    # Bimini aft → bim LPAsset
    rows = fetch_matrix(token, 'OPTMTX_BiminiAft')
    matrices['bimini_aft'] = build_lookup(rows, 'Value')

    # Canvas → LPColor/LPOpacity
    rows = fetch_matrix(token, 'OPTMTX_Canvas')
    matrices['canvas'] = build_lookup(rows, 'Value')

    # Panel colors per series — keyed as "{series}|{QuestionCode}|{AnswerCode}"
    panel_map = {}
    for series in ['M', 'S', 'Q', 'QX', 'R', 'RT', 'RX', 'LXS', 'LT', 'S1', 'M1']:
        name = f'{series}_PanelColors_2026'
        rows = fetch_matrix(token, name)
        for row in rows:
            qc = str(row.get('QuestionCode', '')).upper()
            ac = str(row.get('AnswerCode', '')).upper()
            if qc and ac:
                panel_map[f'{series.upper()}|{qc}|{ac}'] = row
                # Also store without series prefix as fallback
                panel_map[f'|{qc}|{ac}'] = row
    matrices['panel_colors'] = panel_map

    print(f'  base_vinyl: {len(matrices["base_vinyl"])} entries')
    print(f'  furn_accent: {len(matrices["furn_accent"])} entries')
    print(f'  furn_upgrades: {len(matrices["furn_upgrades"])} entries')
    print(f'  bimini_aft: {len(matrices["bimini_aft"])} entries')
    print(f'  canvas: {len(matrices["canvas"])} entries')
    print(f'  panel_colors: {len(matrices["panel_colors"])} entries')
    return matrices


# ── Config extraction ─────────────────────────────────────────────────────────

def get_boat_config(cur, serial):
    """Return dict of CfgName→CfgValue for a CPQ boat from BoatOptions26, falling back to BoatOptions25."""
    cur.execute("""
        SELECT CfgName, CfgValue, BoatModelNo, Series
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
        ORDER BY LineNo, LineSeqNo
    """, (serial,))
    config = {}
    model = None
    series = None
    for row in cur.fetchall():
        cfg_name, cfg_val, boat_model, boat_series = row
        if cfg_name and cfg_val:
            config[cfg_name] = cfg_val
        if boat_model and boat_model not in ('Base Boat', ''):
            model = boat_model
        if boat_series:
            series = boat_series

    # BoatOptions25 has no CfgName/CfgValue — fall back for model/series only
    if not model:
        cur.execute("""
            SELECT DISTINCT BoatModelNo, Series
            FROM BoatOptions25
            WHERE BoatSerialNo = %s AND BoatModelNo IS NOT NULL AND BoatModelNo != ''
            LIMIT 1
        """, (serial,))
        row = cur.fetchone()
        if row:
            model, series = row[0], row[1]

    return config, model, series


# ── LP panel type mapping ─────────────────────────────────────────────────────

# CPQ panel/accent panel type codes → Liquifire panel type codes
PANEL_TYPE_LP = {
    'PP_SMTH': 'sm',
    'PP_TEXT': 'cr',
    'AP_SNG_SMTH': 'sm',
    'AP_SNG_TEXT': 'cr',
    'AP_DUL_SMTH': 'sm',
    'AP_LOW_SMTH': 'sm',
    'AP_UPR_SMTH': 'sm',
}

# Asset name fixes: BoatItemNo → Liquifire asset
# SF = Special Fishing package (not in Liquifire, strip suffix)
# SE = Special Edition (not in Liquifire, strip suffix)
# A = Arch (sometimes stripped for asset matching)
ASSET_FIXES = {
    # SF suffix removal + year-walk
    '20SFSF': '20SF',
    '20SLSF': '22SL',
    '22MFBSF': '24MFB',
    '22MSBSF': '23MSB',
    '22SSRSF': '22SSR',
    '23MSBSF': '23MSB',
    '23MSLSF': '24MSL',
    '23SSBSF': '22SSB',
    '23SSRSF': '22SSR',
    '24MSLSF': '24MSL',
    '25QSBWASF': '25QSBW',
    '25QXFBASF': '25QXFBW',
    '25QXFBWASF': '25QXFBW',
    '25QXSBWASF': '25QXSBW',
    '25RFBSF': '23RFB',
    '25RSRSF': '25RSR',
    # SE suffix variants (Special Edition, no separate Liquifire asset)
    '22MFBSE': '24MFB',
    '23RXSBSE': '23RFB',
    '27QXSBWAT2SE': '25QXSBW',
    # SFC series → S series (SFC = Sport Fishing Combo, no separate Liquifire asset)
    '188SFC':     '22SSR',
    '20SFC':      '22SSR',
    '21SFC':      '22SSR',
    '22SFC':      '22SSR',
    '22SFCSF':    '22SSR',
    '23SFC':      '22SSR',
    # SX series → S series (SX = upgraded S, no separate Liquifire asset)
    '20SXSSF':    '22SSR',
    '22SXSRSF':   '22SSR',
    '23SXSAPGSF': '22SSR',
    '23SXSBSF':   '22SSB',
    '24SXSRSF':   '22SSR',
    '25SXSRCSF':  '22SSR',
    # LT series → SL (closest hull shape, no separate Liquifire asset)
    '23LTSBASF': '22SL',
    '25LTSBSF':  '22SL',
    # R / RX series
    '23RSBA':    '23RFB',
    '23RSBASF':  '23RFB',
    '23RXFBASF': '23RFB',
    '23RXSBSF':  '23RFB',
    '25RSBWASF': '25RSR',
    # LXS series
    '26LXSSBASF': '25RSR',
    # Large / twin-engine QX → base QX asset (no separate Liquifire asset)
    '27QXFBWAT2SF': '25QXFBW',
    '27QXFBWAX2SF': '25QXFBW',
    '27RXSBWAT2SF': '25RSR',
    '28QXFBAX1SF':  '25QXFBW',
    '30QXFBWAX2SF': '25QXFBW',
    '30QXSBAX2SF':  '25QXSBW',
    '30QXSBWAX2SF': '25QXSBW',
    # MC variant → base M series (24MCSB has no Liquifire asset, use 23MSB)
    '24MCSB': '23MSB',
    # MOFB series → M series (Open Fastback, no separate Liquifire asset)
    '22MOFB': '23MSB',
    '23MOFB': '23MSB',
    '24MOFB': '23MSB',
    '26MOFB': '23MSB',
    # Arch suffix removal
    '25QSBA': '25QSB',
    # S1 series → S series mapping (S1 = upgraded S, not a separate Liquifire asset)
    '22S1SR': '23SSR',
    '22S1SB': '22SSB',
    '20S1SR': '22SSR',
    '23S1SR': '22SSR',
    '20S1L':  '22SL',
    # Legacy/old model naming
    '188SL':  '22SL',
    '188SLSF': '22SL',
}

# Series-level stock assets — used as last-resort fallback when no model-specific
# asset renders. These are known-good Liquifire assets for each series.
SERIES_STOCK_ASSET = {
    'S':   '22SSR',
    'S1':  '22SSR',
    'M':   '23MSB',
    'M1':  '23MSB',
    'Q':   '25QSB',
    'QX':  '25QXFBW',
    'R':   '25RSR',
    'RT':  '25RSR',
    'RX':  '25RSR',
    'LXS': '25LXSSB',
    'LT':  '22SL',
}


def normalize_asset(model):
    """
    Normalize BoatItemNo to Liquifire asset name.
    Returns (asset_name, was_fixed).
    """
    if not model:
        return model, False

    # Check explicit fixes first
    if model in ASSET_FIXES:
        return ASSET_FIXES[model], True

    # Strip SF/SE suffix if present (Special Fishing / Special Edition package)
    for suffix in ('SF', 'SE'):
        if model.endswith(suffix) and len(model) > 4:
            stripped = model[:-2]
            # Re-check ASSET_FIXES with the stripped name
            if stripped in ASSET_FIXES:
                return ASSET_FIXES[stripped], True
            return stripped, True

    return model, False


# ── URL builder ───────────────────────────────────────────────────────────────

def build_url(serial, config, model, series, matrices):
    """
    Build a Liquifire URL for a CPQ boat from its configuration.
    Returns the URL string, or None if required data is missing.
    If config is empty (no CPQ attributes), returns a minimal default URL.
    """
    if not model:
        return None

    # Normalize asset name (strip SF/SE suffix, apply known fixes)
    asset, _ = normalize_asset(model)

    # No CPQ config — return a minimal default URL (no color params)
    if not config:
        return f"{LIQUIFIRE_BASE}?set=cat[pon],asset[{asset}],view[side],tube[std]&call=url[file:PS/main]&sink"

    bv_key = config.get('baseVinyl', '').upper()
    fa_key = config.get('furnAccent', '').upper()
    fu_key = config.get('furnUpgrades', '').upper()
    panel_type_key = config.get('panelType', '').upper()
    panel_color_key = config.get('panelColor', '').upper()
    accent_type_key = config.get('accentPanelType', '').upper()
    accent_color_key = config.get('accentPanelColor', '').upper()
    bimini_key = config.get('biminiAft', '').upper()
    canvas_key = config.get('canvas', '').upper()
    anodizing = config.get('anodizing', '')
    arch_val = config.get('arch', '')

    bv = matrices['base_vinyl'].get(bv_key, {})
    fa = matrices['furn_accent'].get(fa_key, {})
    fu = matrices['furn_upgrades'].get(fu_key, {})
    bim = matrices['bimini_aft'].get(bimini_key, {})
    cv = matrices['canvas'].get(canvas_key, {})

    series_up = (series or '').upper()

    def panel_lp(q_code, a_code):
        key = f'{series_up}|{q_code.upper()}|{a_code.upper()}'
        row = matrices['panel_colors'].get(key) or matrices['panel_colors'].get(f'|{q_code.upper()}|{a_code.upper()}', {})
        return row

    # Furniture package asset
    furn_pkg = g(fu, 'LPAsset', default='furn_m_std')

    # Base vinyl (furniture prime color)
    furn_prime = g(bv, 'LPColor', default='d3d3d3')
    furn_prime_opc = g(bv, 'LPOpacity', default='73')

    # Roto
    if series_up == 'S':
        furn_roto = g(bv, 'LPRotoSSeries', default=g(bv, 'LPRoto', default=''))
        furn_roto_opc = g(bv, 'LPRotoSSeriesOpacity', default='73')
    else:
        furn_roto = g(bv, 'LPRoto', default='')
        furn_roto_opc = g(bv, 'LPRotoOpacity', default='80')

    # Furniture secondary accent (from base vinyl, series-dependent)
    if series_up == 'S':
        furn_sec_acc = g(bv, 'LPFurnSecondaryAccSSeries', default='')
        furn_sec_acc_opc = g(bv, 'LPFurnSecondaryAccSSeriesOpacity', default='80')
    elif fu_key == 'M_SPT':
        furn_sec_acc = g(bv, 'LPFurnSecondaryAccMSport', default=g(bv, 'LPFurnSecondaryAcc', default=''))
        furn_sec_acc_opc = g(bv, 'LPFurnSecondaryAccMSportOpacity', default=g(bv, 'LPFurnSecondaryAccOpacity', default='60'))
    else:
        furn_sec_acc = g(bv, 'LPFurnSecondaryAcc', default='')
        furn_sec_acc_opc = g(bv, 'LPFurnSecondaryAccOpacity', default='60')

    # Lumbar (series/upgrade-dependent)
    if fu_key == 'M_STD':
        furn_lum = g(bv, 'LPFurnLumMStd', default='')
        furn_lum_opc = g(bv, 'LPFurnLumMStdOpacity', default='100')
    elif fu_key == 'M_LUXE':
        furn_lum = g(bv, 'LPFurnLumMLuxe', default='')
        furn_lum_opc = g(bv, 'LPFurnLumMLuxeOpacity', default='100')
    elif fu_key == 'M_SPT':
        furn_lum = g(bv, 'LPFurnLumMSport', default='')
        furn_lum_opc = g(bv, 'LPFurnLumMSportOpacity', default='100')
    elif series_up == 'S':
        furn_lum = g(bv, 'LPFurnLumSSeries', default='')
        furn_lum_opc = g(bv, 'LPFurnLumSSeriesOpacity', default='80')
    else:
        furn_lum = g(fa, 'LPFurnLum', default='')
        furn_lum_opc = g(fa, 'LPFurnLumOpacity', default='')

    # Lumbar strip
    if 'MONO' in bv_key:
        furn_lum_strp = g(bv, 'LPFurnLumStrpMono', default='')
        furn_lum_strp_opc = g(bv, 'LPFurnLumStrpMonoOpacity', default='100')
    else:
        furn_lum_strp = g(bv, 'LPFurnLumStrp', default='')
        furn_lum_strp_opc = g(bv, 'LPFurnLumStrpOpacity', default='100')

    # Accent-driven furniture colors
    furn_accnt = g(fa, 'LPColor', default='')
    furn_accnt_opc = g(fa, 'LPOpacity', default='60')
    furn_seat_acc = g(fa, 'LPFurnSeatAcc', default='')
    furn_seat_acc_opc = g(fa, 'LPFurnSeatAccOpacity', default='60')
    furn_seat_pan = g(fa, 'LPFurnSeatPan', default='')
    furn_seat_pan_opc = g(fa, 'LPFurnSeatPanOpacity', default='60')
    furn_cup_hld = g(fa, 'LPFurnCupHld', default='')
    furn_cup_hld_opc = g(fa, 'LPFurnCupHldOpacity', default='60')
    furn_welt = g(fa, 'LPFurnWelt', default='')
    furn_welt_opc = g(fa, 'LPFurnWeltOpacity', default='60')
    furn_cro_stch = g(fa, 'LPFurnCroStch', default='')
    furn_mgram2 = g(fa, 'LPFurnMgram2', default='')

    # Top stitch (M series uses LPFurnTopStchMSeries)
    if series_up == 'M':
        furn_top_stch = g(bv, 'LPFurnTopStchMSeries', default=g(fa, 'LPFurnTopStch', default=''))
    elif series_up == 'S':
        furn_top_stch = g(bv, 'LPFurnTopStchSSeries', default=g(fa, 'LPFurnTopStch', default=''))
    else:
        furn_top_stch = g(fa, 'LPFurnTopStch', default='')

    # Lum stitch and monogram 1 (from base vinyl)
    furn_lum_stch = g(bv, 'LPFurnLumStch', default='')
    furn_mgram1 = g(bv, 'LPFurnMgram1', default='')

    # Panel colors
    pc_row = panel_lp(panel_type_key, panel_color_key)
    ppn_type = PANEL_TYPE_LP.get(panel_type_key, 'sm')
    ppn_color = g(pc_row, 'LPColor', default='')
    ppn_opc = g(pc_row, 'LPOpacity', default='60')

    # Accent panel colors
    ap_row = panel_lp(accent_type_key, accent_color_key) if accent_color_key not in ('NO_ACCENT', '') else {}
    ap_type = PANEL_TYPE_LP.get(accent_type_key, 'sm') if accent_color_key not in ('NO_ACCENT', '') else ''
    ap_color = g(ap_row, 'LPColor', default='') if accent_color_key not in ('NO_ACCENT', '') else ''
    ap_opc = g(ap_row, 'LPOpacity', default='80') if accent_color_key not in ('NO_ACCENT', '') else ''

    # Highlight (graph1)
    is_matte_satin = 'MATTE' in panel_color_key or 'SATIN' in panel_color_key
    highlight = '' if is_matte_satin else 'hlt'

    # Logo color
    logo_color = '0e0e0e' if anodizing == 'blackoutLuxe' else 'd8d9dc'

    # Bimini
    bim_asset = g(bim, 'LPAsset', default='cur')
    # Bimini secondary color — use accent color if available, else canvas
    bim_c2 = furn_accnt if furn_accnt else g(cv, 'LPColor', default='')

    # Arch
    arch_asset = ''  # default noArch
    arch_c2 = furn_accnt if furn_accnt else ''

    # Canvas (bimC1 not normally set, but canvas drives bimC2 for some configs)
    # Rail: windshield models use 'wds', others 'psg'
    # Check if 'W' appears in last 3 chars of model name (WA=Windshield+Arch, W, WL etc.)
    has_windshield = any(c == 'W' for c in model.upper()[-3:])
    rail = 'wds' if has_windshield else 'psg'

    # Tubes: standard single engine
    tubes = 'std'

    # Deck
    deck = 'trm'
    deck_opt = 'ins'

    params = (
        f"cat[pon],asset[{asset}],view[side],"
        f"tube[{tubes}],tubeC1[],tubeOPC1[],tubeC2[ffffff],tubeOPC2[120],"
        f"furnPrime[{furn_prime}],furnPrimeOPC[{furn_prime_opc}],"
        f"furnAccnt[{furn_accnt}],furnAccntOPC[{furn_accnt_opc}],"
        f"furnSecondaryAcc[{furn_sec_acc}],furnSecondaryAccOPC[{furn_sec_acc_opc}],"
        f"furnRoto[{furn_roto}],furnRotoOPC[{furn_roto_opc}],"
        f"furnSeatAcc[{furn_seat_acc}],furnSeatAccOPC[{furn_seat_acc_opc}],"
        f"furnSeatPan[{furn_seat_pan}],furnSeatPanOPC[{furn_seat_pan_opc}],"
        f"furnLum[{furn_lum}],furnLumOPC[{furn_lum_opc}],"
        f"furnLumStrp[{furn_lum_strp}],furnLumStrpOPC[{furn_lum_strp_opc}],"
        f"furnCupHld[{furn_cup_hld}],furnCupHldOPC[{furn_cup_hld_opc}],"
        f"furnWelt[{furn_welt}],furnWeltOPC[{furn_welt_opc}],"
        f"furnLumStch[{furn_lum_stch}],furnTopStch[{furn_top_stch}],"
        f"furnCroStch[{furn_cro_stch}],furnMgram1[{furn_mgram1}],furnMgram2[{furn_mgram2}],"
        f"arch[{arch_asset}],archC1[131315],archOPC1[60],archC2[{arch_c2}],archOPC2[60],"
        f"ppn[{ppn_type}],ppnC1[{ppn_color}],ppnOPC1[{ppn_opc}],"
        f"ap1[{ap_type}],ap1C1[{ap_color}],ap1OPC1[{ap_opc}],"
        f"ap2[],ap2C1[],ap2OPC1[],"
        f"graph1[{highlight}],graph1C1[],graph1OPC1[],"
        f"graph2[],graph2C1[],graph2OPC1[],"
        f"logo1[std],logo1C1[{logo_color}],"
        f"rail[{rail}],railC1[],railOPC1[],"
        f"deck[{deck}],deckC1[],deckOPC1[],"
        f"deckOpt1[{deck_opt}],deckOpt1C1[],deckOpt1OPC1[],"
        f"bim[{bim_asset}],bimC1[],bimOPC1[],bimC2[{bim_c2}],bimOPC2[60],"
        f"hdlght[std],seed[005]"
    )
    return f"{LIQUIFIRE_BASE}?set={params}&call=url[file:PS/main]&sink"


def test_url(url, retries=2, timeout=30):
    """Return (ok, size_bytes) for a Liquifire URL.
    Liquifire returns a small (~4KB) placeholder JPEG for invalid/unknown assets.
    A real boat render is typically >20KB.
    Retries on timeout/error to handle transient Liquifire slowness.
    """
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200 and 'image' in r.headers.get('Content-Type', ''):
                size = len(r.content)
                return size > 20_000, size
            return False, 0
        except Exception:
            if attempt == retries - 1:
                return False, 0


def build_and_test_url(serial, config, model, series, matrices, from_snm=False):
    """
    Build a Liquifire URL and verify it renders, with year-walk fallback.
    Returns (url, size_bytes, method) on success, or (None, 0, None) on failure.

    method values:
      colored        — full CPQ config, exact asset rendered
      snm-colored    — config built from SNM text fields, exact asset rendered
      year-walk      — CPQ config, asset year was walked to find a renderable version
      snm-year-walk  — SNM config + year walk
      stock-colored  — series stock hull rendered with colors
      stock-bare     — series stock hull, no colors (last resort)
    """
    url = build_url(serial, config, model, series, matrices)
    if not url:
        return None, 0, None

    normalized_asset, _ = normalize_asset(model)
    pfx = 'snm-' if from_snm else ''

    # No config at all — bare stock hull only
    if not config:
        stock = SERIES_STOCK_ASSET.get((series or '').upper())
        if stock:
            stock_url = f"{LIQUIFIRE_BASE}?set=cat[pon],asset[{stock}],view[side],tube[std]&call=url[file:PS/main]&sink"
            ok, size = test_url(stock_url)
            if ok:
                print(f'  {serial} ({model}): no CPQ config (BO25), using stock asset [{stock}]')
                return stock_url, size, 'stock-bare'
        return None, 0, None

    ok, size = test_url(url)

    # Year-walk: try ±1, ±2, ±3 years if the base asset doesn't render
    if not ok and len(normalized_asset) >= 2 and normalized_asset[:2].isdigit():
        year = int(normalized_asset[:2])
        model_suffix = normalized_asset[2:]
        for delta in [1, -1, 2, -2, 3, -3]:
            try_year = year + delta
            if try_year < 10:
                continue
            fallback_asset = f'{try_year:02d}{model_suffix}'
            fallback_url = url.replace(f'asset[{normalized_asset}]', f'asset[{fallback_asset}]')
            ok, size = test_url(fallback_url)
            if ok:
                print(f'  {serial} ({model}): using year-walk asset [{fallback_asset}]')
                return fallback_url, size, f'{pfx}year-walk'

    if ok:
        return url, size, f'{pfx}colored'

    # Last resort: series-level stock asset — substitute into the colored URL so we
    # at least render the right colors on a known-good hull shape.
    stock = SERIES_STOCK_ASSET.get((series or '').upper())
    if stock and url:
        colored_stock_url = url.replace(f'asset[{normalized_asset}]', f'asset[{stock}]')
        ok, size = test_url(colored_stock_url)
        if ok:
            print(f'  {serial} ({model}): using series stock asset [{stock}] with colors')
            return colored_stock_url, size, 'stock-colored'
    if stock:
        stock_url = f"{LIQUIFIRE_BASE}?set=cat[pon],asset[{stock}],view[side],tube[std]&call=url[file:PS/main]&sink"
        ok, size = test_url(stock_url)
        if ok:
            print(f'  {serial} ({model}): using series stock asset [{stock}] (bare fallback)')
            return stock_url, size, 'stock-bare'

    return None, 0, None


def get_snm_colors(cur, serial):
    """Return SNM plain-text color fields for a serial (used for BoatOptions25 boats)."""
    cur.execute("""
        SELECT BaseVinyl, PanelColor, AccentPanel
        FROM SerialNumberMaster
        WHERE Boat_SerialNo = %s
    """, (serial,))
    row = cur.fetchone()
    if not row:
        return {}
    return {
        'BaseVinyl':  row[0] or '',
        'PanelColor': row[1] or '',
        'AccentPanel': row[2] or '',
    }


def get_snm_config(cur, serial, matrices):
    """
    Build a CPQ config dict from SNM plain-text color fields.
    Returns (config, from_snm) — from_snm is True when SNM fields produced a config.
    """
    snm_colors = get_snm_colors(cur, serial)
    if not any(snm_colors.values()):
        return {}, False
    config = snm_to_config(snm_colors, matrices)
    return config, bool(config)


def store_url(conn, serial, url):
    cur = conn.cursor()
    cur.execute(
        "UPDATE SerialNumberMaster SET LiquifireImageUrl = %s WHERE Boat_SerialNo = %s",
        (url, serial)
    )
    conn.commit()
    return cur.rowcount


# ── Main ──────────────────────────────────────────────────────────────────────

def get_target_serials(cur, specific=None, rebuild_all=False):
    if specific:
        return specific
    if rebuild_all:
        cur.execute("""
            SELECT DISTINCT bo.BoatSerialNo
            FROM BoatOptions26 bo
            JOIN SerialNumberMaster snm ON snm.Boat_SerialNo = bo.BoatSerialNo
            WHERE bo.BoatModelNo IS NOT NULL AND bo.BoatModelNo != 'Base Boat'
            UNION
            SELECT DISTINCT bo.BoatSerialNo
            FROM BoatOptions25 bo
            JOIN SerialNumberMaster snm ON snm.Boat_SerialNo = bo.BoatSerialNo
            WHERE bo.BoatModelNo IS NOT NULL AND bo.BoatModelNo != ''
        """)
    else:
        cur.execute("""
            SELECT DISTINCT bo.BoatSerialNo
            FROM BoatOptions26 bo
            JOIN SerialNumberMaster snm ON snm.Boat_SerialNo = bo.BoatSerialNo
            WHERE bo.BoatModelNo IS NOT NULL AND bo.BoatModelNo != 'Base Boat'
              AND (snm.LiquifireImageUrl IS NULL OR snm.LiquifireImageUrl = '')
            UNION
            SELECT DISTINCT bo.BoatSerialNo
            FROM BoatOptions25 bo
            JOIN SerialNumberMaster snm ON snm.Boat_SerialNo = bo.BoatSerialNo
            WHERE bo.BoatModelNo IS NOT NULL AND bo.BoatModelNo != ''
              AND (snm.LiquifireImageUrl IS NULL OR snm.LiquifireImageUrl = '')
        """)
    return [r[0] for r in cur.fetchall()]


def main():
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    rebuild_all = '--all' in args
    specific = [a for a in args if not a.startswith('--')]

    token = get_trn_token()
    matrices = load_matrices(token)

    prod_conn = mysql.connector.connect(database='warrantyparts', **DB)
    test_conn = mysql.connector.connect(database='warrantyparts_test', **DB)
    prod_cur = prod_conn.cursor()

    serials = get_target_serials(prod_cur, specific or None, rebuild_all)
    print(f'\nProcessing {len(serials)} boat(s)...\n')

    results = {'ok': 0, 'failed': 0, 'skipped': 0}

    for serial in serials:
        config, model, series = get_boat_config(prod_cur, serial)

        if not model:
            print(f'  {serial}: SKIP — no model in BoatOptions26 or BoatOptions25')
            results['skipped'] += 1
            continue

        # BO25 boats have no CfgName/CfgValue — try to build config from SNM color text fields
        from_snm = False
        if not config:
            config, from_snm = get_snm_config(prod_cur, serial, matrices)
            if from_snm:
                print(f'  {serial}: built config from SNM colors ({len(config)} keys)')

        # Log if asset was normalized
        _, was_fixed = normalize_asset(model)
        if was_fixed:
            normalized_asset, _ = normalize_asset(model)
            print(f'  {serial}: asset normalized {model} → {normalized_asset}')

        url, size, method = build_and_test_url(serial, config, model, series, matrices, from_snm=from_snm)

        if not url:
            print(f'  {serial} ({model}): FAIL — URL did not render')
            results['failed'] += 1
            continue

        if dry_run:
            print(f'  {serial} ({model}): OK [{method}] ({size:,} bytes) [dry-run, not stored]')
        else:
            n_prod = store_url(prod_conn, serial, url)
            n_test = store_url(test_conn, serial, url)
            print(f'  {serial} ({model}): OK [{method}] ({size:,} bytes) — stored prod={n_prod} test={n_test}')

        results['ok'] += 1

    prod_conn.close()
    test_conn.close()
    print(f'\nDone. ok={results["ok"]} failed={results["failed"]} skipped={results["skipped"]}')


if __name__ == '__main__':
    main()
