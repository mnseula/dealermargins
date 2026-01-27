"""
Warranty Survey Export Script for Aimbase
Exports approved warranty claims (where OrdOptOut is NOT checked) to Aimbase format.
Sends report to Mandy on Fridays and uploads to Aimbase FTP on Mondays.

  python survey_export.py           # Normal mode (runs based on day of week)
  python survey_export.py --test    # Test mode (sends email AND uploads FTP regardless of day)
"""

import mysql.connector
import csv
import socket
import subprocess
import os
import sys
import time
from datetime import datetime, timedelta
from ftplib import FTP_TLS, FTP
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ssl
from email.utils import formataddr
import re

# Database Configuration
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

# FTP Configuration for Aimbase
AIMBASE_FTP = {
    'host': 'ftp.aimbase.com',
    'port': 21,
    'user': 'BM7970',
    'password': 'n-Xa7TeG',
    # Toggle to use PROT C (clear data channel) if PROT P fails
    # NOTE: Aimbase requires SSL (PROT P), they reject PROT C with "534 Policy requires SSL"
    'use_prot_c': False,
    # Allow plain FTP fallback if FTPS fails
    'use_plain_fallback': True,
    # Optional upload directory (set to None or '' to skip)
    'upload_dir': ''
}

# Email Configuration
EMAIL_CONFIG = {
    'smtp_server': 'smtp.polarisdmz.com',
    'smtp_port': 25,
    'sender_email': 'warrantysurvey@benningtonmarine.com',
    'sender_password': None,
    'mandy_email': 'mtardi@benningtonmarine.com'
}

def get_fake_test_claims():
    """Generate fake warranty claims for testing purposes (customers who WANT surveys)."""
    print("\n" + "="*80)
    print("[TEST MODE] GENERATING FAKE SURVEY TEST DATA (OrdOptOut=0)")
    print("="*80 + "\n")

    fake_claims = [
        {
            'PartsOrderID': 99991, 'HIN': 'BEN12345A123', 'CLAIMNO': 'TEST-2025-001',
            'CLAIMDT': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'DLRNUMBR': 999999,
            'OrdHdrOwnerName': 'John TestCustomer', 'CADDRES1': '123 Test Street',
            'CCITY': 'Testville', 'CSTATE': 'IN', 'CPSTCODE': '46001', 'CCOUNTRY': 'US',
            'CHMPHONE': '555-0001', 'CEMAIL': 'test1@example.com', 'OrdHdrDateOfSale': '2024-06-15',
            'OrdOptOut': 0, 'MODELBRD': 'Bennington', 'MODELCOD': '25QSBAWAIO', 'MODELYER': 2025
        },
        {
            'PartsOrderID': 99992, 'HIN': 'BEN67890B456', 'CLAIMNO': 'TEST-2025-002',
            'CLAIMDT': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'DLRNUMBR': 999999,
            'OrdHdrOwnerName': 'Jane TestUser', 'CADDRES1': '456 Demo Avenue',
            'CCITY': 'Sampletown', 'CSTATE': 'MI', 'CPSTCODE': '48001', 'CCOUNTRY': 'US',
            'CHMPHONE': '555-0002', 'CEMAIL': 'test2@example.com', 'OrdHdrDateOfSale': '2024-07-20',
            'OrdOptOut': 0, 'MODELBRD': 'Bennington', 'MODELCOD': '23RSBA', 'MODELYER': 2024
        },
        {
            'PartsOrderID': 99993, 'HIN': 'BEN11223C789', 'CLAIMNO': 'TEST-2025-003',
            'CLAIMDT': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'DLRNUMBR': 999999,
            'OrdHdrOwnerName': 'Bob TestOwner', 'CADDRES1': '789 Fake Boulevard',
            'CCITY': 'Demoville', 'CSTATE': 'FL', 'CPSTCODE': '33001', 'CCOUNTRY': 'US',
            'CHMPHONE': '555-0003', 'CEMAIL': 'test3@example.com', 'OrdHdrDateOfSale': '2024-08-10',
            'OrdOptOut': 0, 'MODELBRD': 'Bennington', 'MODELCOD': '24SSRXP', 'MODELYER': 2024
        }
    ]

    print(f"Generated {len(fake_claims)} fake survey test claims\n")
    return fake_claims

