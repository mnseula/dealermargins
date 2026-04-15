#!/usr/bin/env python3
"""
Bennington EOS Scheduler — Python replacement for the Node.js bennington_node.js scheduler.

Each function mirrors a job from the EOS JAMS scheduler. Run this script as a cron job
or with the built-in schedule loop at the bottom.

Named SQL statements (eos.sStatement) have been translated to direct MySQL queries.
EOS list operations (eos.ben.addByListName / deleteByListName) that have no MySQL
equivalent are logged and skipped — mark those TODOs as you identify the backing table.

Usage:
    python3 bennington_scheduler.py                  # run scheduler loop
    python3 bennington_scheduler.py upd_oe_parts     # run one job and exit
    python3 bennington_scheduler.py run_serial_master
    python3 bennington_scheduler.py export_reset
    python3 bennington_scheduler.py ship
"""

import sys
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

import mysql.connector

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bennington_scheduler.log'),
    ]
)
log = logging.getLogger(__name__)

# ── Database config ───────────────────────────────────────────────────────────

MYSQL_CONFIG = {
    'host':     'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port':     3306,
    'user':     'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts',
    'autocommit': False,
}

def get_db():
    return mysql.connector.connect(**MYSQL_CONFIG)


# ── Email helper ──────────────────────────────────────────────────────────────
# TODO: fill in SMTP details for your mail relay

SMTP_HOST = 'smtp.benningtonmarine.com'
SMTP_PORT = 25
EMAIL_FROM = 'noreply@benningtonmarine.com'

def send_email(to: str, body: str, subject: str = 'Bennington Scheduler'):
    """Replacement for eos.sendEmail()."""
    try:
        msg = MIMEText(body, 'html')
        msg['Subject'] = subject
        msg['From']    = EMAIL_FROM
        msg['To']      = to
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
            s.sendmail(EMAIL_FROM, [a.strip() for a in to.split(',')], msg.as_string())
        log.info(f'EMAIL sent to {to}: {subject}')
    except Exception as e:
        log.error(f'EMAIL failed to {to}: {e}')


def log_scheduler_event(name: str):
    """
    Replacement for eos.ben.addByListName('Scheduler_Log', [...]).
    Logs to Python logger; also tries to insert into warrantyparts.Scheduler_Log
    if that table exists.
    """
    d = datetime.now()
    ts = f"{d.day}/{d.month}/{d.year} @ {d.hour}:{d.minute}:{d.second}"
    log.info(f'SCHEDULER EVENT: {name} at {ts}')
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Scheduler_Log (Timestamp, Event) VALUES (%s, %s)",
            (ts, name)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass  # Scheduler_Log table may not exist — that's fine


# ══════════════════════════════════════════════════════════════════════════════
# JOB: UPD_OE_PARTS
# Writes ERP order numbers (OE#) back to PartsOrderLines from the
# ERPOrderWebOrderMatrix table populated by the PowerShell → PHP → MySQL pipeline.
# ══════════════════════════════════════════════════════════════════════════════

def upd_oe_parts():
    """
    Replacement for: eos.sStatement('UPDATE_ERP_ORDERNO')

    Joins ERPOrderWebOrderMatrix (populated from CSIPRD via PowerShell + PHP)
    against PartsOrderLines and fills in the missing ERP_OrderNo (OE#).
    """
    log_scheduler_event('UPD_OE_PARTS')
    log.info('UPD_OE_PARTS: start')
    try:
        conn = get_db()
        cursor = conn.cursor()
        sql = """
            UPDATE warrantyparts.PartsOrderLines l
            JOIN   warrantyparts.ERPOrderWebOrderMatrix e
                ON  e.WebOrderNo = l.PartsOrderID
                AND CAST(e.LineNo AS UNSIGNED) = l.OrdLineNo
            SET    l.ERP_OrderNo = e.ERPOrderNo
            WHERE  (l.ERP_OrderNo IS NULL OR l.ERP_OrderNo = '')
              AND   e.ERPOrderNo IS NOT NULL
              AND   e.ERPOrderNo != ''
        """
        cursor.execute(sql)
        rows = cursor.rowcount
        conn.commit()
        log.info(f'UPD_OE_PARTS: updated {rows} rows')
        cursor.close()
        conn.close()
    except Exception as e:
        log.error(f'UPD_OE_PARTS error: {e}')


