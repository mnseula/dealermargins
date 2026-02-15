#!/usr/bin/env python3
"""
Test what fields the Performance Data API actually returns
"""

import requests
import json
from typing import Dict

# TRN Environment credentials
CLIENT_ID = 'QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8'
CLIENT_SECRET = 'CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAnyArDH3ZebqYTKAoMq37_aQ'
SERVICE_KEY = 'QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw'
SERVICE_SECRET = 'pAze3yNlj8r6dbcTv-Fn8AiGvhIcs2x-yEgJaMiuoraAJdkFB6iLQFKaFQCP_17KZIYoroUoF_CeEoslHWlXug'
TOKEN_ENDPOINT = 'https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2'
PERFORMANCE_ENDPOINT = 'https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/M_PerformanceData_2026/values'

def get_access_token() -> str:
    """Get OAuth access token"""
    payload = {
        'grant_type': 'password',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'username': SERVICE_KEY,
        'password': SERVICE_SECRET
    }

    response = requests.post(TOKEN_ENDPOINT, data=payload, verify=False)
    response.raise_for_status()

    token_data = response.json()
    return token_data['access_token']

def fetch_performance_data(token: str) -> Dict:
    """Fetch M series performance data"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }

    response = requests.get(PERFORMANCE_ENDPOINT, headers=headers, timeout=30, verify=False)
    response.raise_for_status()

    return response.json()

if __name__ == '__main__':
    print("=" * 100)
    print("TESTING PERFORMANCE DATA API - M SERIES")
    print("=" * 100)
    print()

    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("1. Getting access token...")
    token = get_access_token()
    print("   ✅ Token obtained")
    print()

    print("2. Fetching performance data...")
    data = fetch_performance_data(token)
    print("   ✅ Data fetched")
    print()

    # Get the details array
    details = data.get('result', {}).get('details', [])
    print(f"3. Found {len(details)} performance records")
    print()

    if details:
        # Show first record's fields
        first_record = details[0]
        print("4. FIELDS IN FIRST RECORD:")
        print("-" * 100)

        # Sort fields for easier reading
        for key in sorted(first_record.keys()):
            value = first_record[key]
            if value is not None and value != '':
                print(f"  {key}: {value}")

        print()
        print("=" * 100)
        print("5. LOOKING FOR LENGTH FIELDS:")
        print("=" * 100)

        # Check all records for length-related fields
        length_fields = set()
        for record in details:
            for key in record.keys():
                if 'length' in key.lower() or 'deck' in key.lower() or 'tube' in key.lower() or 'pontoon' in key.lower():
                    length_fields.add(key)

        if length_fields:
            print("\nFound these length-related fields:")
            for field in sorted(length_fields):
                print(f"  - {field}")

            # Show example values
            print("\nExample values for length fields:")
            print("-" * 100)
            for i, record in enumerate(details[:3], 1):
                model = record.get('model', 'Unknown')
                perf_pack = record.get('perfPack', 'Unknown')
                print(f"\nRecord {i}: {model} / {perf_pack}")
                for field in sorted(length_fields):
                    value = record.get(field)
                    if value:
                        print(f"  {field}: {value}")
        else:
            print("❌ NO LENGTH-RELATED FIELDS FOUND!")
            print("\nAll available fields:")
            all_fields = set()
            for record in details:
                all_fields.update(record.keys())
            for field in sorted(all_fields):
                print(f"  - {field}")
    else:
        print("❌ No performance records returned!")

    print()
    print("=" * 100)