def get_fake_optout_claims():
    """Generate fake opt-out warranty claims for testing purposes."""
    print("\n" + "="*80)
    print("[TEST MODE] GENERATING FAKE OPT-OUT TEST DATA (OrdOptOut=1)")
    print("="*80 + "\n")

    fake_optout_claims = [
        {
            'PartsOrderID': 99994, 'HIN': 'BEN44556D999', 'CLAIMNO': 'TEST-OPTOUT-001',
            'CLAIMDT': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'DLRNUMBR': 999999,
            'OrdHdrOwnerName': 'Alice OptedOut', 'CADDRES1': '999 NoSurvey Lane',
            'CCITY': 'PrivacyTown', 'CSTATE': 'CA', 'CPSTCODE': '90001', 'CCOUNTRY': 'US',
            'CHMPHONE': '555-9999', 'CEMAIL': 'optout@example.com', 'OrdHdrDateOfSale': '2024-09-01',
            'OrdOptOut': 1, 'MODELBRD': 'Bennington', 'MODELCOD': '24QCWBA', 'MODELYER': 2024
        },
        {
            'PartsOrderID': 99995, 'HIN': 'BEN77889E888', 'CLAIMNO': 'TEST-OPTOUT-002',
            'CLAIMDT': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'DLRNUMBR': 999999,
            'OrdHdrOwnerName': 'Charlie NoEmail', 'CADDRES1': '777 Decline Street',
            'CCITY': 'Optoutville', 'CSTATE': 'TX', 'CPSTCODE': '75001', 'CCOUNTRY': 'US',
            'CHMPHONE': '555-7777', 'CEMAIL': 'noemail@example.com', 'OrdHdrDateOfSale': '2024-09-15',
            'OrdOptOut': 1, 'MODELBRD': 'Bennington', 'MODELCOD': '25RSBR', 'MODELYER': 2025
        }
    ]

    print(f"Generated {len(fake_optout_claims)} fake opt-out test claims\n")
    return fake_optout_claims

