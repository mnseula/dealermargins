#!/usr/bin/env python3
"""
Sync OE# (ERP Order Numbers) between MySQL PartsOrderLines and Syteline.

This script replaces the CSV/PHP pipeline with direct MSSQL queries and XML generation.

Flow:
1. Find PartsOrderLines with missing ERP_OrderNo
2. Query Syteline (CSIPRD) to check if order exists
3. If found → update MySQL with OE# directly
4. If not found → generate XML → write to network share → wait → requery → update MySQL

Usage:
    python3 sync_oe_parts.py                    # run sync
    python3 sync_oe_parts.py --dry-run          # SELECT only, no writes
    python3 sync_oe_parts.py --order WP0524059  # process single order
"""

import sys
# import os
import logging
# import uuid
from datetime import datetime
# from decimal import Decimal
# import xml.etree.ElementTree as ET
# from xml.dom import minidom

import mysql.connector

try:
    import pymssql
except ImportError:
    print("ERROR: pymssql required. Install with: pip install pymssql")
    sys.exit(1)

DRY_RUN = False
SINGLE_ORDER = None


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sync_oe_parts.log', encoding='utf-8'),
    ]
)
log = logging.getLogger(__name__)

MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts',
    'autocommit': False,
}

MSSQL_CONFIG = {
    'server': 'MPL1ITSSQL086.POLARISIND.COM',
    'database': 'CSIPRD',
    'user': 'svcSpecs01',
    'password': 'SD4nzr0CJ5oj38',
    'timeout': 300,
    'login_timeout': 60
}

XML_OUTPUT_DIR = r'\\Elk1itsqvp001\Qlikview\SytelineProd'

def get_mysql_conn():
    return mysql.connector.connect(**MYSQL_CONFIG)

def get_mssql_conn():
    return pymssql.connect(
        server=MSSQL_CONFIG['server'],
        database=MSSQL_CONFIG['database'],
        user=MSSQL_CONFIG['user'],
        password=MSSQL_CONFIG['password'],
        timeout=MSSQL_CONFIG['timeout'],
        login_timeout=MSSQL_CONFIG['login_timeout']
    )

def execute_write(cursor, sql, params=None):
    keyword = sql.strip().split()[0].upper()
    if keyword in ('DELETE', 'TRUNCATE'):
        raise RuntimeError(f'DELETE/TRUNCATE not permitted: {sql.strip()[:80]}')
    if DRY_RUN:
        preview = (sql.split('\n')[0].strip())[:120]
        log.info(f'[DRY-RUN] would execute: {preview} | params={params}')
        return
    if params:
        cursor.execute(sql, params)
    else:
        cursor.execute(sql)

def commit(conn):
    if DRY_RUN:
        log.info('[DRY-RUN] would commit')
        return
    conn.commit()

def check_order_in_syteline(mssql_cursor, web_order_no, line_no):
    sql = """
        SELECT TOP 1
            coitem_mst.co_num AS ERP_OrderNo,
            coitem_mst.Uf_BENN_PartsWebOrderNumber AS WebOrderNumber
        FROM [CSIPRD].[dbo].[coitem_mst]
        WHERE
            (LEFT(co_num, 2) LIKE 'WP' OR LEFT(co_num, 2) LIKE 'WN')
            AND coitem_mst.Uf_BENN_PartsWebOrderNumber IS NOT NULL
            AND site_ref = 'BENN'
            AND coitem_mst.Uf_BENN_PartsWebOrderNumber LIKE %s
    """
    search_pattern = f'PO{web_order_no}-{line_no}'
    mssql_cursor.execute(sql, (search_pattern,))
    result = mssql_cursor.fetchone()
    if result:
        return result['ERP_OrderNo']
    return None

def check_order_in_syteline_by_partsorder(mssql_cursor, parts_order_id):
    sql = """
        SELECT TOP 1
            coitem_mst.co_num AS ERP_OrderNo
        FROM [CSIPRD].[dbo].[coitem_mst]
        WHERE
            (LEFT(co_num, 2) LIKE 'WP' OR LEFT(co_num, 2) LIKE 'WN')
            AND coitem_mst.Uf_BENN_PartsWebOrderNumber LIKE %s
            AND site_ref = 'BENN'
    """
    search_pattern = f'%{parts_order_id}-%'
    mssql_cursor.execute(sql, (search_pattern,))
    result = mssql_cursor.fetchone()
    if result:
        return [{'ERP_OrderNo': result['ERP_OrderNo']}]
    return []

