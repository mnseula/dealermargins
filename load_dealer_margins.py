"""
Load Dealer Margins from Infor CPQ API to MySQL Database

This script:
1. Fetches dealer margin data from CPQ API
2. Loads into Dealers and DealerMargins tables
3. Handles margin configurations per dealer-series combination

Designed to run via JAMS scheduler for automated data synchronization.
"""

import requests
import json
import urllib3
import time
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Optional
from datetime import datetime, date

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== CONFIGURATION ====================

# TRN credentials for dealer margins API
CLIENT_ID_TRN = "QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8"
CLIENT_SECRET_TRN = "CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAnyArDH3ZebqYTKAoMq37_aQ"
TOKEN_ENDPOINT_TRN = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2"
SERVICE_KEY_TRN = "QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw"
SERVICE_SECRET_TRN = "pAze3yNlj8r6dbcTv-Fn8AiGvhIcs2x-yEgJaMiuoraAJdkFB6iLQFKaFQCP_17KZIYoroUoF_CeEoslHWlXug"

# Dealer Margins API Endpoint
DEALER_MARGIN_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities/C_GD_DealerMargin"

# Database Configuration
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

# Settings
REQUEST_TIMEOUT = 120
MAX_RETRIES = 3
MODEL_YEAR = 2026

# ==================== TOKEN MANAGEMENT ====================

