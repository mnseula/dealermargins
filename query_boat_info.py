import requests
import json
from typing import Optional, Dict, Any
import urllib3

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API Configuration
CLIENT_ID_PRD = "QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo"
CLIENT_SECRET_PRD = "4O7OIZ64sukP1N6YeGZ6IpzsFTG4T6RFkcTZgq6ZwAetb4VoNOOJ1qMkGQAlvnOqqcgaZDlXKux6YEQNvoZQgg"
SERVICE_ACCOUNT_ACCESS_KEY_PRD = "QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9xuXKp_iYp49_M7JuB7UaEo0xjWDqTAE1Q15rQhxojw"
SERVICE_ACCOUNT_SECRET_KEY_PRD = "IZq8wArFnHi4rESTZ-3SQT5zMgiCQfre8aLM6KirsVmvBhXmGDZS_4TXvCZlD40AjpXX6igL7y8A3svCHV-glg"
TOKEN_ENDPOINT_PRD = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2"

CLIENT_ID_TRN = "QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8"
CLIENT_SECRET_TRN = "CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAnyArDH3ZebqYTKAoMq37_aQ"
SERVICE_ACCOUNT_ACCESS_KEY_TRN = "QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw"
SERVICE_ACCOUNT_SECRET_KEY_TRN = "pAze3yNlj8r6dbcTv-Fn8AiGvhIcs2x-yEgJaMiuoraAJdkFB6iLQFKaFQCP_17KZIYoroUoF_CeEoslHWlXug"
TOKEN_ENDPOINT_TRN = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2"

# API Endpoints
OPTION_LIST_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/DataImport/QA2FNBZCKUAUH7QB_PRD/v1/OptionLists/bb38d84e-6493-40c7-b282-9cb9c0df26ae/values"
PERFORMANCE_MATRIX_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/{series}_PerformanceData_2026/values"
STANDARDS_MATRIX_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQ/DataImport/v2/Matrices/{series}_ModelStandards_2026/values"
DEALER_MARGIN_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities/C_GD_DealerMargin"

def get_token(environment: str = "PRD") -> Optional[str]:
    """Get OAuth token for the specified environment."""
    if environment == "PRD":
        token_endpoint = TOKEN_ENDPOINT_PRD
        payload = {
            'grant_type': 'password',
            'client_id': CLIENT_ID_PRD,
            'client_secret': CLIENT_SECRET_PRD,
            'username': SERVICE_ACCOUNT_ACCESS_KEY_PRD,
            'password': SERVICE_ACCOUNT_SECRET_KEY_PRD
        }
    else:  # TRN
        token_endpoint = TOKEN_ENDPOINT_TRN
        payload = {
            'grant_type': 'password',
            'client_id': CLIENT_ID_TRN,
            'client_secret': CLIENT_SECRET_TRN,
            'username': SERVICE_ACCOUNT_ACCESS_KEY_TRN,
            'password': SERVICE_ACCOUNT_SECRET_KEY_TRN
        }

    try:
        print(f"🔑 Getting {environment} token...")
        response = requests.post(token_endpoint, data=payload, timeout=60, verify=False)
        response.raise_for_status()
        token = response.json().get('access_token')
        print(f"✅ Token obtained for {environment}")
        return token
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting token: {e}")
        return None

def get_model_info(model_id: str) -> Optional[Dict[str, Any]]:
    """Get model information from OptionList API."""
    token = get_token("PRD")
    if not token:
        return None

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    try:
        print(f"\n🚤 Fetching model information for {model_id}...")
        response = requests.get(OPTION_LIST_ENDPOINT, headers=headers, timeout=60, verify=False)
        response.raise_for_status()
        data = response.json()

        # Find the specific model
        for item in data.get('result', []):
            if item.get('value') == model_id:
                print(f"✅ Found model: {model_id}")
                return item

        print(f"❌ Model {model_id} not found in catalog")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching model info: {e}")
        return None

def get_performance_data(model_id: str, series: str) -> Optional[Dict[str, Any]]:
    """Get performance data for a specific model."""
    token = get_token("TRN")
    if not token:
        return None

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    endpoint = PERFORMANCE_MATRIX_ENDPOINT.format(series=series)

    try:
        print(f"\n⚡ Fetching performance data for {model_id} (Series: {series})...")
        response = requests.get(endpoint, headers=headers, timeout=60, verify=False)
        response.raise_for_status()
        data = response.json()

        # Find records for this model
        model_records = []
        for item in data.get('result', {}).get('details', []):
            if item.get('model') == model_id:
                model_records.append(item)

        if model_records:
            print(f"✅ Found {len(model_records)} performance record(s)")
            return model_records
        else:
            print(f"❌ No performance data found for {model_id}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching performance data: {e}")
        return None

def get_standard_features(model_id: str, series: str) -> Optional[Dict[str, Any]]:
    """Get standard features for a specific model."""
    token = get_token("TRN")
    if not token:
        return None

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    endpoint = STANDARDS_MATRIX_ENDPOINT.format(series=series)

    try:
        print(f"\n✨ Fetching standard features for {model_id} (Series: {series})...")
        response = requests.get(endpoint, headers=headers, timeout=60, verify=False)
        response.raise_for_status()
        data = response.json()

        # Extract features for this model
        features = []
        for item in data.get('result', {}).get('details', []):
            if model_id in item and item.get(model_id) == 'S':
                features.append({
                    'area': item.get('Area'),
                    'description': item.get('Description'),
                    'sort': item.get('Sort')
                })

        if features:
            print(f"✅ Found {len(features)} standard features")
            return sorted(features, key=lambda x: (x['area'], x['sort']))
        else:
            print(f"❌ No standard features found for {model_id}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching standard features: {e}")
        return None