def get_parts_order_data(mysql_cursor, parts_order_id):
    cursor = mysql_cursor
    
    cursor.execute("""
        SELECT 
            h.PartsOrderID,
            h.OrdHdrDealerNo,
            h.OrdHdrDealerRefNo,
            h.OrdHdrBoatSerialNo,
            h.OrdHdrSpecInstructions,
            h.OrdHdrDealerComments,
            h.OrdHdrClaimType,
            h.HdrCreateDate,
            h.OrdHdrShipMethID,
            l.OrdLineNo,
            l.OrdLinePartNo,
            l.OrdLinePartDesc,
            l.Qty_Ordered,
            l.DealerPrice,
            l.OrdLineEstShipDate,
            l.OrdLineID,
            l.ShipmentID
        FROM warrantyparts.PartsOrderHeader h
        JOIN warrantyparts.PartsOrderLines l ON h.PartsOrderID = l.PartsOrderID
        WHERE h.PartsOrderID = %s
        ORDER BY l.OrdLineNo
    """, (parts_order_id,))
    
    lines = []
    header = None
    for row in cursor.fetchall():
        if header is None:
            header = {
                'PartsOrderID': row['PartsOrderID'],
                'OrdHdrDealerNo': row['OrdHdrDealerNo'],
                'OrdHdrDealerRefNo': row['OrdHdrDealerRefNo'],
                'OrdHdrBoatSerialNo': row['OrdHdrBoatSerialNo'],
                'OrdHdrSpecInstructions': row['OrdHdrSpecInstructions'],
                'OrdHdrDealerComments': row['OrdHdrDealerComments'],
                'OrdHdrClaimType': row['OrdHdrClaimType'],
                'HdrCreateDate': row['HdrCreateDate'],
                'OrdHdrShipMethID': row['OrdHdrShipMethID'],
            }
        lines.append({
            'OrdLineNo': row['OrdLineNo'],
            'OrdLinePartNo': row['OrdLinePartNo'],
            'OrdLinePartDesc': row['OrdLinePartDesc'],
            'Qty_Ordered': row['Qty_Ordered'],
            'DealerPrice': row['DealerPrice'],
            'OrdLineEstShipDate': row['OrdLineEstShipDate'],
            'OrdLineID': row['OrdLineID'],
            'ShipmentID': row['ShipmentID'],
        })
    
    return header, lines

# ── XML generation functions (disabled) ──────────────────────────────────────
# Uncomment when XML submission to Syteline is ready to re-enable.
#
# def get_boat_info(mysql_cursor, boat_serial_no):
#     if not boat_serial_no or boat_serial_no == 'StockParts':
#         return None
#     cursor = mysql_cursor
#     cursor.execute("""
#         SELECT BoatItemNo, PanelColor
#         FROM warrantyparts.SerialNumberMaster
#         WHERE Boat_SerialNo = %s
#         LIMIT 1
#     """, (boat_serial_no,))
#     row = cursor.fetchone()
#     if row:
#         return {'BoatModel': row['BoatItemNo'], 'PanelColor': row['PanelColor']}
#     return None
#
# def get_dealer_info(mysql_cursor, dealer_no):
#     cursor = mysql_cursor
#     cursor.execute("""
#         SELECT Default_Terms_Code
#         FROM Eos.dealers
#         WHERE DlrNo = %s
#         LIMIT 1
#     """, (dealer_no,))
#     row = cursor.fetchone()
#     if row:
#         return {'TermsCode': row['Default_Terms_Code']}
#     return {'TermsCode': 'NK'}
#
# def escape_xml(text):
#     if text is None:
#         return ''
#     text = str(text)
#     text = text.replace('&', '&amp;')
#     text = text.replace('<', '&lt;')
#     text = text.replace('>', '&gt;')
#     text = text.replace('"', '&quot;')
#     text = text.replace("'", '&apos;')
#     return text