def get_token() -> Optional[str]:
    """Get OAuth token for TRN environment"""
    payload = {
        'grant_type': 'password',
        'client_id': CLIENT_ID_TRN,
        'client_secret': CLIENT_SECRET_TRN,
        'username': SERVICE_KEY_TRN,
        'password': SERVICE_SECRET_TRN
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(TOKEN_ENDPOINT_TRN, data=payload, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            return response.json().get('access_token')
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Token attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(attempt * 5)

    return None

# ==================== FETCH DEALER MARGINS ====================

def fetch_dealer_margins(token: str) -> List[Dict]:
    """Fetch all dealer margins from API"""
    print("\n📋 Fetching dealer margins from API...")

    try:
        headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
        response = requests.get(DEALER_MARGIN_ENDPOINT, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
        response.raise_for_status()

        data = response.json()
        margins = data.get('items', [])

        print(f"✅ Fetched {len(margins)} dealer margin records")
        return margins

    except Exception as e:
        print(f"❌ Error fetching dealer margins: {e}")
        return []

# ==================== LOAD TO DATABASE ====================

def load_dealer_margins_to_db(cursor, margins: List[Dict]):
    """Load dealer margins into database"""
    print(f"\n💾 Loading {len(margins)} dealer margin records to database...")

    dealers_loaded = 0
    margins_loaded = 0
    errors = 0

    for margin_record in margins:
        try:
            dealer_id = margin_record.get('C_DealerId')
            dealer_name = margin_record.get('C_DealerName')
            series_id = margin_record.get('C_Series')

            if not dealer_id or not dealer_name or not series_id:
                print(f"⚠️  Skipping record - missing required fields")
                errors += 1
                continue

            # Insert/update dealer
            cursor.execute(
                """INSERT INTO Dealers (dealer_id, dealer_name, active)
                   VALUES (%s, %s, TRUE)
                   ON DUPLICATE KEY UPDATE
                   dealer_name = VALUES(dealer_name),
                   updated_at = NOW()""",
                (dealer_id, dealer_name)
            )
            dealers_loaded += 1

            # Ensure series exists (may already be loaded from CPQ data)
            cursor.execute(
                """INSERT INTO Series (series_id, series_name, active)
                   VALUES (%s, %s, TRUE)
                   ON DUPLICATE KEY UPDATE updated_at = NOW()""",
                (series_id, series_id)
            )

            # Get margin values
            base_boat = margin_record.get('C_BaseBoat', 0)
            engine = margin_record.get('C_Engine', 0)
            options = margin_record.get('C_Options', 0)
            freight = margin_record.get('C_Freight', 0)
            prep = margin_record.get('C_Prep', 0)
            volume = margin_record.get('C_Volume', 0)
            enabled = margin_record.get('C_Enabled', False)

            # Check if margins already exist with same values
            cursor.execute(
                """SELECT margin_id FROM DealerMargins
                   WHERE dealer_id = %s AND series_id = %s AND end_date IS NULL
                   AND base_boat_margin = %s AND engine_margin = %s
                   AND options_margin = %s AND freight_margin = %s
                   AND prep_margin = %s AND volume_discount = %s""",
                (dealer_id, series_id, base_boat, engine, options, freight, prep, volume)
            )

            if cursor.fetchone():
                # Margins haven't changed, just update enabled status if needed
                cursor.execute(
                    """UPDATE DealerMargins SET enabled = %s, updated_at = NOW()
                       WHERE dealer_id = %s AND series_id = %s AND end_date IS NULL""",
                    (enabled, dealer_id, series_id)
                )
            else:
                # Margins changed - end old record and insert new
                effective_date = date.today()

                # End current active margins
                cursor.execute(
                    """UPDATE DealerMargins
                       SET end_date = DATE_SUB(%s, INTERVAL 1 DAY)
                       WHERE dealer_id = %s AND series_id = %s AND end_date IS NULL""",
                    (effective_date, dealer_id, series_id)
                )

                # Insert new margins
                cursor.execute(
                    """INSERT INTO DealerMargins (
                       dealer_id, series_id,
                       base_boat_margin, engine_margin, options_margin,
                       freight_margin, prep_margin, volume_discount,
                       enabled, effective_date, year
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        dealer_id, series_id,
                        base_boat, engine, options,
                        freight, prep, volume,
                        enabled, effective_date, MODEL_YEAR
                    )
                )

            margins_loaded += 1

        except Exception as e:
            errors += 1
            dealer_info = f"{margin_record.get('C_DealerName', 'unknown')} - {margin_record.get('C_Series', 'unknown')}"
            print(f"⚠️  Error loading dealer margin for {dealer_info}: {e}")

    print(f"✅ Loaded {dealers_loaded} dealers, {margins_loaded} margin records, {errors} errors")
    return dealers_loaded, margins_loaded, errors

# ==================== MAIN EXECUTION ====================

def main():
    """Main execution - load dealer margins"""
    print("=" * 80)
    print("LOAD DEALER MARGINS TO DATABASE")
    print("=" * 80)
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Year: {MODEL_YEAR}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    start_time = time.time()

    # Get token
    print("\n🔐 Obtaining API token...")
    token = get_token()

    if not token:
        print("❌ Failed to obtain API token. Exiting.")
        return

    print("✅ Token obtained successfully")

    # Fetch dealer margins
    margins = fetch_dealer_margins(token)

    if not margins:
        print("❌ No dealer margins fetched. Exiting.")
        return

    # Connect to database
    try:
        print(f"\n🔌 Connecting to database...")
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✅ Connected to database")

        # Load dealer margins
        dealers_count, margins_count, errors_count = load_dealer_margins_to_db(cursor, margins)

        # Commit changes
        connection.commit()

        # Get summary statistics
        cursor.execute("SELECT COUNT(*) FROM Dealers WHERE active = TRUE")
        total_dealers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM DealerMargins WHERE end_date IS NULL")
        total_active_margins = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT series_id) FROM DealerMargins WHERE end_date IS NULL")
        total_series = cursor.fetchone()[0]

        # Close database connection
        cursor.close()
        connection.close()
        print("\n✅ Database connection closed")

    except Error as e:
        print(f"\n❌ Database error: {e}")
        return

    # Summary
    elapsed_time = time.time() - start_time

    print("\n" + "=" * 80)
    print("LOAD COMPLETE - SUMMARY")
    print("=" * 80)
    print(f"✅ Dealers processed:        {dealers_count} ({errors_count} errors)")
    print(f"✅ Margin records loaded:    {margins_count}")
    print(f"📊 Total active dealers:     {total_dealers}")
    print(f"📊 Total active margins:     {total_active_margins}")
    print(f"📊 Series covered:           {total_series}")
    print(f"⏱️  Total execution time:    {elapsed_time:.1f} seconds")
    print(f"💾 Database:                 {DB_CONFIG['database']}")
    print(f"📅 Completed:                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