def get_dealer_margins(dealer_name: str, series: str) -> Optional[Dict[str, Any]]:
    """Get dealer margins from CPQ API."""
    token = get_token("TRN")
    if not token:
        return None

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    try:
        print(f"\n💰 Fetching dealer margins for {dealer_name} (Series: {series})...")
        # First, try to find by dealer name and series
        filter_query = f"$filter=C_DealerName eq '{dealer_name}' and C_Series eq '{series}'"
        url = f"{DEALER_MARGIN_ENDPOINT}?{filter_query}"

        response = requests.get(url, headers=headers, timeout=60, verify=False)
        response.raise_for_status()
        data = response.json()

        items = data.get('items', [])
        if items:
            print(f"✅ Found margins for {dealer_name}")
            return items[0]
        else:
            print(f"❌ No margins found for {dealer_name} in series {series}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching dealer margins: {e}")
        return None

def display_boat_info(model_id: str, dealer_name: str = None):
    """Display complete boat information."""
    print("=" * 80)
    print(f"BOAT INFORMATION REPORT: {model_id}")
    if dealer_name:
        print(f"Dealer: {dealer_name}")
    print("=" * 80)

    # 1. Get Model Info
    model_info = get_model_info(model_id)
    if not model_info:
        print("\n❌ Cannot proceed without model information")
        return

    # Extract series
    series = model_info.get('customProperties', {}).get('Series', '')

    # Display basic model info
    print("\n" + "─" * 80)
    print("📋 MODEL DETAILS")
    print("─" * 80)
    props = model_info.get('customProperties', {})
    print(f"Model ID: {model_info.get('value')}")
    print(f"Series: {props.get('Series')}")
    print(f"Parent Series: {props.get('ParentSeries')}")
    print(f"MSRP: ${props.get('Price'):,.2f}" if props.get('Price') else "MSRP: N/A")
    print(f"Length: {props.get('Length')}' ({props.get('LOAStr')})")
    print(f"Beam: {props.get('BeamStr')}")
    print(f"Floorplan: {props.get('FloorplanDesc')} ({props.get('Floorplan')})")
    print(f"Seating: {props.get('Seats')} seats")
    print(f"Visible: {'Yes' if model_info.get('visible') else 'No'}")

    # 2. Get Performance Data
    if series:
        perf_data = get_performance_data(model_id, series)
        if perf_data:
            print("\n" + "─" * 80)
            print("⚡ PERFORMANCE SPECIFICATIONS")
            print("─" * 80)
            for idx, perf in enumerate(perf_data, 1):
                if len(perf_data) > 1:
                    print(f"\nPackage {idx}: {perf.get('perfPack')}")
                print(f"Max HP: {perf.get('MaxHP')}")
                print(f"Number of Tubes: {int(perf.get('NoOfTubes', 0))}")
                print(f"Person Capacity: {perf.get('PersonCapacity')}")
                print(f"Hull Weight: {perf.get('HullWeight'):,.0f} lbs" if perf.get('HullWeight') else "Hull Weight: N/A")
                print(f"Pontoon Gauge: {perf.get('PontoonGauge')}\"")
                print(f"Transom: {perf.get('Transom')}\"")
                print(f"Tube Height: {perf.get('TubeHeight')}")
                print(f"Tube Center-to-Center: {perf.get('TubeCentertoCenter')}")
                print(f"Max Width: {perf.get('MaxWidth')}")
                print(f"Fuel Capacity: {perf.get('FuelCapacity')}")

    # 3. Get Standard Features
    if series:
        features = get_standard_features(model_id, series)
        if features:
            print("\n" + "─" * 80)
            print("✨ STANDARD FEATURES")
            print("─" * 80)
            current_area = None
            for feature in features:
                if feature['area'] != current_area:
                    current_area = feature['area']
                    print(f"\n{current_area}:")
                print(f"  • {feature['description']}")

    # 4. Get Dealer Margins
    if dealer_name and series:
        margins = get_dealer_margins(dealer_name, series)
        if margins:
            print("\n" + "─" * 80)
            print(f"💰 DEALER MARGINS - {dealer_name}")
            print("─" * 80)
            print(f"Dealer ID: {margins.get('C_DealerId')}")
            print(f"Dealer Name: {margins.get('C_DealerName')}")
            print(f"Series: {margins.get('C_Series')}")
            print(f"Enabled: {'Yes' if margins.get('C_Enabled') else 'No'}")
            print(f"\nMargin Percentages:")
            print(f"  Base Boat: {margins.get('C_BaseBoat')}%")
            print(f"  Engine: {margins.get('C_Engine')}%")
            print(f"  Options: {margins.get('C_Options')}%")
            print(f"  Freight: {margins.get('C_Freight')}%")
            print(f"  Prep: {margins.get('C_Prep')}%")
            print(f"  Volume Discount: {margins.get('C_Volume')}%")

            # Calculate dealer cost
            msrp = props.get('Price')
            if msrp and margins.get('C_BaseBoat'):
                base_margin = margins.get('C_BaseBoat') / 100
                dealer_cost = msrp * (1 - base_margin)
                print(f"\nEstimated Base Dealer Cost: ${dealer_cost:,.2f}")
                print(f"  (MSRP ${msrp:,.2f} × {1-base_margin:.2%})")

    print("\n" + "=" * 80)
    print("END OF REPORT")
    print("=" * 80)

if __name__ == "__main__":
    # Query for 25QXFBWA for Nichols Marine
    display_boat_info("25QXFBWA", "Nichols Marine")
