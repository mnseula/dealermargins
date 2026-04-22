"""
snm_color_map.py

Maps SerialNumberMaster plain-text color fields to CPQ config keys
suitable for build_url() in build_liquifire_url.py.

Used for 2025 MY boats (BoatOptions25) which have no CfgName/CfgValue
config attributes — only the human-readable descriptions stored in SNM.

SNM fields mapped:
  BaseVinyl   → baseVinyl  (CPQ Item key)
  PanelColor  → panelType + panelColor
  AccentPanel → accentPanelType + accentPanelColor

SNM fields NOT mapped (not available in a form we can reverse-map):
  TrimAccent  → decorative wood trim identifier, not a Liquifire color param
  ColorPackage → usually empty for BO25 boats
"""

# Strip these prefixes (longest first) before description lookup
VINYL_PREFIXES  = ['VINYL BASE VENETO ', 'BASE VINYL ', 'VINYL BASE ']
PANEL_PREFIXES  = ['PANEL COLOR ']
ACCENT_PREFIXES = ['PANEL ACCENT ', 'ACC PNL ']

# SNM varchar(30) field causes description truncation.
# Full suffixes tried first, then truncated variants.
SMOOTH_SUFFIXES = [' SMOOTH', ' SMTH', ' SMOOT', ' SMO', ' SM']


def _strip_prefix(text, prefixes):
    t = text.upper().strip()
    for p in prefixes:
        if t.startswith(p):
            return t[len(p):].strip()
    return t


def _strip_smooth(text):
    """
    Strip smooth/finish suffix. Returns (text_without_suffix, is_smooth).
    Handles truncated 'SMOOTH' at a 30-char field boundary:
      'METALLIC SILVER S'  → ('METALLIC SILVER', True)
      'METALLIC WHITE SM'  → ('METALLIC WHITE',  True)
      'MATTE BLACK SMOOT'  → ('MATTE BLACK',     True)
    """
    for sfx in SMOOTH_SUFFIXES:
        if text.endswith(sfx):
            return text[:-len(sfx)].strip(), True
    # Single trailing ' S' — only treat as smooth when remaining text is
    # substantial (>=7 chars), avoiding false matches on short colour names.
    if text.endswith(' S') and len(text) >= 10:
        return text[:-2].strip(), True
    return text, False


def _normalize(text):
    """Expand common SNM abbreviations before matching."""
    t = text.upper().strip()
    # 'MET ' is used in SNM as shorthand for 'METALLIC '
    if t.startswith('MET ') and not t.startswith('METT'):
        t = 'METALLIC ' + t[4:]
    return t


def _build_vinyl_rev(matrices):
    """Build description.upper() → CPQ Item key for the BaseVinyl matrix."""
    rev = {}
    for item_key, row in matrices['base_vinyl'].items():
        if item_key == 'DEFAULT_VALUE':
            continue
        desc = row.get('Description', '').upper().strip()
        if not desc:
            continue
        rev[desc] = item_key
        # Index without trailing material/finish words so partial SNM text still matches:
        #   'GRAPHITE SIMTEX' → also index 'GRAPHITE'
        #   'SHADOW GREY VENETO' → also index 'SHADOW GREY'
        for sfx in (' SIMTEX', ' VENETO', ' MONOTONE'):
            if desc.endswith(sfx):
                rev[desc[:-len(sfx)].strip()] = item_key
    return rev


def _build_panel_rev(matrices):
    """Build normalized description → AnswerCode for panel/accent colours."""
    rev = {}
    for row in matrices['panel_colors'].values():
        desc = row.get('Description', '').upper().strip()
        ac   = row.get('AnswerCode', '')
        if not desc or not ac:
            continue
        rev[desc] = ac
        # Also index without leading qualifier so 'METALLIC SILVER' → 'SILVER'
        # and 'MATTE BLACK' → 'BLACK' etc. as fallbacks
        for prefix in ('METALLIC ', 'MATTE '):
            if desc.startswith(prefix):
                rev[desc[len(prefix):].strip()] = ac
    return rev


def _best_match(query, lookup):
    """
    Find the best key in lookup for query string.
    Priority:
      1. Exact match
      2. Lookup description starts with query  (query is a truncated desc)
      3. Query starts with lookup description  (desc is shorter than query)
    Minimum 8 chars required for prefix matching to avoid false positives.
    """
    if not query:
        return None
    if query in lookup:
        return lookup[query]
    # Query might be truncated — find a desc that begins the same way
    for desc, key in lookup.items():
        if len(query) >= 8 and desc.startswith(query):
            return key
    # Desc might be shorter than query (extra words in SNM)
    for desc, key in lookup.items():
        if len(desc) >= 8 and query.startswith(desc):
            return key
    return None


def snm_to_config(snm_colors, matrices):
    """
    Convert SerialNumberMaster color text fields to a CPQ config dict.

    Parameters
    ----------
    snm_colors : dict
        Keys: BaseVinyl, PanelColor, AccentPanel  (strings, may be empty)
    matrices : dict
        The matrices dict returned by load_matrices() in build_liquifire_url.py

    Returns
    -------
    dict
        CPQ config keys: baseVinyl, panelType, panelColor,
                         accentPanelType, accentPanelColor
        Empty dict if nothing could be mapped.
    """
    config = {}
    vinyl_rev = _build_vinyl_rev(matrices)
    panel_rev = _build_panel_rev(matrices)

    # ── BaseVinyl ─────────────────────────────────────────────────────────────
    bv_raw = snm_colors.get('BaseVinyl', '').upper().strip()
    if bv_raw:
        bv_text = _strip_prefix(bv_raw, VINYL_PREFIXES)
        bv_key  = _best_match(bv_text, vinyl_rev)
        if bv_key:
            config['baseVinyl'] = bv_key

    # ── PanelColor ────────────────────────────────────────────────────────────
    pc_raw = snm_colors.get('PanelColor', '').upper().strip()
    if pc_raw:
        pc_text = _strip_prefix(pc_raw, PANEL_PREFIXES)
        pc_text, is_smooth = _strip_smooth(pc_text)
        pc_text = _normalize(pc_text)
        config['panelType'] = 'PP_SMTH' if is_smooth else 'PP_TEXT'
        ac = _best_match(pc_text, panel_rev)
        if ac:
            config['panelColor'] = ac

    # ── AccentPanel ───────────────────────────────────────────────────────────
    ap_raw = snm_colors.get('AccentPanel', '').upper().strip()
    if ap_raw:
        ap_text = _strip_prefix(ap_raw, ACCENT_PREFIXES)
        ap_text, is_smooth = _strip_smooth(ap_text)
        ap_text = _normalize(ap_text)
        if 'NO ACCENT' in ap_text or ap_text == 'NO_ACCENT':
            config['accentPanelColor'] = 'NO_ACCENT'
            config['accentPanelType']  = 'AP_SNG_SMTH' if is_smooth else 'AP_SNG_TEXT'
        else:
            config['accentPanelType'] = 'AP_SNG_SMTH' if is_smooth else 'AP_SNG_TEXT'
            ac = _best_match(ap_text, panel_rev)
            if ac:
                config['accentPanelColor'] = ac

    return config
