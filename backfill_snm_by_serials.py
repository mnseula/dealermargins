#!/usr/bin/env python3
"""
Backfill SerialNumberMaster + SerialNumberRegistrationStatus for boats that
were missed by the nightly JAMS run (e.g. because the pipeline crashed after
BoatOptions loaded but before the SNM step ran).

Usage:
    python3 backfill_snm_by_serials.py --auto          # detect boats with blank DealerName (last 7 days)
    python3 backfill_snm_by_serials.py --auto --days 3 # same but only last 3 days
    python3 backfill_snm_by_serials.py ETWS2179C626 ETWS2222C626 ...  # explicit HINs

All field logic mirrors import_daily_boats.py exactly — no shortcuts.
"""

import sys
import os
import csv
import tempfile

import pymssql
import mysql.connector

# ── Import shared functions from the main pipeline ──────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import import_daily_boats as idb

# ── Boats missed on 2026-04-09 ───────────────────────────────────────────────
DEFAULT_SERIALS = [
    'ETWC7261C626', 'ETWC7306C626', 'ETWS1944C626', 'ETWS2179C626',
    'ETWS2222C626', 'ETWS2243C626', 'ETWS2247C626', 'ETWS2253C626',
    'ETWS2271C626', 'ETWS2308C626', 'ETWS2324C626', 'ETWS2344C626',
    'ETWS2345C626', 'ETWS2457C626', 'ETWS2459C626', 'ETWS2463C626',
    'ETWS2464C626', 'ETWS2504D626', 'ETWS2516D626', 'ETWS2518D626',
    'ETWS2532D626', 'ETWS2533D626',
]


def build_query_by_serials(db: str, serials: list) -> str:
    """Same as build_serial_master_query but filters by HIN list instead of today's date."""
    placeholders = ', '.join(f"'{s}'" for s in serials)
    return f"""
    SELECT DISTINCT
        COALESCE(NULLIF(coi.Uf_BENN_BoatSerialNumber, ''), ser.ser_num) AS BoatSerialNo,
        coi.item                                AS BoatItemNo,
        coi.description                         AS BoatDesc1,
        im.Uf_BENN_Series                       AS Series,
        coi.co_num                              AS ERP_OrderNo,
        LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
        iim.inv_num                             AS InvoiceNo,
        LEFT(LTRIM(RTRIM(iim.inv_num)), 30)     AS ApplyToNo,
        LEFT(co.type, 1)                        AS OrigOrderType,
        CASE WHEN iim.tax_date IS NOT NULL
            THEN CONVERT(INT, CONVERT(VARCHAR(8), iim.tax_date, 112))
            ELSE NULL
        END                                     AS InvoiceDate,
        co.cust_num                             AS DealerNumber,
        cust.name                               AS DealerName,
        cust.city                               AS DealerCity,
        cust.state                              AS DealerState,
        cust.zip                                AS DealerZip,
        cust.country                            AS DealerCountry,
        coi.Uf_BENN_BoatModel                   AS BoatModelNo,
        co.order_date                           AS OrderDate,
        co.Uf_BENN_ProductionNumber             AS ProdNo,
        co.Uf_BENN_BenningtonOwned              AS BenningtonOwned,
        coi.Uf_BENN_PannelColor                 AS PanelColor,
        coi.Uf_BENN_BaseVnyl                    AS BaseVinyl,
        coi.Uf_BENN_PreSold                     AS Presold,
        coi.qty_invoiced                        AS Quantity,
        coi.config_id                           AS ConfigId,
        co.external_confirmation_ref            AS SoNumber,
        co.slsman                               AS SlsMan
    FROM [{db}].[dbo].[coitem_mst] coi
    LEFT JOIN [{db}].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND coi.co_release = ser.ref_release
        AND coi.item = ser.item
        AND coi.site_ref = ser.site_ref
        AND ser.ref_type = 'O'
    INNER JOIN [{db}].[dbo].[inv_item_mst] iim
        ON coi.co_num = iim.co_num
        AND coi.co_line = iim.co_line
        AND coi.co_release = iim.co_release
        AND coi.site_ref = iim.site_ref
    INNER JOIN [{db}].[dbo].[co_mst] co
        ON coi.co_num = co.co_num
        AND coi.site_ref = co.site_ref
    LEFT JOIN [{db}].[dbo].[item_mst] im
        ON coi.item = im.item
        AND coi.site_ref = im.site_ref
    LEFT JOIN [{db}].[dbo].[custaddr_mst] cust
        ON co.cust_num = cust.cust_num
        AND co.site_ref = cust.site_ref
        AND cust.cust_seq = 0
    WHERE coi.site_ref = 'BENN'
        AND im.Uf_BENN_MaterialCostType IN ('BOA', 'BOI')
        AND (
            co.external_confirmation_ref LIKE 'SO%'
            OR TRY_CAST(co.external_confirmation_ref AS BIGINT) IS NOT NULL
        )
        AND (
            (coi.Uf_BENN_BoatSerialNumber IS NOT NULL AND coi.Uf_BENN_BoatSerialNumber != '')
            OR ser.ser_num IS NOT NULL
        )
        AND iim.inv_num IS NOT NULL
        AND iim.inv_num NOT LIKE 'CR%'
        AND coi.qty_invoiced > 0
        AND co.co_num NOT LIKE 'WN%'
        AND co.co_num NOT LIKE 'WP%'
        AND co.co_num NOT LIKE 'WW%'
        AND COALESCE(NULLIF(coi.Uf_BENN_BoatSerialNumber, ''), ser.ser_num) IN ({placeholders})
    ORDER BY BoatSerialNo
    """