# ══════════════════════════════════════════════════════════════════════════════
# JOB: EXPORT_RESET
# Resets the warranty claim export counter to 1 at the start of each day.
# Controls which claims appear in the next export batch.
# ══════════════════════════════════════════════════════════════════════════════

def export_reset():
    """
    Replacement for:
        eos.ben.deleteByListName('PW_warranty_claim_export_counter', '*/*')
        eos.ben.addByListName('PW_warranty_claim_export_counter', [1])

    TODO: verify the exact MySQL table/column name for PW_warranty_claim_export_counter.
    """
    log_scheduler_event('EXPORT_RESET')
    log.info('EXPORT_RESET: start')
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE warrantyparts.PW_warranty_claim_export_counter")
        cursor.execute("INSERT INTO warrantyparts.PW_warranty_claim_export_counter (Counter) VALUES (1)")
        conn.commit()
        log.info('EXPORT_RESET: counter reset to 1')
        cursor.close()
        conn.close()
    except Exception as e:
        log.error(f'EXPORT_RESET error: {e}')


# ══════════════════════════════════════════════════════════════════════════════
# JOB: RUN_SERIAL_MASTER
# Syncs boats from Update_Tables.serial_master_update into
# warrantyparts.SerialNumberMaster and SerialNumberRegistrationStatus.
# ══════════════════════════════════════════════════════════════════════════════

