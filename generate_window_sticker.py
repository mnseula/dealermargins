import requests
import json
from typing import Optional, Dict, Any, List
import urllib3
from datetime import datetime
import mysql.connector
from mysql.connector import Error

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

# Database Configuration
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

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
        response = requests.post(token_endpoint, data=payload, timeout=60, verify=False)
        response.raise_for_status()
        token = response.json().get('access_token')
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
        response = requests.get(OPTION_LIST_ENDPOINT, headers=headers, timeout=60, verify=False)
        response.raise_for_status()
        data = response.json()

        for item in data.get('result', []):
            if item.get('value') == model_id:
                return item
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching model info: {e}")
        return None

def get_performance_data(model_id: str, series: str) -> Optional[List[Dict[str, Any]]]:
    """Get performance data for a specific model."""
    token = get_token("TRN")
    if not token:
        return None

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    endpoint = PERFORMANCE_MATRIX_ENDPOINT.format(series=series)

    try:
        response = requests.get(endpoint, headers=headers, timeout=60, verify=False)
        response.raise_for_status()
        data = response.json()

        model_records = []
        for item in data.get('result', {}).get('details', []):
            if item.get('model') == model_id:
                model_records.append(item)

        return model_records if model_records else None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching performance data: {e}")
        return None

def get_standard_features(model_id: str, series: str) -> Optional[Dict[str, List[Dict]]]:
    """Get standard features for a specific model, organized by area."""
    token = get_token("TRN")
    if not token:
        return None

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    endpoint = STANDARDS_MATRIX_ENDPOINT.format(series=series)

    try:
        response = requests.get(endpoint, headers=headers, timeout=60, verify=False)
        response.raise_for_status()
        data = response.json()

        # Organize features by area
        features_by_area = {}
        for item in data.get('result', {}).get('details', []):
            if model_id in item and item.get(model_id) == 'S':
                area = item.get('Area', 'Other')
                if area not in features_by_area:
                    features_by_area[area] = []
                features_by_area[area].append({
                    'description': item.get('Description'),
                    'sort': item.get('Sort', 999)
                })

        # Sort features within each area
        for area in features_by_area:
            features_by_area[area] = sorted(features_by_area[area], key=lambda x: x['sort'])

        return features_by_area if features_by_area else None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching standard features: {e}")
        return None