def log(msg, level="INFO"):
    from datetime import datetime
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {msg}")


def detect_incomplete_boats(days: int = 7) -> list:
    """
    Find boats in SNM that were inserted via the BoatOptions fallback —
    identified by blank DealerName and a recent createdate.
    These are the boats that need a full backfill from MSSQL.
    """
    conn = mysql.connector.connect(**idb.MYSQL_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT Boat_SerialNo
        FROM SerialNumberMaster
        WHERE (DealerName IS NULL OR DealerName = '')
          AND DATE(createdate) >= CURDATE() - INTERVAL %s DAY
        ORDER BY createdate DESC
    """, (days,))
    serials = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return serials


def main():
    args = sys.argv[1:]

    if '--auto' in args:
        days = 7
        if '--days' in args:
            idx = args.index('--days')
            try:
                days = int(args[idx + 1])
            except (IndexError, ValueError):
                pass
        log(f"Auto-detecting boats with blank DealerName in last {days} day(s)...")
        serials = detect_incomplete_boats(days)
        if not serials:
            log("No incomplete boats found — nothing to backfill.")
            sys.exit(0)
        log(f"Found {len(serials)} boat(s) to backfill: {serials}")
    elif args:
        serials = args
    else:
        serials = DEFAULT_SERIALS

    if not serials:
        print("No serials specified.")
        sys.exit(1)

    log(f"Backfilling {len(serials)} boats: {serials}")

    # ── 1. Pull data from MSSQL ───────────────────────────────────────────────
    log(f"Connecting to MSSQL ({idb.MSSQL_CONFIG['server']})...")
    mssql_conn = pymssql.connect(**idb.MSSQL_CONFIG)
    cursor = mssql_conn.cursor(as_dict=True)
    cursor.execute(build_query_by_serials(idb.MSSQL_DB, serials))
    raw_boats = cursor.fetchall()
    cursor.close()
    mssql_conn.close()
    log(f"Fetched {len(raw_boats)} boats from MSSQL", "SUCCESS")

    if not raw_boats:
        log("No boats returned from MSSQL — check serial numbers.", "WARNING")
        sys.exit(0)

    # ── 2. Fetch color attributes from CPQ config ─────────────────────────────
    config_ids = {b.get('ConfigId') for b in raw_boats if b.get('ConfigId')}
    color_attrs = idb.fetch_color_attrs(config_ids, idb.MSSQL_DB) if config_ids else {}
    log(f"Fetched color attrs for {len(color_attrs)} CPQ configs")

    # ── 3. Fetch color attributes from BoatOptions (fallback for legacy boats) ─
    mysql_conn_bo = mysql.connector.connect(**idb.MYSQL_CONFIG)
    boatoptions_colors = idb.fetch_color_attrs_from_boatoptions(serials, mysql_conn_bo)
    mysql_conn_bo.close()

    # ── 4. Load rep name maps ─────────────────────────────────────────────────
    rep_names, state_rep_map = idb.load_rep_names()
    log(f"Loaded {len(rep_names)} rep names, {len(state_rep_map)} state mappings")

    # ── 5. Fetch Liquifire image URLs from CPQ ────────────────────────────────
    # Use ERP_OrderNo (SO00936xxx from Syteline co_num) as CPQ ExternalId —
    # NOT SoNumber (external_confirmation_ref), which is a CPQ-generated ref like SONVU000005.
    so_numbers = [b.get('ERP_OrderNo') for b in raw_boats if str(b.get('ERP_OrderNo', '')).startswith('SO')]
    config_id_map = {b.get('ERP_OrderNo'): b.get('ConfigId') for b in raw_boats if b.get('ConfigId')}
    itemno_map    = {b.get('ERP_OrderNo'): b.get('BoatItemNo') for b in raw_boats if b.get('BoatItemNo')}
    cpq_image_urls = {}
    if so_numbers:
        try:
            cpq_image_urls = idb.fetch_cpq_image_urls(so_numbers, config_id_map, itemno_map)
            log(f"Fetched {len(cpq_image_urls)} Liquifire image URLs")
        except Exception as e:
            log(f"WARNING: Could not fetch Liquifire URLs ({e})", "WARNING")

    # ── 6. Build prepared dicts — identical logic to main pipeline ────────────
    prepared = []
    for boat in raw_boats:
        serial = boat.get('BoatSerialNo')
        if not serial:
            continue
        sn_my    = idb.get_model_year_2digit(serial)
        cfg      = color_attrs.get(boat.get('ConfigId'), {}) if boat.get('ConfigId') else {}
        bo_colors = boatoptions_colors.get(serial, {})

        panel_color   = (boat.get('PanelColor') or cfg.get('PanelColor_cfg') or bo_colors.get('PanelColor') or '').strip()
        accent_panel  = (cfg.get('AccentPanel') or bo_colors.get('AccentPanel') or '').strip()
        trim_accent   = (cfg.get('TrimAccent')  or bo_colors.get('TrimAccent')  or '').strip()
        color_package = (cfg.get('ColorPackage') or bo_colors.get('ColorPackage') or '').strip()

        fallback_image = 'https://s3.amazonaws.com/eosstatic/images/0/5880c9a7a9d29ae43164c78f/Generic-01.jpg'

        prepared.append({
            'SN_MY':           sn_my,
            'BoatSerialNo':    serial,
            'BoatItemNo':      (boat.get('BoatItemNo') or '').strip(),
            'Series':          (boat.get('Series') or '').strip(),
            'BoatDesc1':       (boat.get('BoatDesc1') or '').strip(),
            'SerialModelYear': idb.get_full_model_year(sn_my),
            'ERP_OrderNo':     (boat.get('ERP_OrderNo') or '').strip(),
            'InvoiceNo':       (boat.get('InvoiceNo') or '').strip(),
            'ApplyToNo':       (boat.get('ApplyToNo') or '').strip(),
            'OrigOrderType':   (boat.get('OrigOrderType') or 'O').strip(),
            'InvoiceDate':     boat.get('InvoiceDate') or '',
            'DealerNumber':    (boat.get('DealerNumber') or '').strip().lstrip('0'),
            'DealerName':      (boat.get('DealerName') or '').strip(),
            'DealerCity':      (boat.get('DealerCity') or '').strip(),
            'DealerState':     (boat.get('DealerState') or '').strip(),
            'DealerZip':       (boat.get('DealerZip') or '').strip(),
            'DealerCountry':   (boat.get('DealerCountry') or '').strip(),
            'WebOrderNo':      (boat.get('WebOrderNo') or '').strip(),
            'ProdNo':          str(boat.get('ProdNo') or '').strip(),
            'BenningtonOwned': 1 if boat.get('BenningtonOwned') in (1, True, 'Y', 'y', '1') else 0,
            'PanelColor':      panel_color,
            'AccentPanel':     accent_panel,
            'BaseVinyl':       (cfg.get('BaseVinyl') or boat.get('BaseVinyl') or bo_colors.get('BaseVinyl') or '').strip(),
            'ColorPackage':    color_package,
            'TrimAccent':      trim_accent,
            'ParentRepName':   (
                (rep_names.get(int(boat['SlsMan'])) if boat.get('SlsMan') not in (None, '', 0) else None)
                or state_rep_map.get((boat.get('DealerState') or '').strip().upper())
                or ''
            ),
            'Presold':         'Y' if boat.get('Presold') in (1, True, 'Y', 'y') else 'N',
            'Quantity':        int(boat.get('Quantity') or 1),
            'LiquifireImageUrl': cpq_image_urls.get(str(boat.get('ERP_OrderNo', '')), fallback_image),
            'SN_ID':           0,
        })

    log(f"Prepared {len(prepared)} boats for insert")

    # ── 7. Insert into MySQL ──────────────────────────────────────────────────
    mysql_conn = mysql.connector.connect(**idb.MYSQL_CONFIG, allow_local_infile=True)
    idb.ensure_snm_image_column(mysql_conn)

    snm_inserted, snm_skipped = idb.load_serial_master(prepared, mysql_conn)
    reg_inserted, reg_skipped = idb.load_registration_status(prepared, mysql_conn)
    snm_reconciled = idb.reconcile_snm_invoices(prepared, mysql_conn)

    # Apply Liquifire image URLs
    boats_with_image = [b for b in prepared if b.get('LiquifireImageUrl')]
    if boats_with_image:
        cursor = mysql_conn.cursor()
        for boat in boats_with_image:
            cursor.execute(
                "UPDATE SerialNumberMaster SET LiquifireImageUrl = %s WHERE Boat_SerialNo = %s",
                (boat['LiquifireImageUrl'], boat['BoatSerialNo'])
            )
        mysql_conn.commit()
        cursor.close()
        log(f"Image URLs applied for {len(boats_with_image)} boat(s)", "SUCCESS")

    mysql_conn.close()

    log("=" * 60)
    log(f"BACKFILL COMPLETE")
    log(f"  SerialNumberMaster:            {snm_inserted} inserted, {snm_skipped} already existed")
    log(f"  SerialNumberRegistrationStatus:{reg_inserted} inserted, {reg_skipped} already existed")
    if snm_reconciled:
        log(f"  Invoice reconciliation:        {snm_reconciled} corrected", "WARNING")
    log("=" * 60)


if __name__ == '__main__':
    main()
