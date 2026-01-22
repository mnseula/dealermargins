"""
Load Complete CPQ Data from Infor APIs to MySQL Database

This script:
1. Fetches model prices from OptionList API → Loads to Series, Models, ModelPricing
2. Fetches performance data from Matrix APIs → Loads to PerformancePackages, ModelPerformance
3. Fetches standard features from Matrix APIs → Loads to StandardFeatures, ModelStandardFeatures
4. Saves backup JSON files for all data

Designed to run via JAMS scheduler for automated data synchronization.
"""

import requests
import json
import urllib3
import time
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Optional, Set
from datetime import datetime, date
from pathlib import Path

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== CONFIGURATION ====================

# API Credentials - PRD for pricing, TRN for performance/standards
CLIENT_ID_PRD = "QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo"
CLIENT_SECRET_PRD = "4O7OIZ64sukP1N6YeGZ6IpzsFTG4T6RFkcTZgq6ZwAetb4VoNOOJ1qMkGQAlvnOqqcgaZDlXKux6YEQNvoZQgg"
TOKEN_ENDPOINT_PRD = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2"
SERVICE_KEY_PRD = "QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9xuXKp_iYp49_M7JuB7UaEo0xjWDqTAE1Q15rQhxojw"
SERVICE_SECRET_PRD = "IZq8wArFnHi4rESTZ-3SQT5zMgiCQfre8aLM6KirsVmvBhXmGDZS_4TXvCZlD40AjpXX6igL7y8A3svCHV-glg"

CLIENT_ID_TRN = "QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8"
CLIENT_SECRET_TRN = "CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAnyArDH3ZebqYTKAoMq37_aQ"
TOKEN_ENDPOINT_TRN = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2"
SERVICE_KEY_TRN = "QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw"
SERVICE_SECRET_TRN = "pAze3yNlj8r6dbcTv-Fn8AiGvhIcs2x-yEgJaMiuoraAJdkFB6iLQFKaFQCP_17KZIYoroUoF_CeEoslHWlXug"

# API Endpoints
OPTION_LIST_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/DataImport/QA2FNBZCKUAUH7QB_PRD/v1/OptionLists/bb38d84e-6493-40c7-b282-9cb9c0df26ae/values"
PERFORMANCE_MATRIX_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/{series}_PerformanceData_2026/values"
STANDARDS_MATRIX_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/{series}_ModelStandards_2026/values"

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
OUTPUT_DIR = Path("cpq_data_backups")

# ==================== TOKEN MANAGEMENT ====================

