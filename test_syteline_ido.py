#!/usr/bin/env python3
"""
Test Syteline IDO API access (Staging environment)
"""

import requests
import urllib3
urllib3.disable_warnings()

# STG Syteline credentials
CLIENT_ID = "infor~wC_5ERtTwXb0K7AuZMjSg2OIF3Qw3RjnVF6cYi7HH0E"
CLIENT_SECRET = "6dUj3AplZmucRz5RRJRju7DA5FAhbjzVaT4vwhmfsU5Fzu1rnJh4o3Of45wGpdXG5TcA-N0vVNs2fgdUd3PT5g"
TOKEN_ENDPOINT = "https://inforosmarine.polarisstage.com/InforIntSTS/connect/token"
SERVICE_KEY = "infor#8veago_wmL7KLy4XlIfPN8rueWOu01iqV4DKrBDUj5iVw9su1o4xBnZPpEb-ojOkpOlf2Khv44af6SgLchv8Cg"
SERVICE_SECRET = "1o7YFOdbDXJmwm-50wajT7_-pIPMHJWvcRlnggrwK5fNhn8aTUwNxHuMV4J8jJ7W42sPs9-DB3ifDTQeVjC7bQ"
CONFIG = "CSISTG_BENN"
BASE_URL = "https://inforosmarine.polarisstage.com:7443/infor/CSI/IDORequestService/ido"


def get_token():
    """Get OAuth token from Syteline STS."""
    print(f"Getting token from: {TOKEN_ENDPOINT}")
    resp = requests.post(
        TOKEN_ENDPOINT,
        data={
            'grant_type': 'password',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'username': SERVICE_KEY,
            'password': SERVICE_SECRET,
        },
        verify=False,
        timeout=30
    )
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Token: {data.get('access_token', '')[:50]}...")
        return data.get('access_token')
    print(f"  Error: {resp.text[:500]}")
    return None


def get_session_token():
    """Get session token from Syteline IDO service."""
    session_url = "https://inforosmarine.polarisstage.com:7443/infor/CSI/IDORequestService/session"
    headers = {
        'Accept': 'application/json',
        'X-Infor-MongooseConfig': CONFIG,
    }
    
    # Try with basic auth using service credentials
    print(f"\nTrying session endpoint: {session_url}")
    resp = requests.post(
        session_url,
        headers=headers,
        auth=(SERVICE_KEY, SERVICE_SECRET),
        verify=False,
        timeout=30
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {resp.text[:500]}")
    
    if resp.status_code == 200:
        return resp.json().get('sessionId') or resp.json().get('token') or resp.json().get('access_token')
    return None


def get_token_via_ion_api():
    """Try ION API token endpoint on port 7443."""
    ion_token_url = "https://inforosmarine.polarisstage.com:7443/infor/CSI/IONTokenService/token"
    print(f"\nTrying ION token endpoint: {ion_token_url}")
    resp = requests.post(
        ion_token_url,
        data={
            'grant_type': 'password',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'username': SERVICE_KEY,
            'password': SERVICE_SECRET,
        },
        headers={'Accept': 'application/json'},
        verify=False,
        timeout=30
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {resp.text[:500]}")
    if resp.status_code == 200:
        return resp.json().get('access_token')
    return None


def query_ido(token, ido_name, properties="*", filter_clause=None, record_cap=10):
    """Query an IDO."""
    url = f"{BASE_URL}/load/{ido_name}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
        'X-Infor-MongooseConfig': CONFIG,
    }
    params = {
        'properties': properties,
        'recordCap': record_cap,
    }
    if filter_clause:
        params['filter'] = filter_clause
    
    print(f"\nQuerying IDO: {ido_name}")
    print(f"  URL: {url}")
    print(f"  Params: {params}")
    
    resp = requests.get(url, headers=headers, params=params, verify=False, timeout=30)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {resp.text[:1000]}")
    return resp


def create_session():
    """Create a session and get a session token."""
    session_url = "https://inforosmarine.polarisstage.com:7443/infor/CSI/IDORequestService/session/CreateSession"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    
    print(f"\nTrying to create session: {session_url}")
    resp = requests.post(
        session_url,
        headers=headers,
        json={
            'configuration': CONFIG,
            'userName': SERVICE_KEY,
            'password': SERVICE_SECRET,
        },
        verify=False,
        timeout=30
    )
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {resp.text[:500]}")
    return resp.json() if resp.status_code == 200 else None


def try_token_as_param():
    """Try passing token as query parameter instead of header."""
    print("\n--- Trying token as query param ---")
    token = get_token()
    if token:
        url = f"{BASE_URL}/load/SLCos"
        params = {
            'properties': 'CoNum',
            'recordCap': 1,
            'token': token,
        }
        headers = {
            'Accept': 'application/json',
            'X-Infor-MongooseConfig': CONFIG,
        }
        resp = requests.get(url, headers=headers, params=params, verify=False, timeout=30)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text[:500]}")
        return resp
    return None


def try_slrest_api():
    """Try SLREST endpoint instead of IDO."""
    print("\n--- Trying SLREST API ---")
    token = get_token()
    if token:
        url = "https://inforosmarine.polarisstage.com:7443/infor/CSI/SLREST/api/v1/Co"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'X-Infor-MongooseConfig': CONFIG,
        }
        params = {'$top': 1}
        resp = requests.get(url, headers=headers, params=params, verify=False, timeout=30)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text[:500]}")
        return resp
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("Syteline IDO API Test (STG)")
    print("=" * 60)
    
    # Method 1: Try creating a session first
    print("\n--- Method 1: Create session ---")
    session_data = create_session()
    
    # Method 2: Try token as query param
    print("\n--- Method 2: Token as query param ---")
    try_token_as_param()
    
    # Method 3: Try SLREST API
    print("\n--- Method 3: SLREST API ---")
    try_slrest_api()
    
    # Method 4: OAuth token with different header format
    print("\n--- Method 4: Different auth header formats ---")
    token = get_token()
    if token:
        url = f"{BASE_URL}/load/SLCos"
        params = {'properties': 'CoNum', 'recordCap': 1}
        
        # Try different header variations
        header_variations = [
            {'Authorization': token, 'Accept': 'application/json', 'X-Infor-MongooseConfig': CONFIG},
            {'X-Auth-Token': token, 'Accept': 'application/json', 'X-Infor-MongooseConfig': CONFIG},
            {'AuthToken': token, 'Accept': 'application/json', 'X-Infor-MongooseConfig': CONFIG},
        ]
        
        for i, headers in enumerate(header_variations, 1):
            print(f"\n  Header variation {i}: {list(headers.keys())}")
            resp = requests.get(url, headers=headers, params=params, verify=False, timeout=30)
            print(f"  Status: {resp.status_code}")
            print(f"  Response: {resp.text[:300]}")