def run_serial_master():
    """
    Replacement for the RUN_SERIAL_MASTER function.

    Source:  Update_Tables.serial_master_update  (SER_MAST_UPDT)
    Target:  warrantyparts.SerialNumberMaster    (INS_PW_SERIAL_MASTER / UPD_PW_SERIAL_MASTER / UPD_PW_MASTER_ALL)
             warrantyparts.SerialNumberRegistrationStatus (INSERT_SN_REG_STATUS)

    Logic mirrors the Node.js version exactly:
      - New boat  → INSERT + INSERT reg status
      - Existing, origOrdType='C' → mark Active=0
      - Existing, Active=0       → full UPDATE all fields
      - Existing, Active=1       → skip (already current)

    _OLD variants (yearCheck < 7 or > 97) use the same tables here — if the EOS
    _OLD statements target a different schema, update the table name below.
    """
    log_scheduler_event('RUN_SERIAL_MASTER')
    log.info('RUN_SERIAL_MASTER: start')

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # SER_MAST_UPDT — get all boats pending sync
        cursor.execute("SELECT * FROM Update_Tables.serial_master_update")
        updates = cursor.fetchall()
        log.info(f'RUN_SERIAL_MASTER: {len(updates)} boats to process')

        if not updates:
            send_email('max.zaicev@benningtonmarine.com', 'Serial # Master has 0 Records.')
            cursor.close()
            conn.close()
            return

        new_written = 0
        for i, row in enumerate(updates):
            sn = row.get('Boat_SerialNo', '')

            # Determine _OLD variant (same logic as Node.js yearCheck)
            try:
                year_check = int(sn[-2:])
            except (ValueError, IndexError):
                year_check = 50  # default to non-old
            is_old = year_check < 7 or year_check > 97

            # SEL_ONE_SER_NO_MST — check if serial already exists
            cursor.execute(
                "SELECT * FROM warrantyparts.SerialNumberMaster WHERE Boat_SerialNo = %s",
                (sn,)
            )
            existing = cursor.fetchone()

            if not existing:
                # INS_PW_SERIAL_MASTER — new boat, insert it
                _insert_serial_master(cursor, row)
                # INSERT_SN_REG_STATUS — add registration status row
                registered    = '0'
                field_inv     = '1'
                unknown       = '0'
                snd           = '1' if row.get('Presold') == 'Y' else '0'
                cursor.execute(
                    """
                    INSERT IGNORE INTO warrantyparts.SerialNumberRegistrationStatus
                        (SN_MY, Boat_SerialNo, Registered, FieldInventory, `Unknown`, SND)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (row.get('SN_MY'), sn, registered, field_inv, unknown, snd)
                )
                new_written += 1

            else:
                orig_ord_type = row.get('OrigOrderType', '')
                master_active = existing.get('Active')

                if orig_ord_type == 'C':
                    # UPD_PW_SERIAL_MASTER — credit order, mark inactive
                    cursor.execute(
                        "UPDATE warrantyparts.SerialNumberMaster SET Active = '0' WHERE Boat_SerialNo = %s",
                        (sn,)
                    )
                    log.debug(f'Boat {sn} is type C — marked inactive')
                else:
                    if str(master_active) == '0':
                        # UPD_PW_MASTER_ALL — full update for inactive (previously written) boat
                        _update_serial_master_all(cursor, row, existing.get('ProdNo'))
                        log.debug(f'Boat {sn} — full update')
                    else:
                        # Active=1, already current — skip
                        pass

            conn.commit()

        log.info(f'RUN_SERIAL_MASTER: done. New records written: {new_written}')
        cursor.close()
        conn.close()

    except Exception as e:
        log.error(f'RUN_SERIAL_MASTER error: {e}')


def _insert_serial_master(cursor, row: dict):
    """INS_PW_SERIAL_MASTER — insert a new boat into SerialNumberMaster."""
    cursor.execute(
        """
        INSERT IGNORE INTO warrantyparts.SerialNumberMaster (
            Boat_SerialNo, SN_MY, BoatItemNo, Series, BoatDesc1, BoatDesc2, SerialModelYear,
            ERP_OrderNo, ProdNo, OrigOrderType, InvoiceNo, ApplyToNo, InvoiceDateYYYYMMDD,
            DealerNumber, DealerName, DealerCity, DealerState, DealerZip, DealerCountry, ParentRepName,
            ColorPackage, PanelColor, AccentPanel, TrimAccent, BaseVinyl,
            WebOrderNo, Presold, Active, SN_ID, Quantity
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        """,
        (
            row.get('Boat_SerialNo'),  row.get('SN_MY'),            row.get('BoatItemNo'),
            row.get('Series'),         row.get('BoatDesc1'),         row.get('BoatDesc2'),
            row.get('SerialModelYear'),
            row.get('ERP_OrderNo'),    row.get('ProdNo'),            row.get('OrigOrderType'),
            row.get('InvoiceNo'),      row.get('ApplyToNo'),         row.get('InvoiceDateYYYYMMDD'),
            row.get('DealerNumber'),   row.get('DealerName'),        row.get('DealerCity'),
            row.get('DealerState'),    row.get('DealerZip'),         row.get('DealerCountry'),
            row.get('ParentRepName'),
            row.get('ColorPackage'),   row.get('PanelColor'),        row.get('AccentPanel'),
            row.get('TrimAccent'),     row.get('BaseVinyl'),
            row.get('WebOrderNo'),     row.get('Presold'),           row.get('Active'),
            row.get('SN_ID'),          row.get('Quantity'),
        )
    )


def _update_serial_master_all(cursor, row: dict, existing_prod_no):
    """
    UPD_PW_MASTER_ALL — full update of all fields for an existing inactive boat.
    ProdNo is preserved from the existing record (not overwritten from the source).
    """
    cursor.execute(
        """
        UPDATE warrantyparts.SerialNumberMaster SET
            SN_MY              = %s,
            BoatItemNo         = %s,
            Series             = %s,
            BoatDesc1          = %s,
            BoatDesc2          = %s,
            SerialModelYear    = %s,
            ERP_OrderNo        = %s,
            ProdNo             = %s,
            OrigOrderType      = %s,
            InvoiceNo          = %s,
            ApplyToNo          = %s,
            InvoiceDateYYYYMMDD = %s,
            DealerNumber       = %s,
            DealerName         = %s,
            DealerCity         = %s,
            DealerState        = %s,
            DealerZip          = %s,
            DealerCountry      = %s,
            ParentRepName      = %s,
            ColorPackage       = %s,
            PanelColor         = %s,
            AccentPanel        = %s,
            TrimAccent         = %s,
            BaseVinyl          = %s,
            WebOrderNo         = %s,
            Presold            = %s,
            Active             = %s,
            SN_ID              = %s,
            Quantity           = %s
        WHERE Boat_SerialNo = %s
        """,
        (
            row.get('SN_MY'),            row.get('BoatItemNo'),       row.get('Series'),
            row.get('BoatDesc1'),         row.get('BoatDesc2'),        row.get('SerialModelYear'),
            row.get('ERP_OrderNo'),       existing_prod_no,            row.get('OrigOrderType'),
            row.get('InvoiceNo'),         row.get('ApplyToNo'),        row.get('InvoiceDateYYYYMMDD'),
            row.get('DealerNumber'),      row.get('DealerName'),       row.get('DealerCity'),
            row.get('DealerState'),       row.get('DealerZip'),        row.get('DealerCountry'),
            row.get('ParentRepName'),
            row.get('ColorPackage'),      row.get('PanelColor'),       row.get('AccentPanel'),
            row.get('TrimAccent'),        row.get('BaseVinyl'),
            row.get('WebOrderNo'),        row.get('Presold'),          row.get('Active'),
            row.get('SN_ID'),             row.get('Quantity'),
            row.get('Boat_SerialNo'),
        )
    )


# ══════════════════════════════════════════════════════════════════════════════
# JOB: SHIP
# Reads new shipments from Syteline (via SHIP_UPDATE22) and writes tracking
# numbers + marks part order lines as completed.
# ══════════════════════════════════════════════════════════════════════════════

# PW_GET_PART_STATE_CHG_ID — next sequence ID for line-level status tracker
GET_LINE_STATE_CHG_ID_SQL = (
    "SELECT MAX(StateChg_ID) + 1 AS ID "
    "FROM warrantyparts.PartsOrderLine_StateChangeStatusTracker"
)

# PW_GET_PART_STATE_CHG_ID_HEADER — next sequence ID for header-level status tracker
GET_HDR_STATE_CHG_ID_SQL = (
    "SELECT MAX(StateChg_ID) + 1 AS ID "
    "FROM warrantyparts.PartsOrderHeader_StateChangeStatusTracker"
)

SHIP_UPDATE22_SQL = """
    SELECT DISTINCT
        t1.UPSTrackingNo,
        t1.ERP_OrderNo,
        t2.OrdLineStatus,
        TRIM(LEADING '0' FROM t1.WebOrderNo)                              AS PartsOrderID,
        t1.LineNo,
        CONCAT(TRIM(LEADING '0' FROM t1.WebOrderNo), '-', t1.LineNo)     AS ShipmentID,
        DATE_FORMAT(STR_TO_DATE(t1.ShipDate, '%%Y%%m%%d'), '%%m/%%d/%%Y') AS `date`,
        t2.OrdLineID,
        t1.RGA
    FROM warrantyparts.ShipmentTrackingInfo AS t1
    JOIN warrantyparts.PartsOrderLines      AS t2
        ON t1.WebOrderNo = t2.PartsOrderID
       AND t1.LineNo     = t2.OrdLineNo
    WHERE (
            t2.OrdLineShipmentTrackingNo IS NULL
         OR t2.OrdLineShipmentTrackingNo = ''
         OR (t2.OrdLineStatus = 'exported' AND LENGTH(t2.OrdLineShipmentTrackingNo) > 0)
          )
      AND t1.WebOrderNo  != ''
      AND t1.LineNo      != ''
      AND t2.PartsOrderID IS NOT NULL
      AND t1.RGA = %s
"""


def ship():
    """
    Replacement for SHIP.

    Reads new shipments from ShipmentTrackingInfo (SHIP_UPDATE22), merges RGA
    tracking numbers onto matching lines, then marks each part order line as
    completed with its tracking number and ship date, and logs the state change
    to PartsOrderLine_StateChangeStatusTracker.
    """
    log_scheduler_event('SHIP')
    log.info('SHIP: start')
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(SHIP_UPDATE22_SQL, ('N',))
        new_data = cursor.fetchall()
        log.info(f'SHIP: {len(new_data)} normal lines')

        cursor.execute(SHIP_UPDATE22_SQL, ('Y',))
        new_data_rga = cursor.fetchall()
        log.info(f'SHIP: {len(new_data_rga)} RGA lines')

        # Merge RGA tracking numbers onto matching non-RGA lines
        data_map = {(r['PartsOrderID'], r['LineNo']): r for r in new_data}
        for r in new_data_rga:
            key = (r['PartsOrderID'], r['LineNo'])
            if key in data_map:
                data_map[key]['UPSTrackingNo'] += ',' + r['UPSTrackingNo']
            else:
                data_map[key] = r
        actual = list(data_map.values())
        log.info(f'SHIP: {len(actual)} total lines to update')

        email_body = ''
        for row in actual:
            poid      = row['PartsOrderID']
            line_no   = row['LineNo']
            track_no  = row['UPSTrackingNo']
            ship_date = row['date']
            oe_number = row['ERP_OrderNo']
            ord_line_id = row['OrdLineID']

            # --- PW_GET_PART_STATE_CHG_ID ---
            cursor.execute(GET_LINE_STATE_CHG_ID_SQL)
            state_chg_id = cursor.fetchone()['ID'] or 1

            # --- SHIP_UPDATE_PARTS ---
            cursor.execute(
                """
                UPDATE warrantyparts.PartsOrderLines SET
                    OrdLineShipmentTrackingNo = %s,
                    OrdLineActShipDate        = %s,
                    OrdLineStatus             = %s,
                    OrdLinePublicStatus       = %s,
                    OrdLineSttusLastUpd       = %s,
                    ERP_OrderNo               = %s
                WHERE PartsOrderID = %s AND OrdLineNo = %s
                """,
                (track_no, ship_date, 'completed', 'Completed',
                 datetime.now().strftime('%m/%d/%Y'), oe_number,
                 poid, line_no)
            )

            # --- PW_ADD_STATUS_TO_TRACKER_PARTS ---
            cursor.execute(
                """
                INSERT INTO warrantyparts.PartsOrderLine_StateChangeStatusTracker (
                    StateChg_ID,
                    StateChg_EntityID,
                    OrdLineID,
                    StateChg_EntityType,
                    StateChg_ChgToPublicState,
                    StateChg_ChgToState,
                    StateChg_UserID,
                    StateChg_CreateDate,
                    StateChg_DeleteDate
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (state_chg_id, ord_line_id, ord_line_id,
                 'PartOrderLineItem', 'completed', 'Completed', '', ship_date, '')
            )

            conn.commit()
            email_body += (
                f"Updated {poid} line {line_no} "
                f"tracking {track_no} ship date {ship_date}<br>"
            )
            log.info(f'SHIP: {poid} line {line_no} tracking {track_no}')

        if email_body:
            send_email(
                'ZSpringman@benningtonmarine.com, DHartsough@benningtonmarine.com, spenick@benningtonmarine.com',
                email_body,
                'ship update'
            )

        cursor.close()
        conn.close()

    except Exception as e:
        log.error(f'SHIP error: {e}')


# ══════════════════════════════════════════════════════════════════════════════
# JOB: DLR_UPDATE
# Syncs dealer records from Syteline into the EOS dealer list.
# ══════════════════════════════════════════════════════════════════════════════

def dlr_update():
    """
    Replacement for DLR_UPDATE.

    TODO: provide SQL for:
        DLR_UPDT_TBL   — source of updated dealer data from Syteline
        ALL_DLR        — current dealer list
        UPD_DLR_LIST_SCH  — update existing dealer row
        INS_DLR_LIST      — insert new dealer row
    """
    log_scheduler_event('DLR_UPDATE')
    log.info('DLR_UPDATE: start — TODO: add DLR_UPDT_TBL / ALL_DLR SQL')


# ══════════════════════════════════════════════════════════════════════════════
# JOB: WARR_CLAIMS
# Updates Club Bennington IDs on owner records.
# (Despite the name, this is NOT warranty claim processing.)
# ══════════════════════════════════════════════════════════════════════════════

def warr_claims():
    """
    Replacement for WARR_CLAIMS (Club Bennington ID updates).

    TODO: provide SQL for:
        CLUB_B_UPDATES_TO_OWNERS   — returns {OwnerID, ClubID, OwnerEmail} for pending updates
        CLUB_B_ADD_ID_UPDATE       — UPDATE owners SET ClubID=?, Active=1, Email=? WHERE OwnerID=?
    """
    log_scheduler_event('WARR_CLAIMS')
    log.info('WARR_CLAIMS: start — TODO: add CLUB_B_UPDATES_TO_OWNERS SQL')


# ══════════════════════════════════════════════════════════════════════════════
# JOB: SPECS_COMPILE_OPTIONS
# Pre-compiles all live boat options per ProdNo for the specs display.
# ══════════════════════════════════════════════════════════════════════════════

def specs_compile_options():
    """
    Replacement for SPECS_COMPILE_OPTIONS.

    TODO: provide SQL for:
        SPECS_DEL_COMPILED_OPTIONS          — TRUNCATE / DELETE compiled options
        SEL_DISCTINT_PRODNOS_IN_OPTIONS     — SELECT DISTINCT ProdNo FROM options table
        SEL_SPECS_ALL_LIVE_BOAT_OPTIONS     — SELECT options for one ProdNo
        INS_SPECS_OPTIONS_COMPILED          — INSERT compiled options row
    """
    log_scheduler_event('SPECS_COMPILE_OPTIONS')
    log.info('SPECS_COMPILE_OPTIONS: start — TODO: add SQL statements')


# ══════════════════════════════════════════════════════════════════════════════
# JOB: BOAT_REGISTRATION
# Pushes pending boat registrations to the EOS registration endpoint.
# ══════════════════════════════════════════════════════════════════════════════

def boat_registration():
    """
    Replacement for BOAT_REGISTRATION.

    TODO: provide SQL for:
        LOAD_BOAT_REG_UPDATE_TABLE   — rows pending registration
        UPDATE_BOAT_REG_UPDATE_TABLE — mark row as processed after success

    The HTTP call goes to https://node.eoscpq.com/bennington/pwregistration
    with the boat data as JSON. Keeping that endpoint call intact.
    """
    import requests as req
    log_scheduler_event('BOAT_REGISTRATION')
    log.info('BOAT_REGISTRATION: start — TODO: add LOAD_BOAT_REG_UPDATE_TABLE SQL')

    # try:
    #     conn = get_db()
    #     cursor = conn.cursor(dictionary=True)
    #     cursor.execute("<LOAD_BOAT_REG_UPDATE_TABLE SQL>")
    #     boats = cursor.fetchall()
    #     log.info(f'BOAT_REGISTRATION: {len(boats)} boats to register')
    #
    #     success, failure = [], []
    #     for boat in boats:
    #         try:
    #             r = req.post(
    #                 'https://node.eoscpq.com/bennington/pwregistration',
    #                 json={'key': '<PUBLIC_KEY>', 'data': boat},
    #                 timeout=30
    #             )
    #             result = r.json()
    #             if result.get('result'):
    #                 cursor.execute("<UPDATE_BOAT_REG_UPDATE_TABLE SQL>", (boat['SerialNo'],))
    #                 conn.commit()
    #                 success.append(boat['SerialNo'])
    #             else:
    #                 failure.append(f"{boat['SerialNo']}: {result.get('error')}")
    #         except Exception as e:
    #             failure.append(f"{boat['SerialNo']}: {e}")
    #
    #     body = ''
    #     if failure:
    #         body += 'NOT registered:<br>' + '<br>'.join(failure) + '<br><br>'
    #     if success:
    #         body += 'Registered:<br>' + '<br>'.join(success)
    #     send_email('spenick@benningtonmarine.com', body, 'Boat Registration Import Report')
    #     cursor.close()
    #     conn.close()
    # except Exception as e:
    #     log.error(f'BOAT_REGISTRATION error: {e}')


# ══════════════════════════════════════════════════════════════════════════════
# JOB: DLR_GEOCODE
# Geocodes dealer addresses and updates the dealer lat/long list.
# ══════════════════════════════════════════════════════════════════════════════

def dlr_geocode():
    """
    Replacement for DLR_GEOCODE.

    TODO: provide SQL for ALL_DLR and the Dealer_Latitude_Longitude table structure.
    TODO: provide Google Maps API key (or whichever geocoding service EOS uses).
    """
    log_scheduler_event('DLR_GEOCODE')
    log.info('DLR_GEOCODE: start — TODO: add geocoding API key and ALL_DLR SQL')


# ══════════════════════════════════════════════════════════════════════════════
# JOBs: VALIDATE / BOAT_LOG / REPORT / CHECK_PRINT_SHOP
# These all call ben/sweep or ben/print_shop_check Node modules.
# TODO: determine what HTTP endpoints or SQL these map to.
# ══════════════════════════════════════════════════════════════════════════════

def validate():
    log_scheduler_event('VALIDATE')
    log.info('VALIDATE: TODO — requires ben/sweep module mapping')

def boat_log():
    log_scheduler_event('BOAT_LOG')
    log.info('BOAT_LOG: TODO — requires ben/sweep module mapping')

def report():
    log_scheduler_event('REPORT')
    log.info('REPORT: TODO — requires ben/sweep module mapping')

def check_print_shop():
    log_scheduler_event('CHECK_PRINT_SHOP')
    log.info('CHECK_PRINT_SHOP: TODO — requires ben/print_shop_check module mapping')


# ══════════════════════════════════════════════════════════════════════════════
# Schedule setup
# Mirror the JAMS schedule intervals from EOS.
# TODO: confirm exact run times for each job from JAMS.
# ══════════════════════════════════════════════════════════════════════════════

JOB_MAP = {
    'upd_oe_parts':        upd_oe_parts,
    'export_reset':        export_reset,
    'run_serial_master':   run_serial_master,
    'ship':                ship,
    'dlr_update':          dlr_update,
    'warr_claims':         warr_claims,
    'specs_compile_options': specs_compile_options,
    'boat_registration':   boat_registration,
    'dlr_geocode':         dlr_geocode,
    'validate':            validate,
    'boat_log':            boat_log,
    'report':              report,
    'check_print_shop':    check_print_shop,
}


def run_scheduler():
    """Run all jobs on a schedule. Requires: pip install schedule"""
    try:
        import schedule
        import time
    except ImportError:
        log.error("pip install schedule")
        sys.exit(1)

    # TODO: adjust run times to match JAMS schedule
    schedule.every().day.at("00:05").do(export_reset)
    schedule.every(15).minutes.do(upd_oe_parts)
    schedule.every().day.at("01:00").do(run_serial_master)
    schedule.every(30).minutes.do(ship)
    schedule.every().day.at("02:00").do(dlr_update)
    schedule.every().day.at("03:00").do(specs_compile_options)
    schedule.every().day.at("04:00").do(boat_registration)
    schedule.every().day.at("05:00").do(dlr_geocode)
    schedule.every().hour.do(validate)
    schedule.every().hour.do(boat_log)
    schedule.every().day.at("06:00").do(report)
    schedule.every(5).minutes.do(check_print_shop)

    log.info("Scheduler started. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        job_name = sys.argv[1].lower()
        if job_name in JOB_MAP:
            log.info(f'Running single job: {job_name}')
            JOB_MAP[job_name]()
        else:
            log.error(f'Unknown job: {job_name}. Available: {", ".join(JOB_MAP.keys())}')
            sys.exit(1)
    else:
        run_scheduler()