def get_token(environment: str = "PRD") -> Optional[str]:
    """Get OAuth token for specified environment"""
    if environment == "PRD":
        token_endpoint = TOKEN_ENDPOINT_PRD
        payload = {
            'grant_type': 'password',
            'client_id': CLIENT_ID_PRD,
            'client_secret': CLIENT_SECRET_PRD,
            'username': SERVICE_KEY_PRD,
            'password': SERVICE_SECRET_PRD
        }
    else:  # TRN
        token_endpoint = TOKEN_ENDPOINT_TRN
        payload = {
            'grant_type': 'password',
            'client_id': CLIENT_ID_TRN,
            'client_secret': CLIENT_SECRET_TRN,
            'username': SERVICE_KEY_TRN,
            'password': SERVICE_SECRET_TRN
        }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(token_endpoint, data=payload, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            return response.json().get('access_token')
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Token attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(attempt * 5)

    return None

# ==================== STEP 1: MODEL PRICES ====================

def fetch_model_prices(token: str) -> List[Dict]:
    """Fetch all models with pricing from OptionList API"""
    print("\n📋 Fetching model prices from OptionList API...")

    try:
        headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
        response = requests.get(OPTION_LIST_ENDPOINT, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
        response.raise_for_status()

        data = response.json()
        models = []

        if 'result' in data and isinstance(data['result'], list):
            for item in data['result']:
                if 'value' in item:
                    custom_props = item.get('customProperties', {})
                    models.append({
                        'model_id': str(item['value']).strip(),
                        'series': custom_props.get('Series', ''),
                        'parent_series': custom_props.get('ParentSeries', ''),
                        'msrp': custom_props.get('Price', 0),
                        'floorplan': custom_props.get('Floorplan', ''),
                        'floorplan_desc': custom_props.get('FloorplanDesc', ''),
                        'length': custom_props.get('Length', ''),
                        'length_str': custom_props.get('LengthStr', ''),
                        'beam_length': custom_props.get('BeamLength', 0),
                        'beam_str': custom_props.get('BeamStr', ''),
                        'loa': custom_props.get('LOA', 0),
                        'loa_str': custom_props.get('LOAStr', ''),
                        'seats': custom_props.get('Seats', 0),
                        'visible': item.get('visible', True),
                        'image_link': custom_props.get('ImageLink', ''),
                        'has_arch': custom_props.get('Arch', False),
                        'has_windshield': custom_props.get('Windshield', False),
                        'twin_engine': custom_props.get('TwinEngine', False)
                    })

        print(f"✅ Fetched {len(models)} models with pricing")
        return models

    except Exception as e:
        print(f"❌ Error fetching model prices: {e}")
        return []

def load_model_prices_to_db(cursor, models: List[Dict]):
    """Load model prices into database"""
    print(f"\n💾 Loading {len(models)} models to database...")

    success = 0
    errors = 0

    for model in models:
        try:
            # Insert/update series
            if model['series']:
                cursor.execute(
                    """INSERT INTO Series (series_id, series_name, parent_series, active)
                       VALUES (%s, %s, %s, TRUE)
                       ON DUPLICATE KEY UPDATE parent_series = VALUES(parent_series), updated_at = NOW()""",
                    (model['series'], model['series'], model['parent_series'])
                )

            # Insert/update model
            cursor.execute(
                """INSERT INTO Models (
                   model_id, series_id, floorplan_code, floorplan_desc,
                   length_feet, length_str, beam_length, beam_str,
                   loa, loa_str, seats, visible, image_link,
                   has_arch, has_windshield, twin_engine
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                   series_id = VALUES(series_id),
                   floorplan_code = VALUES(floorplan_code),
                   floorplan_desc = VALUES(floorplan_desc),
                   length_feet = VALUES(length_feet),
                   length_str = VALUES(length_str),
                   beam_length = VALUES(beam_length),
                   beam_str = VALUES(beam_str),
                   loa = VALUES(loa),
                   loa_str = VALUES(loa_str),
                   seats = VALUES(seats),
                   visible = VALUES(visible),
                   image_link = VALUES(image_link),
                   has_arch = VALUES(has_arch),
                   has_windshield = VALUES(has_windshield),
                   twin_engine = VALUES(twin_engine),
                   updated_at = NOW()""",
                (
                    model['model_id'], model['series'], model['floorplan'], model['floorplan_desc'],
                    model['length'] if model['length'] else None, model['length_str'],
                    model['beam_length'] if model['beam_length'] else None, model['beam_str'],
                    model['loa'] if model['loa'] else None, model['loa_str'],
                    model['seats'] if model['seats'] else None, model['visible'], model['image_link'],
                    model['has_arch'], model['has_windshield'], model['twin_engine']
                )
            )

            # Insert/update pricing (only if MSRP > 0)
            if model['msrp'] > 0:
                # Check if price changed
                cursor.execute(
                    "SELECT pricing_id FROM ModelPricing WHERE model_id = %s AND end_date IS NULL AND msrp = %s",
                    (model['model_id'], model['msrp'])
                )
                if not cursor.fetchone():
                    # Price changed - end old pricing and insert new
                    effective_date = date.today()
                    cursor.execute(
                        "UPDATE ModelPricing SET end_date = DATE_SUB(%s, INTERVAL 1 DAY) WHERE model_id = %s AND end_date IS NULL",
                        (effective_date, model['model_id'])
                    )
                    cursor.execute(
                        "INSERT INTO ModelPricing (model_id, msrp, effective_date, year) VALUES (%s, %s, %s, %s)",
                        (model['model_id'], model['msrp'], effective_date, MODEL_YEAR)
                    )

            success += 1

        except Exception as e:
            errors += 1
            print(f"⚠️  Error loading model {model.get('model_id', 'unknown')}: {e}")

    print(f"✅ Loaded {success} models, {errors} errors")
    return success, errors

# ==================== STEP 2: PERFORMANCE DATA ====================

def fetch_performance_data(token: str, series: str) -> List[Dict]:
    """Fetch performance data for a series"""
    try:
        endpoint = PERFORMANCE_MATRIX_ENDPOINT.format(series=series)
        headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
        response = requests.get(endpoint, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
        response.raise_for_status()

        data = response.json()
        details = data.get('result', {}).get('details', [])
        return details

    except Exception as e:
        print(f"⚠️  Error fetching performance for {series}: {e}")
        return []

def load_performance_to_db(cursor, series: str, perf_data: List[Dict]):
    """Load performance data to database"""
    success = 0
    errors = 0

    for record in perf_data:
        try:
            model_id = record.get('model')
            perf_package = record.get('perfPack')

            if not model_id or not perf_package:
                continue

            # Insert/update performance package
            cursor.execute(
                """INSERT INTO PerformancePackages (perf_package_id, package_name, active)
                   VALUES (%s, %s, TRUE)
                   ON DUPLICATE KEY UPDATE package_name = VALUES(package_name), updated_at = NOW()""",
                (perf_package, perf_package)
            )

            # Insert/update model performance
            cursor.execute(
                """INSERT INTO ModelPerformance (
                   model_id, perf_package_id, year,
                   max_hp, no_of_tubes, person_capacity, hull_weight,
                   pontoon_gauge, transom, tube_height, tube_center_to_center,
                   max_width, fuel_capacity,
                   mech_str_cable_no_ead, mech_str_cable_ead, hyd_str_hose,
                   ctrl_cable_no_ead, ctrl_cable_ead,
                   brp_harness_len, honda_harness_len, merc_harness_len,
                   yamaha_harness_len, suzuki_harness_len, pow_assist_hose,
                   tube_length_str, tube_length_num, deck_length_str, deck_length_num
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                   max_hp = VALUES(max_hp),
                   no_of_tubes = VALUES(no_of_tubes),
                   person_capacity = VALUES(person_capacity),
                   hull_weight = VALUES(hull_weight),
                   pontoon_gauge = VALUES(pontoon_gauge),
                   transom = VALUES(transom),
                   tube_height = VALUES(tube_height),
                   tube_center_to_center = VALUES(tube_center_to_center),
                   max_width = VALUES(max_width),
                   fuel_capacity = VALUES(fuel_capacity),
                   updated_at = NOW()""",
                (
                    model_id, perf_package, MODEL_YEAR,
                    record.get('MaxHP'), record.get('NoOfTubes'), record.get('PersonCapacity'), record.get('HullWeight'),
                    record.get('PontoonGauge'), record.get('Transom'), record.get('TubeHeight'), record.get('TubeCentertoCenter'),
                    record.get('MaxWidth'), record.get('FuelCapacity'),
                    record.get('MechStrCableNoEAD'), record.get('MechStrCableEAD'), record.get('HydStrHose'),
                    record.get('CtrlCableNoEAD'), record.get('CtrlCableEAD'),
                    record.get('BRPHarnessLen'), record.get('HondaHarnessLen'), record.get('MercHarnessLen'),
                    record.get('YamahaHarnessLen'), record.get('SuzukiHarnessLen'), record.get('PowAssistHose'),
                    record.get('TubeLengthStr'), record.get('TubeLengthNum'), record.get('DeckLengthStr'), record.get('DeckLengthNum')
                )
            )

            success += 1

        except Exception as e:
            errors += 1
            print(f"⚠️  Error loading performance record: {e}")

    return success, errors

# ==================== STEP 3: STANDARD FEATURES ====================

def fetch_standard_features(token: str, series: str) -> List[Dict]:
    """Fetch standard features for a series"""
    try:
        endpoint = STANDARDS_MATRIX_ENDPOINT.format(series=series)
        headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
        response = requests.get(endpoint, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
        response.raise_for_status()

        data = response.json()
        details = data.get('result', {}).get('details', [])
        return details

    except Exception as e:
        print(f"⚠️  Error fetching standards for {series}: {e}")
        return []

def load_standards_to_db(cursor, series: str, standards_data: List[Dict], all_model_ids: Set[str]):
    """Load standard features to database"""
    success = 0
    errors = 0

    for record in standards_data:
        try:
            area = record.get('Area', 'Other')
            description = record.get('Description', '')
            sort_order = record.get('Sort', 999)

            if not description:
                continue

            # Create a feature code (unique identifier) - sanitize for database
            feature_code = f"{series}_{area}_{description[:50]}"
            feature_code = feature_code.replace(' ', '_').replace(',', '').replace("'", '').replace('"', '').replace('/', '_')

            # Insert/update standard feature
            cursor.execute(
                """INSERT INTO StandardFeatures (feature_code, area, description, sort_order, active)
                   VALUES (%s, %s, %s, %s, TRUE)
                   ON DUPLICATE KEY UPDATE
                   area = VALUES(area),
                   description = VALUES(description),
                   sort_order = VALUES(sort_order),
                   updated_at = NOW()""",
                (feature_code, area, description, sort_order)
            )

            # Get the feature_id
            cursor.execute("SELECT feature_id FROM StandardFeatures WHERE feature_code = %s", (feature_code,))
            result = cursor.fetchone()

            if not result:
                print(f"⚠️  Feature not found after insert: {feature_code}")
                errors += 1
                continue

            feature_id = result[0]

            # Link to models where feature is standard (value = 'S')
            for model_id in all_model_ids:
                if model_id in record and record.get(model_id) == 'S':
                    cursor.execute(
                        """INSERT INTO ModelStandardFeatures (model_id, feature_id, year, is_standard)
                           VALUES (%s, %s, %s, TRUE)
                           ON DUPLICATE KEY UPDATE is_standard = TRUE, updated_at = NOW()""",
                        (model_id, feature_id, MODEL_YEAR)
                    )

            success += 1

        except Exception as e:
            errors += 1
            print(f"⚠️  Error loading standard feature '{description[:30]}': {e}")

    return success, errors

# ==================== MAIN EXECUTION ====================

def main():
    """Main execution - load all CPQ data"""
    print("=" * 80)
    print("LOAD COMPLETE CPQ DATA TO DATABASE")
    print("=" * 80)
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Year: {MODEL_YEAR}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    start_time = time.time()

    # Get tokens
    print("\n🔐 Obtaining API tokens...")
    token_prd = get_token("PRD")
    token_trn = get_token("TRN")

    if not token_prd or not token_trn:
        print("❌ Failed to obtain API tokens. Exiting.")
        return

    print("✅ Tokens obtained successfully")

    # STEP 1: Fetch and load model prices
    print("\n" + "=" * 80)
    print("STEP 1: MODEL PRICES, SERIES, AND MODELS")
    print("=" * 80)

    models = fetch_model_prices(token_prd)
    if not models:
        print("❌ No models fetched. Exiting.")
        return

    # Extract unique series
    unique_series = sorted(set(m['series'] for m in models if m['series']))
    print(f"📊 Found {len(unique_series)} unique series: {', '.join(unique_series)}")

    # Get all model IDs for later use
    all_model_ids = set(m['model_id'] for m in models)

    # Connect to database
    try:
        print(f"\n🔌 Connecting to database...")
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✅ Connected to database")

        # Load model prices
        models_success, models_errors = load_model_prices_to_db(cursor, models)
        connection.commit()

        # STEP 2: Fetch and load performance data
        print("\n" + "=" * 80)
        print("STEP 2: PERFORMANCE DATA")
        print("=" * 80)

        total_perf_success = 0
        total_perf_errors = 0

        for series in unique_series:
            print(f"\n📊 Processing series: {series}")
            perf_data = fetch_performance_data(token_trn, series)
            if perf_data:
                print(f"   Fetched {len(perf_data)} performance records")
                success, errors = load_performance_to_db(cursor, series, perf_data)
                total_perf_success += success
                total_perf_errors += errors
                connection.commit()

        print(f"\n✅ Performance data loaded: {total_perf_success} records, {total_perf_errors} errors")

        # STEP 3: Fetch and load standard features
        print("\n" + "=" * 80)
        print("STEP 3: STANDARD FEATURES")
        print("=" * 80)

        total_std_success = 0
        total_std_errors = 0

        for series in unique_series:
            print(f"\n📊 Processing series: {series}")
            standards_data = fetch_standard_features(token_trn, series)
            if standards_data:
                print(f"   Fetched {len(standards_data)} standard feature records")
                success, errors = load_standards_to_db(cursor, series, standards_data, all_model_ids)
                total_std_success += success
                total_std_errors += errors
                connection.commit()

        print(f"\n✅ Standard features loaded: {total_std_success} records, {total_std_errors} errors")

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
    print(f"✅ Models loaded:           {models_success} ({models_errors} errors)")
    print(f"✅ Performance records:     {total_perf_success} ({total_perf_errors} errors)")
    print(f"✅ Standard features:       {total_std_success} ({total_std_errors} errors)")
    print(f"⏱️  Total execution time:   {elapsed_time:.1f} seconds")
    print(f"💾 Database:                {DB_CONFIG['database']}")
    print(f"📅 Completed:               {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
