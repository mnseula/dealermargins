"""
Fetch Model Prices (MSRP) from Infor CPQ OptionList API and Load to Database

This script:
1. Fetches all models from the OptionList API
2. Extracts model ID, series, and MSRP price
3. Inserts into MySQL database (Series, Models, ModelPricing)
4. Saves backup to CSV and JSON formats
"""

import requests
import json
import urllib3
import time
import csv
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Optional
from datetime import datetime, date
from pathlib import Path

# Suppress the insecure request warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== CONFIGURATION ====================

# PRD credentials for OptionList API
CLIENT_ID = "QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo"
CLIENT_SECRET = "4O7OIZ64sukP1N6YeGZ6IpzsFTG4T6RFkcTZgq6ZwAetb4VoNOOJ1qMkGQAlvnOqqcgaZDlXKux6YEQNvoZQgg"
TOKEN_ENDPOINT = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2"
SERVICE_ACCOUNT_ACCESS_KEY = "QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9xuXKp_iYp49_M7JuB7UaEo0xjWDqTAE1Q15rQhxojw"
SERVICE_ACCOUNT_SECRET_KEY = "IZq8wArFnHi4rESTZ-3SQT5zMgiCQfre8aLM6KirsVmvBhXmGDZS_4TXvCZlD40AjpXX6igL7y8A3svCHV-glg"
COMPANY_WORKSPACE_NAME = "QA2FNBZCKUAUH7QB_PRD"
OPTION_LIST_ID = "bb38d84e-6493-40c7-b282-9cb9c0df26ae"

MODEL_LIST_ENDPOINT = f"https://mingle-ionapi.inforcloudsuite.com/{COMPANY_WORKSPACE_NAME}/CPQ/DataImport/{COMPANY_WORKSPACE_NAME}/v1/OptionLists/{OPTION_LIST_ID}/values"

# Database configuration
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'bennington_cpq'
}

# Output files
OUTPUT_DIR = Path("model_prices")
CSV_OUTPUT = OUTPUT_DIR / "model_prices.csv"
JSON_OUTPUT = OUTPUT_DIR / "model_prices.json"

# Request settings
REQUEST_TIMEOUT = 120
MAX_RETRIES = 3
MODEL_YEAR = 2026

# ==================== TOKEN MANAGEMENT ====================