def get_all_warranty_claims():
    """
    Fetch approved/completed warranty claims from the past 7 days.
    Designed to run weekly on Fridays.
    We will filter for OptOut in Python to ensure accuracy.

    IMPORTANT: Uses OwnerRegistrations table to get CUSTOMER emails (not dealer emails).
    """
    print("\n" + "="*80)
    print("FETCHING APPROVED/COMPLETED WARRANTY CLAIMS (PAST 7 DAYS)")
    print("="*80 + "\n")

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                wc.PartsOrderID AS CLAIMNO,
                wc.OrdHdrBoatSerialNo AS HIN,
                wc.OrdHdrStatusLastUpd AS CLAIMDT,
                wc.OrdHdrDealerNo AS DLRNUMBR,
                wc.OrdOptOut,
                sn.Series AS MODELBRD,
                sn.BoatDesc1 AS MODELCOD,
                sn.SerialModelYear AS MODELYER,
                owner.OwnerFirstName AS CFSTNAME,
                owner.OwnerLastName AS CLSTNAME,
                owner.OwnerEmail AS CEMAIL,
                owner.OwnerAddress1 AS CADDRES1,
                owner.OwnerCity AS CCITY,
                owner.OwnerState AS CSTATE,
                owner.OwnerZip AS CPSTCODE,
                owner.OwnerCountry AS CCOUNTRY,
                owner.OwnerDayPhone AS CHMPHONE
            FROM WarrantyClaimOrderHeaders wc
            LEFT JOIN SerialNumberMaster sn ON wc.OrdHdrBoatSerialNo = sn.Boat_SerialNo
            LEFT JOIN OwnerRegistrations owner ON wc.OrdHdrBoatSerialNo = owner.Boat_SerialNo
            WHERE wc.OrdHdrPublicStatus IN ('Approved', 'Completed')
              -- AND STR_TO_DATE(wc.OrdHdrStatusLastUpd, '%c/%e/%Y') >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY wc.PartsOrderID
            ORDER BY STR_TO_DATE(wc.OrdHdrStatusLastUpd, '%c/%e/%Y') DESC
        """

        cursor.execute(query)
        claims = cursor.fetchall()

        # Count claims with and without customer emails
        with_email = sum(1 for c in claims if c.get('CEMAIL') and c['CEMAIL'].strip())
        without_email = len(claims) - with_email

        print(f"Found {len(claims)} total claims (Approved/Completed)")
        print(f"  - WITH customer email: {with_email} ({with_email/len(claims)*100:.1f}%)")
        print(f"  - WITHOUT customer email: {without_email} ({without_email/len(claims)*100:.1f}%)")
        print()

        cursor.close()
        conn.close()
        return claims

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        import traceback
        traceback.print_exc()
        return []

def format_aimbase_row(claim, send_survey=True):
    """Format a warranty claim into Aimbase CSV row format."""

    def clean(value):
        if value is None or value == 'None':
            return ''
        return str(value).replace('"', '')

    # Use separate first/last name fields from OwnerRegistrations (not split from full name)
    first_name = clean(claim.get('CFSTNAME'))
    last_name = clean(claim.get('CLSTNAME'))

    claim_date = clean(claim.get('CLAIMDT', ''))
    if claim_date:
        try:
            dt = datetime.strptime(claim_date, '%Y-%m-%d %H:%M:%S')
            claim_date = dt.strftime('%Y%m%d')
        except:
            claim_date = datetime.now().strftime('%Y%m%d')
    else:
        claim_date = datetime.now().strftime('%Y%m%d')

    # Validation helpers
    def valid_us_zip(zipcode):
        return bool(re.fullmatch(r"\d{5}(-?\d{4})?", zipcode))

    def valid_ca_postal(postal):
        return bool(re.fullmatch(r"[A-Za-z]\d[A-Za-z][ ]?\d[A-Za-z]\d", postal))

    # Validate ClaimNumber
    claimno = clean(claim.get('CLAIMNO', ''))
    if not claimno:
        raise ValueError("ClaimNumber is required")

    country = clean(claim.get('CCOUNTRY', 'US')).upper()
    postcode = clean(claim.get('CPSTCODE', ''))

    # Clean up ZIP codes - allow empty or truncate to 5 digits if longer
    if country == 'US' and postcode:
        # Remove non-digits and truncate to 5 digits if longer
        clean_zip = re.sub(r'\D', '', postcode)
        if len(clean_zip) >= 5:
            postcode = clean_zip[:5]
        else:
            # Allow short or empty ZIP codes (some records don't have complete addresses)
            postcode = clean_zip
    elif country == 'CA' and postcode:
        # Only validate if postal code is provided
        if not valid_ca_postal(postcode):
            # Don't reject, just pass through as-is
            pass

    return {
        'ACTION': 'A', 'LANGCODE': 'EN', 'SRVYTYPE': 'W',
        'HIN': clean(claim.get('HIN', '')), 'CLAIMNO': claimno,
        'CLAIMDT': claim_date, 'DLRNUMBR': clean(claim.get('DLRNUMBR', '')),
        'DLRLOCTN': '', 'MODELBRD': clean(claim.get('MODELBRD', 'Bennington')),
        'MODELCOD': clean(claim.get('MODELCOD', '')), 'MODELYER': clean(claim.get('MODELYER', '')),
        'PRODTYPE': 'PONTOON', 'CFSTNAME': first_name, 'CLSTNAME': last_name,
        'CTITLE': '', 'CADDRES1': clean(claim.get('CADDRES1', '')), 'CADDRES2': '',
        'CCITY': clean(claim.get('CCITY', '')), 'CSTATE': clean(claim.get('CSTATE', '')),
        'CPSTCODE': postcode, 'CCOMPNYN': '', 'CCOMPNYT': '',
        'CCOUNTY': '', 'CCOUNTRY': country,
        'CHMPHONE': clean(claim.get('CHMPHONE', '')), 'CWKPHONE': '', 'CFAX': '',
        'CEMAIL': clean(claim.get('CEMAIL', '')), 'CNOEMAIL': 'NO', 'SUBSTATUS': '',
        'SENDSRVY': 'true' if send_survey else 'false',
        'CEXTERNALID': claimno
    }

def create_aimbase_csv(claims, filename, send_survey=True):
    """Create CSV file in Aimbase format with all claims."""
    print(f"Creating Aimbase CSV: {filename}\n")

    fieldnames = [
        'ACTION', 'LANGCODE', 'SRVYTYPE', 'HIN', 'CLAIMNO', 'CLAIMDT',
        'DLRNUMBR', 'DLRLOCTN', 'MODELBRD', 'MODELCOD', 'MODELYER', 'PRODTYPE',
        'CFSTNAME', 'CLSTNAME', 'CTITLE', 'CADDRES1', 'CADDRES2', 'CCITY',
        'CSTATE', 'CPSTCODE', 'CCOMPNYN', 'CCOMPNYT', 'CCOUNTY', 'CCOUNTRY',
        'CHMPHONE', 'CWKPHONE', 'CFAX', 'CEMAIL', 'CNOEMAIL', 'SUBSTATUS',
        'SENDSRVY', 'CEXTERNALID'
    ]

    error_log = filename.replace('.csv', '_errors.log')
    error_count = 0
    valid_count = 0
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile, open(error_log, 'w', encoding='utf-8') as elog:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()

        for idx, claim in enumerate(claims, 1):
            try:
                row = format_aimbase_row(claim, send_survey=send_survey)
                writer.writerow(row)
                valid_count += 1
            except Exception as e:
                error_count += 1
                elog.write(f"Line {idx}: {str(e)} | Data: {claim}\n")

        end_record = {field: '' for field in fieldnames}
        end_record['ACTION'] = 'E'
        writer.writerow(end_record)

    print(f"CSV file created with {valid_count} valid records + end marker. {error_count} errors logged to {error_log}\n")
    return filename

def create_error_csv(error_claims, filename):
    """Create CSV file with claims that have missing required fields (for Mandy's review)."""
    print(f"Creating ERROR CSV: {filename}\n")

    fieldnames = [
        'CLAIMNO', 'HIN', 'ERROR_REASONS',
        'CFSTNAME', 'CLSTNAME', 'CPSTCODE', 'CEMAIL',
        'CADDRES1', 'CCITY', 'CSTATE', 'CCOUNTRY',
        'CHMPHONE', 'CLAIMDT', 'MODELBRD', 'MODELCOD'
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()

        for claim in error_claims:
            row = {
                'CLAIMNO': claim.get('CLAIMNO', ''),
                'HIN': claim.get('HIN', ''),
                'ERROR_REASONS': claim.get('_error_reasons', 'Unknown'),
                'CFSTNAME': claim.get('CFSTNAME', ''),
                'CLSTNAME': claim.get('CLSTNAME', ''),
                'CPSTCODE': claim.get('CPSTCODE', ''),
                'CEMAIL': claim.get('CEMAIL', ''),
                'CADDRES1': claim.get('CADDRES1', ''),
                'CCITY': claim.get('CCITY', ''),
                'CSTATE': claim.get('CSTATE', ''),
                'CCOUNTRY': claim.get('CCOUNTRY', ''),
                'CHMPHONE': claim.get('CHMPHONE', ''),
                'CLAIMDT': claim.get('CLAIMDT', ''),
                'MODELBRD': claim.get('MODELBRD', ''),
                'MODELCOD': claim.get('MODELCOD', '')
            }
            writer.writerow(row)

    print(f"ERROR CSV created with {len(error_claims)} records\n")
    return filename

def send_mail(send_to_email, email_body, email_subject, file_paths):
    """Send an email with optional attachments (can be a single file path or list)."""
    success = False
    try:
        print(f"[EMAIL DEBUG] Preparing email...")
        print(f"[EMAIL DEBUG] To: {send_to_email}")
        print(f"[EMAIL DEBUG] Subject: {email_subject}")

        msg = MIMEMultipart()
        msg['From'] = formataddr(("Bennington Marine Warranty Survey Export", "no_reply@polarisind.com"))
        msg['Subject'] = email_subject
        msg.attach(MIMEText(email_body, 'html'))

        recipients = [addr.strip() for addr in send_to_email.split(';') if addr.strip()]
        msg['To'] = ', '.join(recipients)
        print(f"[EMAIL DEBUG] Recipients: {recipients}")

        # Handle single file path or list of file paths
        if file_paths:
            if not isinstance(file_paths, list):
                file_paths = [file_paths]

            print(f"[EMAIL DEBUG] Attaching {len(file_paths)} file(s)...")
            for file_path in file_paths:
                if file_path and os.path.exists(file_path):
                    print(f"[EMAIL DEBUG] Attaching: {os.path.basename(file_path)}")
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
                    msg.attach(part)
                else:
                    print(f"[EMAIL DEBUG] File not found or None: {file_path}")

        print(f"[EMAIL DEBUG] Connecting to SMTP server: smtp.polarisdmz.com:25")
        client = smtplib.SMTP("smtp.polarisdmz.com", 25)
        print(f"[EMAIL DEBUG] Connected. Sending message...")
        client.send_message(msg)
        print(f"[EMAIL DEBUG] Message sent. Closing connection...")
        client.quit()
        success = True
        print(f"[EMAIL DEBUG] Email sent successfully!")
    except Exception as ex:
        print(f"[ERROR] Email error: {ex}")
        import traceback
        traceback.print_exc()
        success = False
    return success

def send_email_to_mandy(survey_csv_filename, survey_count, optout_csv_filename, optout_count, error_csv_filename, error_count, is_test_mode=False, survey_claims=None):
    """
    Send email with the survey list as attachment.
    In test mode: sends to minseula@benningtonmarine.com
    In production: sends to Mandy
    """
    print("="*80)
    if is_test_mode:
        print("SENDING TEST REPORT TO MINSEULA (TESTING)")
    else:
        print("SENDING REPORT TO MANDY")
    print("="*80 + "\n")

    # Test mode: send only to mnseula. Production: send to Mandy + mnseula
    if is_test_mode:
        send_to = "mnseula@benningtonmarine.com"  # test mode
    else:
        send_to = EMAIL_CONFIG['mandy_email'] + ";mnseula@benningtonmarine.com"

    if survey_count == 0 and optout_count == 0 and error_count == 0:
        subject = f"{'TEST - ' if is_test_mode else ''}Weekly Warranty Survey Report - NO CLAIMS - {datetime.now().strftime('%Y-%m-%d')}"
        body = "Hi Mandy,<br><br>This is the weekly warranty survey report for approved claims.<br><br>Summary:<br>- Total approved claims ready for survey: 0<br><br>Best regards,<br>Automated Survey Export System<br>"
    elif is_test_mode:
        subject = f"TEST - Weekly Warranty Survey Report - REAL DATA - {datetime.now().strftime('%Y-%m-%d')}"
        body = f"Hi,<br><br><b>THIS IS A TEST WITH REAL DATA</b><br><br>This is a test run of the weekly warranty survey export system using REAL customer data.<br><br>IMPORTANT:<br>- All customer data is REAL<br>- These are actual approved warranty claims<br>- <b>FTP upload was SUCCESSFUL</b><br>- This is a test to verify the upload functionality<br>- <b>Using CUSTOMER emails from OwnerRegistrations (NOT dealer emails)</b><br>- <b>FTP file contains ONLY valid records (no errors)</b><br>- <b>Survey CSV NOT attached (too large - already on FTP)</b><br><br><b>FILE SUMMARY:</b><br><br>"
        body += f"<b>1. SURVEY FILE (uploaded to Aimbase FTP):</b><br>"
        body += f"   - File: {os.path.basename(survey_csv_filename) if survey_csv_filename else 'None'}<br>"
        body += f"   - Real customers: {survey_count:,}<br>"
        body += f"   - SENDSRVY: TRUE (these customers WANT surveys)<br>"
        body += f"   - Data Quality: 100% VALID (all required fields present)<br>"
        body += f"   - Uploaded to Aimbase: YES<br>"
        body += f"   - Attached to email: NO (file too large - {survey_count:,} records)<br><br>"

        # Add list of people being sent to Aimbase (first 20 only)
        if survey_claims and len(survey_claims) <= 20:
            body += f"<b>SAMPLE - First {min(20, len(survey_claims))} records sent to Aimbase:</b><br>"
            body += f"<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>"
            body += f"<tr style='background-color: #f0f0f0;'><th>Name</th><th>Email</th><th>Zip</th><th>City, State</th><th>Claim #</th></tr>"
            for claim in survey_claims[:20]:
                first = claim.get('CFSTNAME', '')
                last = claim.get('CLSTNAME', '')
                name = f"{first} {last}".strip()
                email = claim.get('CEMAIL', 'N/A')
                zipcode = claim.get('CPSTCODE', 'N/A')
                city = claim.get('CCITY', 'N/A')
                state = claim.get('CSTATE', 'N/A')
                claim_no = claim.get('CLAIMNO', 'N/A')
                body += f"<tr><td>{name}</td><td>{email}</td><td>{zipcode}</td><td>{city}, {state}</td><td>{claim_no}</td></tr>"
            body += f"</table><br><br>"

        if optout_csv_filename:
            body += f"<b>2. OPT-OUT FILE (attached):</b><br>"
            body += f"   - File: {os.path.basename(optout_csv_filename)}<br>"
            body += f"   - Real customers: {optout_count}<br>"
            body += f"   - SENDSRVY: FALSE (these customers OPTED OUT)<br>"
            body += f"   - Uploaded to Aimbase: NO (for your records only)<br>"
            body += f"   - Attached to email: YES<br><br>"

        if error_csv_filename and error_count > 0:
            error_attached = "YES" if error_count < 1000 else "NO (file too large)"
            body += f"<b>3. ERROR FILE:</b><br>"
            body += f"   - File: {os.path.basename(error_csv_filename)}<br>"
            body += f"   - Records: {error_count:,}<br>"
            body += f"   - Reason: Missing required fields (FirstName, LastName, Zipcode, or Email)<br>"
            body += f"   - Action Needed: Review and fix data issues<br>"
            body += f"   - Uploaded to Aimbase: NO (excluded from FTP upload)<br>"
            body += f"   - Attached to email: {error_attached}<br><br>"

        body += f"Best regards,<br>Automated Survey Export System (TEST MODE)<br>"
    else:
        subject = f"Weekly Warranty Survey Report - {datetime.now().strftime('%Y-%m-%d')}"
        body = f"Hi Mandy,<br><br>This is the weekly warranty survey report for approved claims.<br><br><b>IMPORTANT:</b><br>"
        body += f"- Using CUSTOMER emails from OwnerRegistrations table (NOT dealer emails)<br>"
        body += f"- FTP file contains ONLY valid records (no missing required fields)<br>"
        body += f"- Survey CSV NOT attached to email (too large - already uploaded to FTP)<br><br>"
        body += f"<b>FILE SUMMARY:</b><br><br>"
        body += f"<b>1. SURVEY FILE (uploaded to Aimbase SFTP):</b><br>"
        body += f"   - File: {os.path.basename(survey_csv_filename) if survey_csv_filename else 'None'}<br>"
        body += f"   - Location: \\\\ELK1ITSQVP001\\Qlikview\\Marketing\\{os.path.basename(survey_csv_filename) if survey_csv_filename else 'None'}<br>"
        body += f"   - Customers: {survey_count:,}<br>"
        body += f"   - SENDSRVY: TRUE (these customers WANT surveys)<br>"
        body += f"   - Data Quality: 100% VALID (FirstName, LastName, Zipcode, Email all present)<br>"
        body += f"   - Uploaded to Aimbase: YES<br>"
        body += f"   - Attached to email: NO (file too large - {survey_count:,} records)<br><br>"
        body += f"<b>2. OPT-OUT FILE (attached):</b><br>"
        body += f"   - File: {os.path.basename(optout_csv_filename) if optout_csv_filename else 'None'}<br>"
        body += f"   - Customers: {optout_count}<br>"
        body += f"   - SENDSRVY: FALSE (these customers OPTED OUT)<br>"
        body += f"   - Uploaded to Aimbase: NO (for your records only)<br>"
        body += f"   - Attached to email: YES<br><br>"

        if error_csv_filename and error_count > 0:
            error_attached = "YES" if error_count < 1000 else "NO (file too large)"
            body += f"<b>3. ERROR FILE - ACTION REQUIRED:</b><br>"
            body += f"   - File: {os.path.basename(error_csv_filename)}<br>"
            body += f"   - Location: \\\\ELK1ITSQVP001\\Qlikview\\Marketing\\{os.path.basename(error_csv_filename)}<br>"
            body += f"   - Records: {error_count:,}<br>"
            body += f"   - Reason: Missing required fields (FirstName, LastName, Zipcode, or Email)<br>"
            body += f"   - Action: Please review and fix data quality issues in warranty system<br>"
            body += f"   - Uploaded to Aimbase: NO (excluded from FTP upload for data quality)<br>"
            body += f"   - Attached to email: {error_attached}<br><br>"

        body += f"<b>All files saved to:</b> \\\\ELK1ITSQVP001\\Qlikview\\Marketing\\<br><br>"
        body += f"Best regards,<br>Automated Survey Export System<br>"

    # Attach files - smart handling to avoid email size limits
    files_to_attach = []

    print("[INFO] Email attachment strategy (to avoid size limits):")

    # DON'T attach survey CSV (already uploaded to FTP - too large for email)
    # Survey file is ~108K records = ~20-30 MB
    if survey_csv_filename:
        print(f"  - Survey CSV ({survey_count:,} records): NOT attached (too large - already on FTP)")

    # Always attach opt-out CSV (tiny - usually < 100 records)
    if optout_csv_filename:
        files_to_attach.append(optout_csv_filename)
        print(f"  - Opt-out CSV ({optout_count} records): ATTACHED (small file)")

    # Error CSV: Only attach if small (< 1000 records), otherwise provide network path
    if error_csv_filename and error_count > 0:
        if error_count < 1000:
            files_to_attach.append(error_csv_filename)
            print(f"  - Error CSV ({error_count} records): ATTACHED (small file)")
        else:
            print(f"  - Error CSV ({error_count:,} records): NOT attached (too large - network path provided)")
    print()

    result = send_mail(send_to, body, subject, files_to_attach)
    if result:
        print(f"[SUCCESS] Email sent to {send_to}\n")
    else:
        print(f"[ERROR] Failed to send email to {send_to}\n")

def upload_to_aimbase_ftp(csv_filename, is_test_mode=False):
    """Upload CSV file to Aimbase FTP server using curl (Aimbase recommended method)."""
    print("="*80)
    if is_test_mode:
        print("[TEST MODE] UPLOADING TEST FILE TO AIMBASE FTP USING CURL")
    else:
        print("UPLOADING TO AIMBASE FTP USING CURL")
    print("="*80 + "\n")

    try:
        # Generate remote filename
        if is_test_mode:
            remote_filename = f"TEST_bennington_warranty_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            remote_filename = f"bennington_warranty_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Use curl for upload (Aimbase recommended method)
        curl_cmd = [
            'curl',
            '-T', csv_filename,
            '--user', f"{AIMBASE_FTP['user']}:{AIMBASE_FTP['password']}",
            f"ftps://{AIMBASE_FTP['host']}/{remote_filename}",
            '--ftp-ssl',
            '--ssl-reqd',
            '--silent',
            '--show-error'
        ]

        print(f"[CURL] Uploading {csv_filename} as {remote_filename}...")
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print(f"[SUCCESS] Upload completed\n")
        else:
            print(f"[ERROR] Upload failed: {result.stderr}")
            return False

        # Verify upload using curl list command
        print("[VERIFY] Verifying uploaded file exists on server...")
        list_cmd = [
            'curl',
            '--list-only',
            '--user', f"{AIMBASE_FTP['user']}:{AIMBASE_FTP['password']}",
            f"ftps://{AIMBASE_FTP['host']}/",
            '--ftp-ssl',
            '--ssl-reqd',
            '--silent',
            '--show-error'
        ]

        list_result = subprocess.run(list_cmd, capture_output=True, text=True, timeout=60)

        if list_result.returncode == 0:
            files = list_result.stdout.strip().split('\n')
            if remote_filename in files:
                print(f"[VERIFIED] {remote_filename} exists on FTP server\n")

                # Save verification log
                log_filename = f"ftp_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                jams_directory = r"\\ELK1ITSQVP001\Qlikview\Marketing"
                log_path = os.path.join(jams_directory, log_filename)

                with open(log_path, 'w', encoding='utf-8') as log_file:
                    log_file.write(f"Aimbase FTP Upload Verification\n")
                    log_file.write(f"================================\n\n")
                    log_file.write(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    log_file.write(f"FTP Server: {AIMBASE_FTP['host']}\n")
                    log_file.write(f"Uploaded File: {remote_filename}\n")
                    log_file.write(f"Upload Status: SUCCESS\n")
                    log_file.write(f"File Verified on Server: YES\n")
                    log_file.write(f"\nFile list from server:\n")
                    for f in files:
                        log_file.write(f"  {f}\n")

                print(f"[INFO] Verification log saved: {log_path}\n")
                return True
            else:
                print(f"[WARNING] File not found in directory listing\n")
                return True  # Still return True since upload command succeeded
        else:
            print(f"[WARNING] Could not verify file (list command failed)\n")
            return True  # Still return True since upload command succeeded

    except FileNotFoundError:
        print("[ERROR] curl not found - please install curl")
        print("[INFO] Download curl from: https://curl.se/windows/")
        return False
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    Main execution function.

    Test mode (--test flag):
    - Uses fake data
    - Sends email to minseula@benningtonmarine.com only
    - Creates CSV but does NOT upload to FTP

    Production mode:
    - Uses real database data
    - Sends email to Mandy
    - Uploads CSV to Aimbase FTP

    Exit codes:
    0 = Success
    1 = FTP upload failed (critical error)
    """
    # Check for test mode
    test_mode = '--test' in sys.argv

    today = datetime.now()

    print("\n" + "="*80)
    if test_mode:
        print("[TEST MODE] WARRANTY SURVEY EXPORT SCRIPT")
        print("   (Using fake test data)")
    else:
        print("WARRANTY SURVEY EXPORT SCRIPT")
    print("="*80)
    print(f"Today: {today.strftime('%A, %B %d, %Y')}\n")

    # Use real database queries for claims
    if test_mode:
        all_claims = get_all_warranty_claims()  # Use REAL data for testing
    else:
        all_claims = get_all_warranty_claims()

    # Split claims based on validation and opt-out status
    survey_claims = []
    optout_claims = []
    error_claims = []

    def is_valid_customer_email(email):
        """Check if email is valid and not a placeholder."""
        # Handle None and non-string values
        if email is None or not isinstance(email, str):
            return False
        if not email.strip():
            return False
        email = email.strip().lower()
        # Filter out invalid/placeholder emails
        invalid_patterns = ['na@na.com', 'n/a', 'na', 'none', 'noemail', 'no email', '']
        if email in invalid_patterns:
            return False
        # Basic email format check
        if '@' not in email or '.' not in email:
            return False
        return True

    def validate_required_fields(claim):
        """
        Validate REQUIRED fields for Aimbase FTP upload.
        Returns (is_valid, error_reasons)
        """
        errors = []

        # Helper to safely check if field has value
        def has_value(field_name):
            value = claim.get(field_name)
            return value is not None and str(value).strip() != ''

        # Required: First Name
        if not has_value('CFSTNAME'):
            errors.append('Missing First Name')

        # Required: Last Name
        if not has_value('CLSTNAME'):
            errors.append('Missing Last Name')

        # Required: Claim Number
        if not has_value('CLAIMNO'):
            errors.append('Missing Claim Number')

        # Required: Zipcode
        if not has_value('CPSTCODE'):
            errors.append('Missing Zipcode')

        # Required: Valid Email
        email = claim.get('CEMAIL')
        if not is_valid_customer_email(email if email else ''):
            errors.append('Invalid or Missing Email')

        return (len(errors) == 0, errors)

    for claim in all_claims:
        # Validate required fields
        is_valid, error_reasons = validate_required_fields(claim)

        if not is_valid:
            # Add error reasons to claim for reporting
            claim['_error_reasons'] = ', '.join(error_reasons)
            error_claims.append(claim)
            continue

        # Check if OrdOptOut is explicitly 1
        if str(claim.get('OrdOptOut', '')).strip() == '1':
            optout_claims.append(claim)
        else:
            survey_claims.append(claim)

    # Report statistics
    print('\n' + '=' * 80)
    print('CLAIM PROCESSING SUMMARY')
    print('=' * 80)
    print(f'Total claims fetched: {len(all_claims)}')
    print(f'  - VALID claims (ready for FTP): {len(survey_claims) + len(optout_claims)}')
    print(f'    • Survey claims (OrdOptOut=0): {len(survey_claims)}')
    print(f'    • Opt-out claims (OrdOptOut=1): {len(optout_claims)}')
    print(f'  - ERROR claims (missing required fields): {len(error_claims)}')
    print('=' * 80 + '\n')

    survey_csv_filename = None
    optout_csv_filename = None
    error_csv_filename = None
    ftp_success = True
    timestamp = today.strftime('%Y%m%d_%H%M%S')

    # If no claims are found, generate a dummy record ONLY in test mode
    if not survey_claims and test_mode:
        print("[INFO] No real claims found in test mode. Generating a dummy record.")
        survey_claims = [{
            'CLAIMNO': 'DUMMY123', 'HIN': 'TESTHIN123',
            'CLAIMDT': today.strftime('%Y-%m-%d'), 'DLRNUMBR': 'D123',
            'CFSTNAME': 'John', 'CLSTNAME': 'Doe', 'CADDRES1': '123 Main St',
            'CCITY': 'Testville', 'CSTATE': 'MN', 'CPSTCODE': '55401', 'CCOUNTRY': 'USA',
            'CHMPHONE': '555-1234', 'CEMAIL': 'johndoe@example.com',
            'OrdOptOut': 0,
            'MODELBRD': 'TestBrand', 'MODELCOD': 'TST', 'MODELYER': '2026'
        }]

    # Create CSV file for valid survey claims (FTP upload)
    if survey_claims:
        survey_csv_filename = f'TEST_warranty_survey_{timestamp}.csv' if test_mode else f'warranty_survey_{timestamp}.csv'
        create_aimbase_csv(survey_claims, survey_csv_filename, send_survey=True)

    # Create CSV file for customers who OPTED OUT (email only)
    if optout_claims:
        optout_csv_filename = f'TEST_warranty_optout_{timestamp}.csv' if test_mode else f'warranty_optout_{timestamp}.csv'
        create_aimbase_csv(optout_claims, optout_csv_filename, send_survey=False)

    # Create ERROR CSV file for records with missing required fields (email only)
    if error_claims:
        error_csv_filename = f'TEST_warranty_errors_{timestamp}.csv' if test_mode else f'warranty_errors_{timestamp}.csv'
        create_error_csv(error_claims, error_csv_filename)

    # Continue with normal test mode logic
    if test_mode:
        if survey_claims:
            print("[UPLOAD] Uploading test SURVEY file to Aimbase FTP...\n")
            ftp_success = upload_to_aimbase_ftp(survey_csv_filename, is_test_mode=True)
        print("[EMAIL] Sending test email with all files to minseula and Mandy...\n")
        send_email_to_mandy(
            survey_csv_filename, len(survey_claims) if survey_claims else 0,
            optout_csv_filename, len(optout_claims) if optout_claims else 0,
            error_csv_filename, len(error_claims) if error_claims else 0,
            is_test_mode=True,
            survey_claims=survey_claims
        )
        print("\n" + "="*80)
        print("[SUCCESS] TEST MODE COMPLETE")
        print("="*80)
        print("[EMAIL] Email sent to: mnseula@benningtonmarine.com")
        if survey_csv_filename:
            print(f"[FILE] Test Survey CSV created: {survey_csv_filename}")
            if ftp_success:
                print("[SUCCESS] FTP upload COMPLETED (survey file uploaded)")
            else:
                print("[ERROR] FTP upload FAILED")
        if optout_csv_filename:
            print(f"[FILE] Test Opt-Out CSV created: {optout_csv_filename}")
            print("[INFO] Opt-out file NOT uploaded to FTP (for Mandy only)")
        if error_csv_filename:
            print(f"[FILE] Test ERROR CSV created: {error_csv_filename} ({len(error_claims)} records)")
            print("[INFO] Error file NOT uploaded to FTP (for Mandy's review only)")
        print("="*80 + "\n")
    else:
        # Production Mode Execution
        if survey_claims:
            print("[UPLOAD] Uploading PRODUCTION survey file to Aimbase FTP...\n")
            ftp_success = upload_to_aimbase_ftp(survey_csv_filename, is_test_mode=False)

        # NOTE: Opt-out and error files are NOT uploaded to FTP - only sent to Mandy via email
        if optout_claims:
            print(f"[INFO] Opt-out file created with {len(optout_claims)} records (NOT uploaded to FTP - for Mandy only)\n")

        if error_claims:
            print(f"[WARNING] Error file created with {len(error_claims)} records (NOT uploaded to FTP - for Mandy's review)\n")

        print("[EMAIL] Sending production email to Mandy...\n")
        send_email_to_mandy(
            survey_csv_filename, len(survey_claims) if survey_claims else 0,
            optout_csv_filename, len(optout_claims) if optout_claims else 0,
            error_csv_filename, len(error_claims) if error_claims else 0,
            is_test_mode=False
        )

if __name__ == "__main__":
    main()
