"""
Fetch Model Prices (MSRP) from Infor CPQ OptionList API

This script:
1. Fetches all models from the OptionList API
2. Extracts model ID, series, and MSRP price
3. Saves to CSV and JSON formats for easy use
"""

import requests
import json
import urllib3
import time
import csv
from typing import List, Dict, Optional
from datetime import datetime
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

# Output files
OUTPUT_DIR = Path("model_prices")
CSV_OUTPUT = OUTPUT_DIR / "model_prices.csv"
JSON_OUTPUT = OUTPUT_DIR / "model_prices.json"

# Request settings
REQUEST_TIMEOUT = 120
MAX_RETRIES = 3

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

                        # Extract key fields
                        series = custom_props.get('Series', '') if custom_props else ''
                        price = custom_props.get('Price', 0) if custom_props else 0
                        parent_series = custom_props.get('ParentSeries', '') if custom_props else ''
                        floorplan = custom_props.get('Floorplan', '') if custom_props else ''
                        floorplan_desc = custom_props.get('FloorplanDesc', '') if custom_props else ''
                        length = custom_props.get('Length', '') if custom_props else ''
                        seats = custom_props.get('Seats', 0) if custom_props else 0

                        model_info = {
                            'model_id': model_id,
                            'series': series,
                            'parent_series': parent_series,
                            'msrp': price,
                            'floorplan': floorplan,
                            'floorplan_desc': floorplan_desc,
                            'length': length,
                            'seats': seats,
                            'visible': visible
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

    print(f"💾 CSV saved to: {output_file}")

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

    print(f"💾 JSON saved to: {output_file}")

# ==================== ANALYSIS ====================

def analyze_pricing(models: List[Dict]):
    """Analyze and display pricing statistics"""
    print("\n" + "=" * 80)
    print("PRICING ANALYSIS")
    print("=" * 80)

    # Filter visible models with prices
    visible_models = [m for m in models if m['visible'] and m['msrp'] > 0]

    if not visible_models:
        print("⚠️  No visible models with pricing found")
        return

    # Overall stats
    prices = [m['msrp'] for m in visible_models]
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)

    print(f"\n📊 Overall Statistics:")
    print(f"   Total models: {len(models)}")
    print(f"   Visible models with pricing: {len(visible_models)}")
    print(f"   Average MSRP: ${avg_price:,.2f}")
    print(f"   Minimum MSRP: ${min_price:,.2f}")
    print(f"   Maximum MSRP: ${max_price:,.2f}")

    # Group by series
    series_stats = {}
    for model in visible_models:
        series = model['series']
        if series:
            if series not in series_stats:
                series_stats[series] = {
                    'count': 0,
                    'prices': [],
                    'models': []
                }
            series_stats[series]['count'] += 1
            series_stats[series]['prices'].append(model['msrp'])
            series_stats[series]['models'].append(model['model_id'])

    print(f"\n📋 Pricing by Series:")
    for series in sorted(series_stats.keys()):
        stats = series_stats[series]
        avg = sum(stats['prices']) / len(stats['prices'])
        min_p = min(stats['prices'])
        max_p = max(stats['prices'])
        print(f"\n   {series}:")
        print(f"      Models: {stats['count']}")
        print(f"      Avg MSRP: ${avg:,.2f}")
        print(f"      Range: ${min_p:,.2f} - ${max_p:,.2f}")

    # Show most expensive models
    print(f"\n💰 Top 10 Most Expensive Models:")
    sorted_models = sorted(visible_models, key=lambda x: x['msrp'], reverse=True)
    for i, model in enumerate(sorted_models[:10], 1):
        print(f"   {i:2d}. {model['model_id']:<15} ({model['series']:<6}) - ${model['msrp']:>8,}")

    # Show least expensive models
    print(f"\n💵 Top 10 Least Expensive Models:")
    for i, model in enumerate(sorted_models[-10:][::-1], 1):
        print(f"   {i:2d}. {model['model_id']:<15} ({model['series']:<6}) - ${model['msrp']:>8,}")

# ==================== MAIN EXECUTION ====================

def main():
    """Main execution function"""
    print("=" * 80)
    print("FETCH MODEL PRICES (MSRP) FROM CPQ OPTIONLIST API")
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

    # Save to files
    print("\n📁 Saving data to files...")
    save_to_csv(models, CSV_OUTPUT)
    save_to_json(models, JSON_OUTPUT)

    # Analyze pricing
    analyze_pricing(models)

    # Summary
    elapsed_time = time.time() - start_time

    print("\n" + "=" * 80)
    print("FETCH COMPLETE")
    print("=" * 80)
    print(f"✅ Total models fetched: {len(models)}")
    print(f"⏱️  Total time: {elapsed_time:.1f} seconds")
    print(f"📂 Output directory: {OUTPUT_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