def get_access_token() -> Optional[str]:
    """Get OAuth access token"""
    payload = {
        'grant_type': 'password',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'username': SERVICE_ACCOUNT_ACCESS_KEY,
        'password': SERVICE_ACCOUNT_SECRET_KEY
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"🔄 Obtaining access token (attempt {attempt}/{MAX_RETRIES})...")
            response = requests.post(TOKEN_ENDPOINT, data=payload, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            token_data = response.json()
            token = token_data.get('access_token')
            print(f"✅ Token obtained successfully")
            return token
        except requests.exceptions.RequestException as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                wait_time = attempt * 10
                print(f"   Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

    print(f"❌ Failed to obtain token after {MAX_RETRIES} attempts")
    return None

# ==================== API FUNCTIONS ====================

def fetch_all_models_with_prices(token: str) -> List[Dict]:
    """Fetch all models with pricing from OptionList API"""
    print(f"\n📋 Fetching models and prices from OptionList API...")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }

            response = requests.get(MODEL_LIST_ENDPOINT, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()

            data = response.json()
            models = []

            if 'result' in data and isinstance(data['result'], list):
                for item in data['result']:
                    if 'value' in item:
                        model_id = str(item['value']).strip()
                        visible = item.get('visible', True)
                        custom_props = item.get('customProperties', {})

                        # Extract all fields from API
                        model_info = {
                            'model_id': model_id,
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
                            'visible': visible,
                            'image_link': custom_props.get('ImageLink', ''),
                            'has_arch': custom_props.get('Arch', False),
                            'has_windshield': custom_props.get('Windshield', False),
                            'twin_engine': custom_props.get('TwinEngine', False)
                        }

                        models.append(model_info)

                print(f"✅ Successfully fetched {len(models)} models with pricing")
                return models
            else:
                print(f"⚠️  Unexpected API response structure")
                return []

        except requests.exceptions.RequestException as e:
            print(f"❌ Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                wait_time = attempt * 10
                print(f"   Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

    print(f"❌ Failed to fetch models after {MAX_RETRIES} attempts")
    return []

# ==================== DATABASE FUNCTIONS ====================

def insert_series(cursor, series_id: str, parent_series: str = None):
    """Insert or update series in database"""
    if not series_id:
        return

    try:
        # Check if series exists
        cursor.execute("SELECT series_id FROM Series WHERE series_id = %s", (series_id,))
        exists = cursor.fetchone()

        if exists:
            # Update existing
            cursor.execute(
                "UPDATE Series SET parent_series = %s, updated_at = NOW() WHERE series_id = %s",
                (parent_series, series_id)
            )
        else:
            # Insert new
            cursor.execute(
                """INSERT INTO Series (series_id, series_name, parent_series, active)
                   VALUES (%s, %s, %s, TRUE)""",
                (series_id, series_id, parent_series)
            )
    except Error as e:
        print(f"⚠️  Error inserting series {series_id}: {e}")

def insert_model(cursor, model: Dict):
    """Insert or update model in database"""
    try:
        # Check if model exists
        cursor.execute("SELECT model_id FROM Models WHERE model_id = %s", (model['model_id'],))
        exists = cursor.fetchone()

        if exists:
            # Update existing model
            cursor.execute(
                """UPDATE Models SET
                   series_id = %s,
                   floorplan_code = %s,
                   floorplan_desc = %s,
                   length_feet = %s,
                   length_str = %s,
                   beam_length = %s,
                   beam_str = %s,
                   loa = %s,
                   loa_str = %s,
                   seats = %s,
                   visible = %s,
                   image_link = %s,
                   has_arch = %s,
                   has_windshield = %s,
                   twin_engine = %s,
                   updated_at = NOW()
                   WHERE model_id = %s""",
                (
                    model['series'],
                    model['floorplan'],
                    model['floorplan_desc'],
                    model['length'] if model['length'] else None,
                    model['length_str'],
                    model['beam_length'] if model['beam_length'] else None,
                    model['beam_str'],
                    model['loa'] if model['loa'] else None,
                    model['loa_str'],
                    model['seats'] if model['seats'] else None,
                    model['visible'],
                    model['image_link'],
                    model['has_arch'],
                    model['has_windshield'],
                    model['twin_engine'],
                    model['model_id']
                )
            )
        else:
            # Insert new model
            cursor.execute(
                """INSERT INTO Models (
                   model_id, series_id, floorplan_code, floorplan_desc,
                   length_feet, length_str, beam_length, beam_str,
                   loa, loa_str, seats, visible, image_link,
                   has_arch, has_windshield, twin_engine
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    model['model_id'],
                    model['series'],
                    model['floorplan'],
                    model['floorplan_desc'],
                    model['length'] if model['length'] else None,
                    model['length_str'],
                    model['beam_length'] if model['beam_length'] else None,
                    model['beam_str'],
                    model['loa'] if model['loa'] else None,
                    model['loa_str'],
                    model['seats'] if model['seats'] else None,
                    model['visible'],
                    model['image_link'],
                    model['has_arch'],
                    model['has_windshield'],
                    model['twin_engine']
                )
            )
    except Error as e:
        print(f"⚠️  Error inserting model {model['model_id']}: {e}")

def insert_pricing(cursor, model_id: str, msrp: float, year: int = MODEL_YEAR):
    """Insert model pricing with effective date tracking"""
    if msrp <= 0:
        return

    try:
        effective_date = date.today()

        # Check if there's already a pricing record with same MSRP (no change needed)
        cursor.execute(
            """SELECT pricing_id FROM ModelPricing
               WHERE model_id = %s AND end_date IS NULL AND msrp = %s""",
            (model_id, msrp)
        )
        same_price = cursor.fetchone()

        if same_price:
            # Price hasn't changed, do nothing
            return

        # End current active pricing
        cursor.execute(
            """UPDATE ModelPricing
               SET end_date = DATE_SUB(%s, INTERVAL 1 DAY)
               WHERE model_id = %s AND end_date IS NULL""",
            (effective_date, model_id)
        )

        # Insert new pricing
        cursor.execute(
            """INSERT INTO ModelPricing (model_id, msrp, effective_date, year)
               VALUES (%s, %s, %s, %s)""",
            (model_id, msrp, effective_date, year)
        )

    except Error as e:
        print(f"⚠️  Error inserting pricing for {model_id}: {e}")

def load_models_to_database(models: List[Dict]):
    """Load models and pricing into database"""
    print(f"\n💾 Loading {len(models)} models into database...")

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        success_count = 0
        error_count = 0

        for idx, model in enumerate(models, 1):
            if idx % 50 == 0:
                print(f"   Processing model {idx}/{len(models)}...")

            try:
                # Insert series (if not exists)
                insert_series(cursor, model['series'], model['parent_series'])

                # Insert/update model
                insert_model(cursor, model)

                # Insert/update pricing
                insert_pricing(cursor, model['model_id'], model['msrp'])

                success_count += 1

            except Exception as e:
                error_count += 1
                print(f"⚠️  Error processing model {model['model_id']}: {e}")

        # Commit all changes
        connection.commit()

        print(f"✅ Database load complete!")
        print(f"   Successful: {success_count} models")
        print(f"   Errors: {error_count} models")

        cursor.close()
        connection.close()

    except Error as e:
        print(f"❌ Database connection error: {e}")

# ==================== DATA EXPORT ====================

def save_to_csv(models: List[Dict], output_file: Path):
    """Save models and prices to CSV"""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if not models:
            print("⚠️  No models to save to CSV")
            return

        fieldnames = ['model_id', 'series', 'parent_series', 'msrp', 'floorplan', 'floorplan_desc', 'length', 'seats', 'visible']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(models)

    print(f"💾 CSV backup saved to: {output_file}")

def save_to_json(models: List[Dict], output_file: Path):
    """Save models and prices to JSON"""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        'timestamp': datetime.now().isoformat(),
        'total_models': len(models),
        'models': models
    }

    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"💾 JSON backup saved to: {output_file}")

# ==================== MAIN EXECUTION ====================

def main():
    """Main execution function"""
    print("=" * 80)
    print("FETCH MODEL PRICES AND LOAD TO DATABASE")
    print("=" * 80)

    start_time = time.time()

    # Get token
    token = get_access_token()
    if not token:
        print("\n❌ Failed to obtain access token. Exiting.")
        return

    # Fetch models with prices
    models = fetch_all_models_with_prices(token)

    if not models:
        print("\n❌ No models fetched. Exiting.")
        return

    # Load to database
    load_models_to_database(models)

    # Save backup files
    print("\n📁 Saving backup files...")
    save_to_csv(models, CSV_OUTPUT)
    save_to_json(models, JSON_OUTPUT)

    # Summary
    elapsed_time = time.time() - start_time

    print("\n" + "=" * 80)
    print("FETCH AND LOAD COMPLETE")
    print("=" * 80)
    print(f"✅ Total models processed: {len(models)}")
    print(f"⏱️  Total time: {elapsed_time:.1f} seconds")
    print(f"💾 Database: {DB_CONFIG['database']}")
    print(f"📂 Backup files: {OUTPUT_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