# def generate_xml(header, lines, boat_info, dealer_info):
#     parts_order_id = header['PartsOrderID']
#     claim_type = header.get('OrdHdrClaimType', 'parts_order')
#     if claim_type == 'parts_order':
#         order_type = 'CHARGE PARTS'
#         order_prefix = 'WP'
#     else:
#         order_type = 'NO CHARGE PARTS'
#         order_prefix = 'WN'
#     shipment_id = lines[0].get('ShipmentID', 'S1') if lines else 'S1'
#     shipment_suffix = shipment_id.split('-')[-1] if '-' in shipment_id else 'S1'
#     alternate_doc_id = f"{order_prefix}{parts_order_id}-{shipment_suffix}"
#     dealer_no = header.get('OrdHdrDealerNo', '')
#     if dealer_no and '~' not in dealer_no:
#         dealer_no = f"{dealer_no}~0"
#     ship_method = header.get('OrdHdrShipMethID', 'UPS')
#     terms_code = dealer_info.get('TermsCode', 'NK')
#     boat_model = boat_info.get('BoatModel', '') if boat_info else ''
#     panel_color = boat_info.get('PanelColor', '') if boat_info else ''
#     boat_serial = header.get('OrdHdrBoatSerialNo', 'StockParts')
#     if not boat_model:
#         boat_model = 'undefined'
#     order_date = header.get('HdrCreateDate', '')
#     if order_date:
#         try:
#             if isinstance(order_date, datetime):
#                 order_date = order_date.strftime('%m/%d/%Y')
#             elif isinstance(order_date, str) and '/' not in order_date:
#                 order_date = datetime.now().strftime('%m/%d/%Y')
#         except:
#             order_date = datetime.now().strftime('%m/%d/%Y')
#     else:
#         order_date = datetime.now().strftime('%m/%d/%Y')
#     dealer_ref = header.get('OrdHdrDealerRefNo', '') or ''
#     if '#' in dealer_ref:
#         dealer_ref = dealer_ref.split('#')[-1].strip()
#     xml_lines = []
#     xml_lines.append("<ProcessTest_Verenia_Boat xmlns='http://schema.infor.com/InforOAGIS/2' xmlns:xs='http://www.w3.org/2001/XMLSchema'>")
#     xml_lines.append("    <ApplicationArea>")
#     xml_lines.append("        <Sender>")
#     xml_lines.append("            <LogicalID>infor.file.test_verenia_boat_sftp</LogicalID>")
#     xml_lines.append("            <ComponentID>External</ComponentID>")
#     xml_lines.append("            <ConfirmationCode>OnError</ConfirmationCode>")
#     xml_lines.append("        </Sender>")
#     xml_lines.append("        <CreationDateTime>2023-09-07T16:34:51.379Z</CreationDateTime>")
#     xml_lines.append(f"        <BODID>infor.file.test_verenia_boat_sftp:{int(datetime.now().timestamp())}:{uuid.uuid4()}</BODID>")
#     xml_lines.append("    </ApplicationArea>")
#     xml_lines.append("    <DataArea>")
#     xml_lines.append("        <Process>")
#     xml_lines.append("            <AccountingEntityID xmlns=\"\"/>")
#     xml_lines.append("            <LocationID xmlns=\"\"/>")
#     xml_lines.append("            <ActionCriteria>")
#     xml_lines.append("                <ActionExpression actionCode='Add'/>")
#     xml_lines.append("            </ActionCriteria>")
#     xml_lines.append("        </Process>")
#     xml_lines.append("        <Test_Verenia_Boat>")
#     xml_lines.append("            <Test_Verenia_BoatHeader>")
#     xml_lines.append(f"                <AlternateDocumentID><ID>{escape_xml(alternate_doc_id)}</ID></AlternateDocumentID>")
#     xml_lines.append(f"                <ShipToParty><PartyIDs><ID>{escape_xml(dealer_no)}</ID></PartyIDs></ShipToParty>")
#     xml_lines.append(f"                <CarrierParty><PartyIDs><ID>{escape_xml(ship_method)}</ID></PartyIDs></CarrierParty>")
#     xml_lines.append(f"                <PaymentTerm><Term><ID>{escape_xml(terms_code)}</ID></Term></PaymentTerm>")
#     xml_lines.append(f"                <PurchaseOrderReference><DocumentID><ID>{escape_xml(dealer_ref)}</ID></DocumentID></PurchaseOrderReference>")
#     xml_lines.append(f"                <OrderDateTime>{escape_xml(order_date)}</OrderDateTime>")
#     xml_lines.append(f"                <ue_BennOrderType>{order_type}</ue_BennOrderType>")
#     xml_lines.append(f"                <ue_EngineForBoat/><ue_PreSold/><ue_ShowBoat/><ue_RentalBoat/>")
#     xml_lines.append(f"                <PanelColor>{escape_xml(panel_color)}</PanelColor>")
#     xml_lines.append(f"                <BaseVinyl/><BuildComments/><DealerComments/>")
#     xml_lines.append(f"                <BoatModel>{escape_xml(boat_model)}</BoatModel>")
#     xml_lines.append(f"                <BoatSerialNo>{escape_xml(boat_serial)}</BoatSerialNo>")
#     xml_lines.append(f"                <ShippingMethod>{escape_xml(ship_method)}</ShippingMethod>")
#     xml_lines.append(f"                <BennTermsCode>{escape_xml(terms_code)}</BennTermsCode>")
#     xml_lines.append(f"                <ue_International>0</ue_International><ue_InternationalType></ue_InternationalType>")
#     xml_lines.append(f"                <ue_SpecialInstructions>{escape_xml(header.get('OrdHdrSpecInstructions', ''))}</ue_SpecialInstructions>")
#     xml_lines.append(f"                <ue_Reason></ue_Reason><ue_LoadNumber/><ue_BennOwned></ue_BennOwned><ue_CustTrackingEmail></ue_CustTrackingEmail>")
#     xml_lines.append(f"            </Test_Verenia_BoatHeader>")
#     for i, line in enumerate(lines):
#         last_record = 1 if i == len(lines) - 1 else 0
#         line_no = line.get('OrdLineNo', i + 1)
#         item_no = line.get('OrdLinePartNo', '')
#         item_desc = line.get('OrdLinePartDesc', '')
#         qty = int(line.get('Qty_Ordered', '1') or 1)
#         unit_price = 0.0 if claim_type != 'parts_order' else float(str(line.get('DealerPrice', '0') or '0').replace('$','') or 0)
#         est_ship_date = line.get('OrdLineEstShipDate', '')
#         if isinstance(est_ship_date, datetime):
#             est_ship_date = est_ship_date.strftime('%Y-%m-%d')
#         parts_web_order_no = f"{order_prefix}{parts_order_id}-{str(line_no).zfill(2)}"
#         xml_lines.append(f"            <Test_Verenia_BoatLine>")
#         xml_lines.append(f"                <Item><ItemID><ID>{escape_xml(item_no)}</ID></ItemID></Item>")
#         xml_lines.append(f"                <Quantity unitCode=\"EA\">{qty}</Quantity>")
#         xml_lines.append(f"                <WarrantyClaimNo/><WarrantyClaimLineID/>")
#         xml_lines.append(f"                <UnitPrice>{unit_price:.2f}</UnitPrice>")
#         xml_lines.append(f"                <ShippingInstructions/>")
#         xml_lines.append(f"                <PartsWebOrderNo>{escape_xml(parts_web_order_no)}</PartsWebOrderNo>")
#         xml_lines.append(f"                <ue_LastRecord>{last_record}</ue_LastRecord>")
#         xml_lines.append(f"                <ue_Dealer_Comments/><ue_Details_Sublet_Comments/>")
#         xml_lines.append(f"                <ue_Item_Desc>{escape_xml(item_desc)}</ue_Item_Desc>")
#         xml_lines.append(f"                <ue_RGA>0</ue_RGA><ue_RGA_Date></ue_RGA_Date>")
#         xml_lines.append(f"                <ue_Estimated_Shipping_Date>{escape_xml(est_ship_date)}</ue_Estimated_Shipping_Date>")
#         xml_lines.append(f"                <ue_TransactionId>{escape_xml(parts_web_order_no)}</ue_TransactionId>")
#         xml_lines.append(f"                <ue_Alternate_Shipping_Location></ue_Alternate_Shipping_Location>")
#         xml_lines.append(f"            </Test_Verenia_BoatLine>")
#     xml_lines.append("        </Test_Verenia_Boat>")
#     xml_lines.append("    </DataArea>")
#     xml_lines.append("</ProcessTest_Verenia_Boat>")
#     return '\n'.join(xml_lines)

