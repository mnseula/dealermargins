"""
Load Complete CPQ Data from Infor APIs to MySQL Database

This script:
1. Fetches model prices from OptionList API → Loads to Series, Models, ModelPricing
2. Fetches performance data from Matrix APIs → Loads to PerformancePackages, ModelPerformance
3. Fetches standard features from Matrix APIs → Loads to StandardFeatures, ModelStandardFeatures
4. Fetches dealer margins from API → Loads to Dealers, DealerMargins

Complete one-stop data loader for all CPQ tables.
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
import hashlib
import csv
import tempfile
import os

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== CONFIGURATION ====================

# API Credentials - All endpoints now use PRD environment
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
# Note: API endpoints use _2026 naming but contain 2025 model year data (model IDs with "25" prefix)
# All endpoints now use PRD environment
OPTION_LIST_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/DataImport/QA2FNBZCKUAUH7QB_PRD/v1/OptionLists/bb38d84e-6493-40c7-b282-9cb9c0df26ae/values"
PERFORMANCE_MATRIX_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/DataImport/v2/Matrices/{series}_PerformanceData_2026/values"
STANDARDS_MATRIX_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/DataImport/v2/Matrices/{series}_ModelStandards_2026/values"
DEALER_MARGIN_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities/C_GD_DealerMargin"

# Database Configuration
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'cpq',
    'allow_local_infile': True  # Required for LOAD DATA LOCAL INFILE (bulk loading)
}

# Settings
REQUEST_TIMEOUT = 120
MAX_RETRIES = 3
MODEL_YEAR = 2025  # Model IDs with "25" prefix = 2025 model year
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
    """Load performance data to database using CSV bulk loading"""
    print(f"  📝 Preparing performance data for {series}...")

    # Collect unique packages and performance records
    packages = set()
    perf_records = []

    for record in perf_data:
        model_id = record.get('model')
        perf_package = record.get('perfPack')

        if not model_id or not perf_package:
            continue

        packages.add(perf_package)
        perf_records.append((
            model_id, perf_package, MODEL_YEAR,
            record.get('MaxHP'), record.get('NoOfTubes'), record.get('PersonCapacity'), record.get('HullWeight'),
            record.get('PontoonGauge'), record.get('Transom'), record.get('TubeHeight'), record.get('TubeCentertoCenter'),
            record.get('MaxWidth'), record.get('FuelCapacity'),
            record.get('MechStrCableNoEAD'), record.get('MechStrCableEAD'), record.get('HydStrHose'),
            record.get('CtrlCableNoEAD'), record.get('CtrlCableEAD'),
            record.get('BRPHarnessLen'), record.get('HondaHarnessLen'), record.get('MercHarnessLen'),
            record.get('YamahaHarnessLen'), record.get('SuzukiHarnessLen'), record.get('PowAssistHose'),
            record.get('TubeLengthStr'), record.get('TubeLengthNum'), record.get('DeckLengthStr'), record.get('DeckLengthNum')
        ))

    if not perf_records:
        return 0, 0

    print(f"  📊 {len(packages)} packages, {len(perf_records)} performance records")

    # Write CSVs
    packages_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
    perf_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')

    try:
        # Write packages
        pkg_writer = csv.writer(packages_csv)
        for pkg in packages:
            pkg_writer.writerow([pkg, pkg, 1])
        packages_csv.close()

        # Write performance records
        perf_writer = csv.writer(perf_csv)
        for record in perf_records:
            perf_writer.writerow(record)
        perf_csv.close()

        # Create temp tables
        cursor.execute("CREATE TEMPORARY TABLE temp_packages (perf_package_id VARCHAR(50), package_name VARCHAR(100), active TINYINT(1))")
        cursor.execute("""CREATE TEMPORARY TABLE temp_perf (
            model_id VARCHAR(20), perf_package_id VARCHAR(50), year INT,
            max_hp DECIMAL(6,1), no_of_tubes DECIMAL(3,1), person_capacity VARCHAR(50), hull_weight DECIMAL(8,1),
            pontoon_gauge DECIMAL(4,2), transom VARCHAR(20), tube_height VARCHAR(20), tube_center_to_center VARCHAR(20),
            max_width VARCHAR(20), fuel_capacity VARCHAR(50),
            mech_str_cable_no_ead INT, mech_str_cable_ead INT, hyd_str_hose INT,
            ctrl_cable_no_ead INT, ctrl_cable_ead INT,
            brp_harness_len INT, honda_harness_len INT, merc_harness_len INT,
            yamaha_harness_len INT, suzuki_harness_len INT, pow_assist_hose INT,
            tube_length_str VARCHAR(20), tube_length_num DECIMAL(6,2), deck_length_str VARCHAR(20), deck_length_num DECIMAL(6,2)
        )""")

        # Bulk load
        print(f"  ⚡ Bulk loading performance packages...")
        cursor.execute(f"LOAD DATA LOCAL INFILE '{packages_csv.name}' INTO TABLE temp_packages FIELDS TERMINATED BY ',' LINES TERMINATED BY '\\n'")
        cursor.execute(f"LOAD DATA LOCAL INFILE '{perf_csv.name}' INTO TABLE temp_perf FIELDS TERMINATED BY ',' LINES TERMINATED BY '\\n'")

        # Insert with upsert
        cursor.execute("""
            INSERT INTO PerformancePackages (perf_package_id, package_name, active)
            SELECT perf_package_id, package_name, active FROM temp_packages
            ON DUPLICATE KEY UPDATE package_name = VALUES(package_name), updated_at = NOW()
        """)

        print(f"  ⚡ Bulk loading model performance...")
        cursor.execute("""
            INSERT INTO ModelPerformance (
                model_id, perf_package_id, year,
                max_hp, no_of_tubes, person_capacity, hull_weight,
                pontoon_gauge, transom, tube_height, tube_center_to_center,
                max_width, fuel_capacity,
                mech_str_cable_no_ead, mech_str_cable_ead, hyd_str_hose,
                ctrl_cable_no_ead, ctrl_cable_ead,
                brp_harness_len, honda_harness_len, merc_harness_len,
                yamaha_harness_len, suzuki_harness_len, pow_assist_hose,
                tube_length_str, tube_length_num, deck_length_str, deck_length_num
            )
            SELECT * FROM temp_perf
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
                updated_at = NOW()
        """)
        success = len(perf_records)

        # Cleanup
        cursor.execute("DROP TEMPORARY TABLE temp_packages")
        cursor.execute("DROP TEMPORARY TABLE temp_perf")

        print(f"  ✅ Loaded {success} performance records")
        return success, 0

    finally:
        os.unlink(packages_csv.name)
        os.unlink(perf_csv.name)

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
    """Load standard features to database using CSV bulk loading"""
    print(f"  📝 Preparing standard features for {series}...")

    # Collect features and model-feature links
    features = []
    model_features = []

    for record in standards_data:
        area = record.get('Area', 'Other')
        description = record.get('Description', '')
        sort_order = record.get('Sort', 999)

        if not description:
            continue

        # Create hash-based feature code
        hash_input = f"{series}_{area}_{description}".encode('utf-8')
        hash_hex = hashlib.md5(hash_input).hexdigest()[:12]
        feature_code = f"{series}_{hash_hex}"

        features.append((feature_code, area, description, sort_order, 1))  # active=1

        # Find models where this feature is standard (value = 'S')
        for model_id in all_model_ids:
            if model_id in record and record.get(model_id) == 'S':
                model_features.append((feature_code, model_id, MODEL_YEAR, 1))  # is_standard=1

    if not features:
        return 0, 0

    print(f"  📊 {len(features)} features, {len(model_features)} model-feature links")

    # Write CSVs
    features_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
    model_features_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')

    try:
        # Write features
        feat_writer = csv.writer(features_csv)
        for feature in features:
            feat_writer.writerow(feature)
        features_csv.close()

        # Write model-feature links
        mf_writer = csv.writer(model_features_csv)
        for mf in model_features:
            mf_writer.writerow(mf)
        model_features_csv.close()

        # Create temp tables
        cursor.execute("""
            CREATE TEMPORARY TABLE temp_features (
                feature_code VARCHAR(50), area VARCHAR(100), description TEXT,
                sort_order INT, active TINYINT(1)
            )
        """)
        cursor.execute("""
            CREATE TEMPORARY TABLE temp_model_features (
                feature_code VARCHAR(50), model_id VARCHAR(20), year INT, is_standard TINYINT(1)
            )
        """)

        # Bulk load
        print(f"  ⚡ Bulk loading standard features...")
        cursor.execute(f"LOAD DATA LOCAL INFILE '{features_csv.name}' INTO TABLE temp_features FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' LINES TERMINATED BY '\\n'")
        cursor.execute(f"LOAD DATA LOCAL INFILE '{model_features_csv.name}' INTO TABLE temp_model_features FIELDS TERMINATED BY ',' LINES TERMINATED BY '\\n'")

        # Insert features with upsert
        cursor.execute("""
            INSERT INTO StandardFeatures (feature_code, area, description, sort_order, active)
            SELECT feature_code, area, description, sort_order, active FROM temp_features
            ON DUPLICATE KEY UPDATE
                area = VALUES(area),
                description = VALUES(description),
                sort_order = VALUES(sort_order),
                updated_at = NOW()
        """)

        print(f"  ⚡ Bulk loading model-feature links...")
        # Insert model-feature links (join with StandardFeatures to get feature_id)
        cursor.execute("""
            INSERT INTO ModelStandardFeatures (model_id, feature_id, year, is_standard)
            SELECT tmf.model_id, sf.feature_id, tmf.year, tmf.is_standard
            FROM temp_model_features tmf
            JOIN StandardFeatures sf ON tmf.feature_code = sf.feature_code
            ON DUPLICATE KEY UPDATE is_standard = TRUE, updated_at = NOW()
        """)

        # Cleanup
        cursor.execute("DROP TEMPORARY TABLE temp_features")
        cursor.execute("DROP TEMPORARY TABLE temp_model_features")

        print(f"  ✅ Loaded {len(features)} features, {len(model_features)} links")
        return len(features), 0

    finally:
        os.unlink(features_csv.name)
        os.unlink(model_features_csv.name)

# ==================== STEP 4: DEALER MARGINS ====================

def fetch_dealer_margins(token: str) -> List[Dict]:
    """Fetch all dealer margins from API"""
    try:
        headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
        # CRITICAL FIX: Add $top=50000 to fetch ALL ~35,000 records (not just 100)
        response = requests.get(
            f"{DEALER_MARGIN_ENDPOINT}?$top=50000",
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            verify=False
        )
        response.raise_for_status()

        data = response.json()
        margins = data.get('items', [])

        print(f"   ✓ Fetched {len(margins):,} margin records from CPQ API")

        return margins

    except Exception as e:
        print(f"⚠️  Error fetching dealer margins: {e}")
        return []

def load_dealer_margins_to_db(cursor, margins: List[Dict]):
    """Load dealer margins into database using CSV bulk loading"""
    import csv
    import tempfile
    import os

    dealers_loaded = 0
    margins_loaded = 0
    errors = 0

    print("  📝 Preparing data for bulk loading...")

    # Deduplicate margins by dealer_id + series_id + effective_date
    unique_margins = {}
    dealers = {}
    series_set = set()
    effective_date = date.today()

    for margin_record in margins:
        dealer_id = margin_record.get('C_DealerId')
        dealer_name = margin_record.get('C_DealerName')
        series_id = margin_record.get('C_Series')

        if not dealer_id or not dealer_name or not series_id:
            errors += 1
            continue

        # Track unique dealers and series
        dealers[dealer_id] = dealer_name
        series_set.add(series_id)

        # Create unique key for deduplication
        key = (dealer_id, series_id, effective_date)

        # Keep last occurrence (in case of duplicates from API)
        unique_margins[key] = {
            'dealer_id': dealer_id,
            'series_id': series_id,
            'base_boat': margin_record.get('C_BaseBoat', 0),
            'engine': margin_record.get('C_Engine', 0),
            'options': margin_record.get('C_Options', 0),
            'freight': margin_record.get('C_Freight', 0),
            'prep': margin_record.get('C_Prep', 0),
            'volume': margin_record.get('C_Volume', 0),
            'enabled': 1 if margin_record.get('C_Enabled', False) else 0,
            'effective_date': effective_date,
            'year': MODEL_YEAR
        }

    print(f"  📊 Deduplicated: {len(margins)} → {len(unique_margins)} unique margins")
    print(f"  📊 Found {len(dealers)} unique dealers, {len(series_set)} unique series")

    # Create temp CSV files
    dealers_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_dealers.csv', newline='')
    margins_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_margins.csv', newline='')

    try:
        # Write dealers CSV
        print("  💾 Writing dealers to CSV...")
        dealer_writer = csv.writer(dealers_csv)
        for dealer_id, dealer_name in dealers.items():
            dealer_writer.writerow([dealer_id, dealer_name, 1])  # active=1
        dealers_csv.close()

        # Write margins CSV
        print("  💾 Writing margins to CSV...")
        margin_writer = csv.writer(margins_csv)
        for margin in unique_margins.values():
            margin_writer.writerow([
                margin['dealer_id'],
                margin['series_id'],
                margin['base_boat'],
                margin['engine'],
                margin['options'],
                margin['freight'],
                margin['prep'],
                margin['volume'],
                margin['enabled'],
                margin['effective_date'],
                margin['year']
            ])
        margins_csv.close()

        # Create temporary tables
        print("  🔧 Creating temporary tables...")
        cursor.execute("""
            CREATE TEMPORARY TABLE temp_dealers (
                dealer_id VARCHAR(20),
                dealer_name VARCHAR(200),
                active TINYINT(1)
            )
        """)
        cursor.execute("""
            CREATE TEMPORARY TABLE temp_margins (
                dealer_id VARCHAR(20),
                series_id VARCHAR(10),
                base_boat_margin DECIMAL(5,2),
                engine_margin DECIMAL(5,2),
                options_margin DECIMAL(5,2),
                freight_margin DECIMAL(5,2),
                prep_margin DECIMAL(5,2),
                volume_discount DECIMAL(5,2),
                enabled TINYINT(1),
                effective_date DATE,
                year INT
            )
        """)

        # Bulk load into temp tables
        print("  ⚡ Bulk loading dealers into temp table...")
        cursor.execute(f"""
            LOAD DATA LOCAL INFILE '{dealers_csv.name}'
            INTO TABLE temp_dealers
            FIELDS TERMINATED BY ','
            LINES TERMINATED BY '\n'
            (dealer_id, dealer_name, active)
        """)

        print("  ⚡ Bulk loading margins into temp table...")
        cursor.execute(f"""
            LOAD DATA LOCAL INFILE '{margins_csv.name}'
            INTO TABLE temp_margins
            FIELDS TERMINATED BY ','
            LINES TERMINATED BY '\n'
            (dealer_id, series_id, base_boat_margin, engine_margin, options_margin,
             freight_margin, prep_margin, volume_discount, enabled, effective_date, year)
        """)

        # Insert from temp tables with ON DUPLICATE KEY UPDATE
        print("  🔄 Inserting dealers with upsert...")
        cursor.execute("""
            INSERT INTO Dealers (dealer_id, dealer_name, active)
            SELECT dealer_id, dealer_name, active FROM temp_dealers
            ON DUPLICATE KEY UPDATE
                dealer_name = VALUES(dealer_name),
                updated_at = NOW()
        """)
        dealers_loaded = len(dealers)
        print(f"  ✅ Loaded {dealers_loaded} dealers")

        print("  🔄 Inserting dealer margins with upsert...")
        cursor.execute("""
            INSERT INTO DealerMargins (
                dealer_id, series_id, base_boat_margin, engine_margin, options_margin,
                freight_margin, prep_margin, volume_discount, enabled, effective_date, year
            )
            SELECT
                dealer_id, series_id, base_boat_margin, engine_margin, options_margin,
                freight_margin, prep_margin, volume_discount, enabled, effective_date, year
            FROM temp_margins
            ON DUPLICATE KEY UPDATE
                base_boat_margin = VALUES(base_boat_margin),
                engine_margin = VALUES(engine_margin),
                options_margin = VALUES(options_margin),
                freight_margin = VALUES(freight_margin),
                prep_margin = VALUES(prep_margin),
                volume_discount = VALUES(volume_discount),
                enabled = VALUES(enabled),
                updated_at = NOW()
        """)
        margins_loaded = len(unique_margins)
        print(f"  ✅ Loaded {margins_loaded} dealer margins")

        # Drop temp tables
        cursor.execute("DROP TEMPORARY TABLE temp_dealers")
        cursor.execute("DROP TEMPORARY TABLE temp_margins")

    finally:
        # Clean up temp files
        os.unlink(dealers_csv.name)
        os.unlink(margins_csv.name)

    return dealers_loaded, margins_loaded, errors

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

    # Get tokens (PRD only - all endpoints now use PRD environment)
    print("\n🔐 Obtaining API tokens...")
    token_prd = get_token("PRD")

    if not token_prd:
        print("❌ Failed to obtain API token. Exiting.")
        return

    print("✅ Token obtained successfully")

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
            perf_data = fetch_performance_data(token_prd, series)
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
            standards_data = fetch_standard_features(token_prd, series)
            if standards_data:
                print(f"   Fetched {len(standards_data)} standard feature records")
                success, errors = load_standards_to_db(cursor, series, standards_data, all_model_ids)
                total_std_success += success
                total_std_errors += errors
                connection.commit()

        print(f"\n✅ Standard features loaded: {total_std_success} records, {total_std_errors} errors")

        # STEP 4: Fetch and load dealer margins
        print("\n" + "=" * 80)
        print("STEP 4: DEALER MARGINS")
        print("=" * 80)

        print("\n📋 Fetching dealer margins from API...")
        margins = fetch_dealer_margins(token_prd)

        if margins:
            print(f"   Fetched {len(margins)} dealer margin records")
            dealers_count, margins_count, margins_errors = load_dealer_margins_to_db(cursor, margins)
            connection.commit()
            print(f"\n✅ Dealer margins loaded: {dealers_count} dealers, {margins_count} margin records, {margins_errors} errors")
        else:
            print("⚠️  No dealer margins fetched")
            dealers_count = 0
            margins_count = 0
            margins_errors = 0

        # Get final database statistics
        cursor.execute("SELECT COUNT(*) FROM Models")
        total_models = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ModelPricing WHERE end_date IS NULL")
        total_active_pricing = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT dealer_id) FROM Dealers")
        total_dealers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM DealerMargins WHERE end_date IS NULL")
        total_active_margins = cursor.fetchone()[0]

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
    print(f"✅ Dealer margins loaded:   {margins_count} ({margins_errors} errors)")
    print(f"\n📊 DATABASE TOTALS:")
    print(f"   Active models:           {total_models}")
    print(f"   Current pricing records: {total_active_pricing}")
    print(f"   Active dealers:          {total_dealers}")
    print(f"   Current margin configs:  {total_active_margins}")
    print(f"\n⏱️  Total execution time:   {elapsed_time:.1f} seconds")
    print(f"💾 Database:                {DB_CONFIG['database']}")
    print(f"📅 Completed:               {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
