"""
Fetch Performance Data for All Series from Infor CPQ Matrix API

This script:
1. Fetches all models from the OptionList API
2. Extracts unique series codes
3. For each series, fetches performance data from Matrix API
4. Saves results to JSON files
"""

import requests
import json
import urllib3
import time
from typing import Dict, List, Optional, Set
import os
from datetime import datetime
from pathlib import Path

# Suppress the insecure request warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== CONFIGURATION ====================

# Use TRN credentials (where we successfully tested the Matrix API)
CLIENT_ID = "QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8"
CLIENT_SECRET = "CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAnyArDH3ZebqYTKAoMq37_aQ"
TOKEN_ENDPOINT = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2"
SERVICE_ACCOUNT_ACCESS_KEY = "QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw"
SERVICE_ACCOUNT_SECRET_KEY = "pAze3yNlj8r6dbcTv-Fn8AiGvhIcs2x-yEgJaMiuoraAJdkFB6iLQFKaFQCP_17KZIYoroUoF_CeEoslHWlXug"

COMPANY_WORKSPACE_NAME = "QA2FNBZCKUAUH7QB_TRN"

# For fetching models - use PRD credentials
PRD_CLIENT_ID = "QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo"
PRD_CLIENT_SECRET = "4O7OIZ64sukP1N6YeGZ6IpzsFTG4T6RFkcTZgq6ZwAetb4VoNOOJ1qMkGQAlvnOqqcgaZDlXKux6YEQNvoZQgg"
PRD_TOKEN_ENDPOINT = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2"
PRD_SERVICE_ACCOUNT_ACCESS_KEY = "QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9xuXKp_iYp49_M7JuB7UaEo0xjWDqTAE1Q15rQhxojw"
PRD_SERVICE_ACCOUNT_SECRET_KEY = "IZq8wArFnHi4rESTZ-3SQT5zMgiCQfre8aLM6KirsVmvBhXmGDZS_4TXvCZlD40AjpXX6igL7y8A3svCHV-glg"
PRD_COMPANY_WORKSPACE_NAME = "QA2FNBZCKUAUH7QB_PRD"
OPTION_LIST_ID = "bb38d84e-6493-40c7-b282-9cb9c0df26ae"

MODEL_LIST_ENDPOINT = f"https://mingle-ionapi.inforcloudsuite.com/{PRD_COMPANY_WORKSPACE_NAME}/CPQ/DataImport/{PRD_COMPANY_WORKSPACE_NAME}/v1/OptionLists/{OPTION_LIST_ID}/values"

# Matrix API base endpoint (TRN environment)
MATRIX_API_BASE = f"https://mingle-ionapi.inforcloudsuite.com/{COMPANY_WORKSPACE_NAME}/CPQ/DataImport/v2/Matrices"

# Current year for matrix names
CURRENT_YEAR = datetime.now().year

# Output directory
OUTPUT_DIR = Path("performance_data")

# Request settings
REQUEST_TIMEOUT = 120
MAX_RETRIES = 3

# ==================== TOKEN MANAGEMENT ====================