# def write_xml_file(xml_content, parts_order_id, order_prefix):
#     timestamp = datetime.now().strftime('%Y-%m-%d')
#     filename = f"sytelineExport_{timestamp}_{order_prefix}{parts_order_id}.xml"
#     if DRY_RUN:
#         log.info(f'[DRY-RUN] would write XML file: {filename}')
#         return filename
#     output_path = os.path.join(XML_OUTPUT_DIR, filename)
#     try:
#         with open(output_path, 'w', encoding='utf-8') as f:
#             f.write(xml_content)
#         log.info(f'XML written to: {output_path}')
#         return filename
#     except Exception as e:
#         local_path = os.path.join(os.getcwd(), filename)
#         with open(local_path, 'w', encoding='utf-8') as f:
#             f.write(xml_content)
#         log.warning(f'Could not write to network share ({e}). Written locally: {local_path}')
#         return local_path

def update_erp_order_no(mysql_cursor, parts_order_id, erp_order_no):
    execute_write(mysql_cursor, """
        UPDATE warrantyparts.PartsOrderLines
        SET ERP_OrderNo = %s
        WHERE PartsOrderID = %s
    """, (erp_order_no, parts_order_id))
    return mysql_cursor.rowcount

def sync_oe_parts():
    """
    Two-phase processing:

    Phase 1 — check Syteline for every order missing an ERP_OrderNo.
        If the EO# is already there, update MySQL immediately and move on.

    Phase 2 — for any orders still missing after Phase 1, push the XML to
        the network share and log it. No waiting, no polling — the user is
        responsible for the order going through in Syteline.
    """
    log.info('=' * 60)
    log.info('SYNC OE PARTS: Starting')
    log.info(f'DRY_RUN: {DRY_RUN}')
    if SINGLE_ORDER:
        log.info(f'SINGLE_ORDER: {SINGLE_ORDER}')
    log.info('=' * 60)

    try:
        mysql_conn = get_mysql_conn()
        mysql_cursor = mysql_conn.cursor(dictionary=True)

        try:
            mssql_conn = get_mssql_conn()
            mssql_cursor = mssql_conn.cursor(as_dict=True)
            mssql_available = True
        except Exception as e:
            log.warning(f'MSSQL connection failed: {e}. Cannot process orders.')
            mssql_available = False
            mssql_cursor = None

        if SINGLE_ORDER:
            mysql_cursor.execute("""
                SELECT DISTINCT PartsOrderID
                FROM warrantyparts.PartsOrderLines
                WHERE PartsOrderID = %s
                  AND (ERP_OrderNo IS NULL OR ERP_OrderNo = '')
            """, (SINGLE_ORDER,))
        else:
            mysql_cursor.execute("""
                SELECT DISTINCT PartsOrderID
                FROM warrantyparts.PartsOrderLines
                WHERE OrdLineStatus = 'Exported'
                  AND (ERP_OrderNo IS NULL OR ERP_OrderNo = '')
                ORDER BY PartsOrderID DESC
            """)

        missing_orders = mysql_cursor.fetchall()
        log.info(f'Found {len(missing_orders)} orders with missing ERP_OrderNo')

        stats = {
            'total':             len(missing_orders),
            'found_in_syteline': 0,
            'xml_submitted':     0,
            'errors':            0,
            'skipped':           0,
        }

        if not missing_orders:
            log.info('Nothing to do.')
            if mssql_cursor:
                mssql_cursor.close()
            mysql_cursor.close()
            mysql_conn.close()
            return

        if not mssql_available:
            log.error('MSSQL unavailable — cannot check Syteline.')
            stats['errors'] = len(missing_orders)
            return

        # ── PHASE 1: check Syteline, update MySQL for any EO# already there ─────
        log.info('--- Phase 1: checking Syteline for existing EO# ---')

        needs_xml = []  # orders not yet in Syteline

        for order in missing_orders:
            parts_order_id = order['PartsOrderID']
            log.info(f'[P1] {parts_order_id}: checking Syteline')

            header, lines = get_parts_order_data(mysql_cursor, parts_order_id)
            if not header or not lines:
                log.warning(f'[P1] {parts_order_id}: no data found — skipped')
                stats['skipped'] += 1
                continue

            num_lines = len(lines)
            syteline_results = check_order_in_syteline_by_partsorder(mssql_cursor, parts_order_id)

            if syteline_results:
                erp_order_no = syteline_results[0]['ERP_OrderNo']
                rows_updated = update_erp_order_no(mysql_cursor, parts_order_id, erp_order_no)
                commit(mysql_conn)
                log.info(f'[P1] {parts_order_id}: found EO# {erp_order_no} -> updated {rows_updated}/{num_lines} lines')
                stats['found_in_syteline'] += 1
            else:
                log.info(f'[P1] {parts_order_id}: not in Syteline yet — skipping (XML submission disabled)')
                needs_xml.append((parts_order_id, header, lines))

        # ── PHASE 2: push XML for orders not yet in Syteline ────────────────────
        # XML submission is disabled — Syteline ingestion not yet confirmed working.
        # Uncomment this block when ready to re-enable.
        #
        # if needs_xml:
        #     log.info(f'--- Phase 2: pushing XML for {len(needs_xml)} orders ---')
        #
        #     for parts_order_id, header, lines in needs_xml:
        #         num_lines    = len(lines)
        #         boat_serial  = header.get('OrdHdrBoatSerialNo')
        #         boat_info    = get_boat_info(mysql_cursor, boat_serial)
        #         dealer_no    = header.get('OrdHdrDealerNo', '').replace('~0', '').replace('~1', '')
        #         dealer_info  = get_dealer_info(mysql_cursor, dealer_no)
        #         xml_content  = generate_xml(header, lines, boat_info, dealer_info)
        #         claim_type   = header.get('OrdHdrClaimType', 'parts_order')
        #         order_prefix = 'WP' if claim_type == 'parts_order' else 'WN'
        #         xml_file     = write_xml_file(xml_content, parts_order_id, order_prefix)
        #         log.info(f'[P2] {parts_order_id}: XML pushed ({num_lines} lines) -> {xml_file}')
        #         stats['xml_submitted'] += 1

        if needs_xml:
            log.info(f'--- Phase 2: {len(needs_xml)} orders not in Syteline (XML submission disabled) ---')
            for parts_order_id, _, _ in needs_xml:
                log.info(f'[P2] {parts_order_id}: not in Syteline — no action taken')

        if mssql_cursor:
            mssql_cursor.close()
        mysql_cursor.close()
        mysql_conn.close()

        log.info('=' * 60)
        log.info('SYNC OE PARTS: Complete')
        log.info(f'  Total orders:        {stats["total"]}')
        log.info(f'  EO# found & updated: {stats["found_in_syteline"]}')
        log.info(f'  XML pushed:          {stats["xml_submitted"]}')
        log.info(f'  Skipped:             {stats["skipped"]}')
        log.info(f'  Errors:              {stats["errors"]}')
        log.info('=' * 60)

    except Exception as e:
        log.error(f'SYNC OE PARTS error: {e}')
        raise

if __name__ == '__main__':
    args = sys.argv[1:]
    
    if '--dry-run' in args:
        DRY_RUN = True
        args.remove('--dry-run')
    
    if '--order' in args:
        idx = args.index('--order')
        if idx + 1 < len(args):
            SINGLE_ORDER = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
    
    if args and not SINGLE_ORDER:
        SINGLE_ORDER = args[0]
    
    sync_oe_parts()