def get_included_options(model_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get included options from BoatOptions25_test table for a specific model."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Query for accessories (ItemMasterProdCat = 'ACC') for this model
        query = """
            SELECT DISTINCT
                ItemNo,
                ItemDesc1,
                QuantitySold,
                ExtSalesAmount
            FROM BoatOptions25_test
            WHERE BoatModelNo = %s
              AND ItemMasterProdCat = 'ACC'
              AND ItemNo IS NOT NULL
              AND ItemNo != ''
            ORDER BY ItemDesc1
        """

        cursor.execute(query, (model_id,))
        options = cursor.fetchall()

        cursor.close()
        connection.close()

        return options if options else None

    except Error as e:
        print(f"❌ Error fetching included options from database: {e}")
        return None

def generate_window_sticker(model_id: str, dealer_name: str = None, output_file: str = None):
    """Generate a comprehensive window sticker."""

    # Fetch all data
    print(f"🔍 Gathering information for {model_id}...")
    model_info = get_model_info(model_id)
    if not model_info:
        print("❌ Could not fetch model information")
        return

    props = model_info.get('customProperties', {})
    series = props.get('Series', '')

    perf_data = get_performance_data(model_id, series) if series else None
    features = get_standard_features(model_id, series) if series else None
    included_options = get_included_options(model_id)

    # Build the window sticker
    sticker_lines = []

    # Header
    sticker_lines.append("═" * 100)
    sticker_lines.append("║" + " " * 98 + "║")
    sticker_lines.append("║" + "BENNINGTON MARINE".center(98) + "║")
    sticker_lines.append("║" + "MANUFACTURER'S SUGGESTED RETAIL PRICE".center(98) + "║")
    sticker_lines.append("║" + " " * 98 + "║")
    sticker_lines.append("═" * 100)

    # Model Information
    sticker_lines.append("")
    sticker_lines.append("MODEL INFORMATION")
    sticker_lines.append("─" * 100)
    sticker_lines.append(f"Model Number:          {model_info.get('value')}")
    sticker_lines.append(f"Series:                {props.get('Series')} ({props.get('ParentSeries')} Parent Series)")
    sticker_lines.append(f"Year:                  2026")
    sticker_lines.append(f"Model Description:     {props.get('Length')}' {props.get('FloorplanDesc')}")
    sticker_lines.append("")

    # Specifications
    sticker_lines.append("VESSEL SPECIFICATIONS")
    sticker_lines.append("─" * 100)
    sticker_lines.append(f"Length:                {props.get('LOAStr')} (Length Overall)")
    sticker_lines.append(f"Beam Width:            {props.get('BeamStr')}")
    sticker_lines.append(f"Floorplan:             {props.get('FloorplanDesc')} ({props.get('Floorplan')})")
    sticker_lines.append(f"Seating Capacity:      {props.get('Seats')} seats")

    # Performance specs (use first/primary package)
    if perf_data and len(perf_data) > 0:
        primary_perf = perf_data[0]
        sticker_lines.append(f"Hull Weight:           {int(primary_perf.get('HullWeight', 0)):,} lbs")
        sticker_lines.append(f"Maximum HP:            {int(primary_perf.get('MaxHP', 0))} HP")
        sticker_lines.append(f"Person Capacity:       {primary_perf.get('PersonCapacity', 'N/A')}")
        sticker_lines.append(f"Pontoon Configuration: {int(primary_perf.get('NoOfTubes', 0))} Tubes")
        sticker_lines.append(f"Pontoon Gauge:         {primary_perf.get('PontoonGauge')}\"")
        sticker_lines.append(f"Tube Height:           {primary_perf.get('TubeHeight')}")
        sticker_lines.append(f"Tube Spacing:          {primary_perf.get('TubeCentertoCenter')} (center to center)")
        sticker_lines.append(f"Maximum Width:         {primary_perf.get('MaxWidth')}")
        sticker_lines.append(f"Transom Height:        {primary_perf.get('Transom')}\"")
        sticker_lines.append(f"Fuel Capacity:         {primary_perf.get('FuelCapacity')}")

    sticker_lines.append("")

    # BASE MSRP
    msrp = props.get('Price', 0)
    sticker_lines.append("═" * 100)
    sticker_lines.append("║" + " " * 98 + "║")
    sticker_lines.append("║" + f"BASE MSRP: ${msrp:,.2f}".center(98) + "║")
    sticker_lines.append("║" + " " * 98 + "║")
    sticker_lines.append("═" * 100)
    sticker_lines.append("")

    # INCLUDED OPTIONS
    if included_options:
        sticker_lines.append("INCLUDED OPTIONS")
        sticker_lines.append("═" * 100)
        sticker_lines.append("")
        sticker_lines.append(f"{'ITEM DESCRIPTION':<50} {'ITEM #':<15} {'QTY':<8} {'MSRP':<12} {'SALE PRICE':<12}")
        sticker_lines.append("─" * 100)

        total_options_msrp = 0
        total_options_sale = 0

        for option in included_options:
            item_desc = option['ItemDesc1'][:48] if option['ItemDesc1'] else 'N/A'
            item_no = option['ItemNo'] if option['ItemNo'] else 'N/A'
            qty = option['QuantitySold'] if option['QuantitySold'] else 0
            sale_price = option['ExtSalesAmount'] if option['ExtSalesAmount'] else 0.00

            # For now, MSRP = Sale Price (can be adjusted if you have actual MSRP data)
            msrp_price = sale_price

            total_options_msrp += msrp_price
            total_options_sale += sale_price

            msrp_str = f"${msrp_price:,.2f}" if msrp_price else "N/A"
            sale_str = f"${sale_price:,.2f}" if sale_price else "N/A"

            sticker_lines.append(f"{item_desc:<50} {item_no:<15} {qty:<8} {msrp_str:<12} {sale_str:<12}")

        sticker_lines.append("─" * 100)
        sticker_lines.append(f"{'TOTAL OPTIONS':<50} {'':<15} {'':<8} ${total_options_msrp:,.2f:<11} ${total_options_sale:,.2f:<11}")
        sticker_lines.append("")
        sticker_lines.append("═" * 100)
        sticker_lines.append("")

    # STANDARD FEATURES
    sticker_lines.append("STANDARD EQUIPMENT INCLUDED IN BASE PRICE")
    sticker_lines.append("═" * 100)

    if features:
        # Console Features
        if 'Console Features' in features:
            sticker_lines.append("")
            sticker_lines.append("CONSOLE FEATURES")
            sticker_lines.append("─" * 100)
            for feature in features['Console Features']:
                sticker_lines.append(f"  ✓ {feature['description']}")

        # Interior Features
        if 'Interior Features' in features:
            sticker_lines.append("")
            sticker_lines.append("INTERIOR FEATURES")
            sticker_lines.append("─" * 100)
            for feature in features['Interior Features']:
                sticker_lines.append(f"  ✓ {feature['description']}")

        # Exterior Features
        if 'Exterior Features' in features:
            sticker_lines.append("")
            sticker_lines.append("EXTERIOR FEATURES")
            sticker_lines.append("─" * 100)
            for feature in features['Exterior Features']:
                sticker_lines.append(f"  ✓ {feature['description']}")

        # Warranty
        if 'Warranty' in features:
            sticker_lines.append("")
            sticker_lines.append("WARRANTY COVERAGE")
            sticker_lines.append("─" * 100)
            for feature in features['Warranty']:
                sticker_lines.append(f"  ✓ {feature['description']}")

        # Other categories
        for area in sorted(features.keys()):
            if area not in ['Console Features', 'Interior Features', 'Exterior Features', 'Warranty']:
                sticker_lines.append("")
                sticker_lines.append(area.upper())
                sticker_lines.append("─" * 100)
                for feature in features[area]:
                    sticker_lines.append(f"  ✓ {feature['description']}")

    # Performance packages available
    if perf_data and len(perf_data) > 1:
        sticker_lines.append("")
        sticker_lines.append("AVAILABLE PERFORMANCE PACKAGES")
        sticker_lines.append("─" * 100)
        for idx, perf in enumerate(perf_data, 1):
            pkg_name = perf.get('perfPack', 'Unknown')
            max_hp = perf.get('MaxHP', 0)
            tubes = int(perf.get('NoOfTubes', 0))
            sticker_lines.append(f"  {idx}. {pkg_name:<25} - Max {int(max_hp)} HP, {tubes} Tube Configuration")

    # Footer
    sticker_lines.append("")
    sticker_lines.append("─" * 100)
    if dealer_name:
        sticker_lines.append(f"Dealer: {dealer_name}")
    sticker_lines.append(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    sticker_lines.append("")
    sticker_lines.append("This label has been affixed in accordance with federal and state regulations.")
    sticker_lines.append("Features and specifications are subject to change without notice.")
    sticker_lines.append("═" * 100)

    # Output
    sticker_content = "\n".join(sticker_lines)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(sticker_content)
        print(f"\n✅ Window sticker saved to: {output_file}")

    print("\n" + sticker_content)

    return sticker_content

if __name__ == "__main__":
    import sys

    model_id = sys.argv[1] if len(sys.argv) > 1 else "25QXFBWA"
    dealer_name = sys.argv[2] if len(sys.argv) > 2 else "NICHOLS MARINE - CHATTANOOGA"
    output_file = sys.argv[3] if len(sys.argv) > 3 else f"window_sticker_{model_id}.txt"

    generate_window_sticker(model_id, dealer_name, output_file)