class TokenManager:
    """Thread-safe token management with automatic refresh"""
    def __init__(self, client_id, client_secret, token_endpoint, access_key, secret_key):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.token = None
        self.expires_at = 0
        self.session = None

    def initialize_session(self):
        """Initialize requests session"""
        if not self.session:
            self.session = requests.Session()
            self.session.verify = False
        return self.session

    def get_token(self) -> Optional[str]:
        """Get a valid token, refreshing if necessary"""
        # Check if current token is still valid (with 5 minute buffer)
        if self.token and time.time() < (self.expires_at - 300):
            return self.token
        return self._refresh_token()

    def _refresh_token(self) -> Optional[str]:
        """Internal method to refresh the token"""
        payload = {
            'grant_type': 'password',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': self.access_key,
            'password': self.secret_key
        }
        try:
            print(f"🔄 Refreshing access token...")
            session = self.initialize_session()
            response = session.post(self.token_endpoint, data=payload, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            self.expires_at = time.time() + expires_in
            print(f"✅ Token refreshed successfully")
            return self.token
        except requests.exceptions.RequestException as e:
            print(f"❌ Error refreshing token: {e}")
            return None

# ==================== API FUNCTIONS ====================

def fetch_all_models(token_manager: TokenManager) -> List[Dict]:
    """Fetch all models from OptionList API"""
    print(f"\n📋 Fetching models from OptionList API...")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            token = token_manager.get_token()
            if not token:
                print("❌ Failed to get API token")
                return []

            session = token_manager.initialize_session()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }

            response = session.get(MODEL_LIST_ENDPOINT, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()

            data = response.json()
            models = []

            if 'result' in data and isinstance(data['result'], list):
                for item in data['result']:
                    if 'value' in item and item.get('visible', True):
                        model_id = str(item['value']).strip()
                        custom_props = item.get('customProperties', {})

                        # Extract series from custom properties
                        series = custom_props.get('Series', '') if custom_props else ''

                        models.append({
                            'model_id': model_id,
                            'series': series,
                            'custom_properties': custom_props
                        })

                print(f"✅ Successfully fetched {len(models)} models")
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

def extract_unique_series(models: List[Dict]) -> Set[str]:
    """Extract unique series codes from models"""
    series_set = set()

    for model in models:
        series = model.get('series', '').strip()
        if series:
            series_set.add(series)

    return series_set

def fetch_performance_data(token_manager: TokenManager, series: str, year: int = CURRENT_YEAR) -> Optional[Dict]:
    """Fetch performance data for a specific series"""
    matrix_name = f"{series}_PerformanceData_{year}"
    matrix_url = f"{MATRIX_API_BASE}/{matrix_name}/values"

    print(f"\n🔍 Fetching performance data for series: {series}")
    print(f"   Matrix: {matrix_name}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            token = token_manager.get_token()
            if not token:
                print(f"   ❌ Failed to get API token")
                return None

            session = token_manager.initialize_session()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }

            response = session.get(matrix_url, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)

            # Check for 404 - matrix doesn't exist for this series
            if response.status_code == 404:
                print(f"   ⚠️  Matrix not found (404) - series may not have performance data")
                return None

            response.raise_for_status()

            data = response.json()

            # Get record count
            total_count = 0
            if 'result' in data and 'totalDetailsCount' in data['result']:
                total_count = data['result']['totalDetailsCount']
            elif 'result' in data and 'details' in data['result']:
                total_count = len(data['result']['details'])

            print(f"   ✅ Successfully fetched {total_count} performance records")

            return data

        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES:
                print(f"   ⚠️  Attempt {attempt}/{MAX_RETRIES} failed: {e}")
                wait_time = attempt * 5
                print(f"   Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"   ❌ Failed after {MAX_RETRIES} attempts: {e}")
                return None

    return None

def save_performance_data(series: str, data: Dict, output_dir: Path):
    """Save performance data to JSON file"""
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = output_dir / f"{series}_PerformanceData_{CURRENT_YEAR}.json"

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"   💾 Saved to: {filename}")

# ==================== MAIN EXECUTION ====================

def main():
    """Main execution function"""
    print("=" * 80)
    print("FETCH ALL SERIES PERFORMANCE DATA FROM CPQ MATRIX API")
    print("=" * 80)
    print(f"Year: {CURRENT_YEAR}")
    print(f"Output Directory: {OUTPUT_DIR}")

    start_time = time.time()

    # Initialize token managers
    print("\n🔐 Initializing authentication...")
    prd_token_manager = TokenManager(
        PRD_CLIENT_ID,
        PRD_CLIENT_SECRET,
        PRD_TOKEN_ENDPOINT,
        PRD_SERVICE_ACCOUNT_ACCESS_KEY,
        PRD_SERVICE_ACCOUNT_SECRET_KEY
    )

    trn_token_manager = TokenManager(
        CLIENT_ID,
        CLIENT_SECRET,
        TOKEN_ENDPOINT,
        SERVICE_ACCOUNT_ACCESS_KEY,
        SERVICE_ACCOUNT_SECRET_KEY
    )

    # Step 1: Fetch all models from PRD
    models = fetch_all_models(prd_token_manager)

    if not models:
        print("\n❌ No models fetched. Exiting.")
        return

    # Step 2: Extract unique series
    print("\n📊 Extracting unique series...")
    unique_series = extract_unique_series(models)

    if not unique_series:
        print("❌ No series found in models. Exiting.")
        return

    # Sort for consistent output
    sorted_series = sorted(unique_series)

    print(f"✅ Found {len(sorted_series)} unique series:")
    for series in sorted_series:
        model_count = sum(1 for m in models if m.get('series') == series)
        print(f"   {series:<15} ({model_count} models)")

    # Step 3: Fetch performance data for each series from TRN
    print("\n" + "=" * 80)
    print("FETCHING PERFORMANCE DATA FOR EACH SERIES")
    print("=" * 80)

    success_count = 0
    not_found_count = 0
    error_count = 0

    results_summary = {
        'timestamp': datetime.now().isoformat(),
        'year': CURRENT_YEAR,
        'total_series': len(sorted_series),
        'series_results': []
    }

    for i, series in enumerate(sorted_series, 1):
        print(f"\n[{i}/{len(sorted_series)}] Processing series: {series}")

        performance_data = fetch_performance_data(trn_token_manager, series, CURRENT_YEAR)

        if performance_data:
            save_performance_data(series, performance_data, OUTPUT_DIR)
            success_count += 1

            # Get record count for summary
            record_count = 0
            if 'result' in performance_data and 'totalDetailsCount' in performance_data['result']:
                record_count = performance_data['result']['totalDetailsCount']
            elif 'result' in performance_data and 'details' in performance_data['result']:
                record_count = len(performance_data['result']['details'])

            results_summary['series_results'].append({
                'series': series,
                'status': 'success',
                'record_count': record_count,
                'matrix_name': f"{series}_PerformanceData_{CURRENT_YEAR}"
            })
        else:
            # Check if it was a 404 or other error
            # For now, count as not found
            not_found_count += 1
            results_summary['series_results'].append({
                'series': series,
                'status': 'not_found',
                'record_count': 0,
                'matrix_name': f"{series}_PerformanceData_{CURRENT_YEAR}"
            })

    # Save summary
    results_summary['success_count'] = success_count
    results_summary['not_found_count'] = not_found_count
    results_summary['error_count'] = error_count

    summary_file = OUTPUT_DIR / f"fetch_summary_{CURRENT_YEAR}.json"
    with open(summary_file, 'w') as f:
        json.dump(results_summary, f, indent=2)

    # Print final summary
    elapsed_time = time.time() - start_time

    print("\n" + "=" * 80)
    print("FETCH COMPLETE")
    print("=" * 80)
    print(f"✅ Success: {success_count} series")
    print(f"⚠️  Not Found: {not_found_count} series")
    print(f"❌ Errors: {error_count} series")
    print(f"⏱️  Total time: {elapsed_time:.1f} seconds")
    print(f"💾 Summary saved to: {summary_file}")
    print(f"📂 Performance data saved to: {OUTPUT_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
