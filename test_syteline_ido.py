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
            'scope': 'ido',
        },
        verify=False,
        timeout=30
    )
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  Token: {data.get('access_token', '')[:50]}...")
        print(f"  Full response keys: {list(data.keys())}")
        return data.get('access_token')
    print(f"  Error: {resp.text[:500]}")
    return None


def get_token_with_resource():
    """Get token with resource parameter."""
    print(f"\nGetting token with resource parameter...")
    resp = requests.post(
        TOKEN_ENDPOINT,
        data={
            'grant_type': 'password',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'username': SERVICE_KEY,
            'password': SERVICE_SECRET,
            'resource': 'https://inforosmarine.polarisstage.com:7443',
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


def get_token_client_credentials():
    """Try client_credentials grant — may return a JWT instead of opaque token."""
    print(f"\nGetting token via client_credentials grant...")
    resp = requests.post(
        TOKEN_ENDPOINT,
        data={
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'scope': 'ido',
        },
        verify=False,
        timeout=30
    )
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        token = data.get('access_token', '')
        print(f"  Token ({len(token)} chars): {token[:60]}...")
        return token
    print(f"  Error: {resp.text[:300]}")
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


def exchange_for_session(oauth_token):
    """Exchange OAuth bearer token for a Mongoose session token."""
    session_url = "https://inforosmarine.polarisstage.com:7443/infor/CSI/IDORequestService/session"
    headers = {
        'Authorization': f'Bearer {oauth_token}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Infor-MongooseConfig': CONFIG,
    }

    # Try POST with config body (required by most Mongoose versions)
    for body in [
        {'configuration': CONFIG},
        {'configuration': CONFIG, 'culture': 'en-US'},
        {},
    ]:
        print(f"\n  POST {session_url}  body={body}")
        resp = requests.post(session_url, headers=headers, json=body, verify=False, timeout=30)
        print(f"  Status: {resp.status_code}  Response: {resp.text[:300]}")
        if resp.status_code == 200:
            data = resp.json()
            session_token = (data.get('SessionToken') or data.get('sessionToken')
                             or data.get('token') or data.get('access_token'))
            if session_token:
                print(f"  Session token: {session_token[:50]}...")
                return session_token

    # Try GET (some versions use GET to retrieve session)
    print(f"\n  GET {session_url}")
    resp = requests.get(session_url, headers=headers, verify=False, timeout=30)
    print(f"  Status: {resp.status_code}  Response: {resp.text[:300]}")
    if resp.status_code == 200:
        data = resp.json()
        return (data.get('SessionToken') or data.get('sessionToken')
                or data.get('token') or data.get('access_token'))

    # Try CreateSession path with direct credentials (no OAuth)
    print(f"\n  Trying CreateSession with direct credentials...")
    cs_url = "https://inforosmarine.polarisstage.com:7443/infor/CSI/IDORequestService/session/CreateSession"
    resp = requests.post(cs_url,
                         headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
                         json={'configuration': CONFIG, 'userName': SERVICE_KEY, 'password': SERVICE_SECRET},
                         verify=False, timeout=30)
    print(f"  Status: {resp.status_code}  Response: {resp.text[:300]}")
    if resp.status_code == 200:
        data = resp.json()
        return (data.get('SessionToken') or data.get('sessionToken')
                or data.get('token') or data.get('access_token'))

    return None


def query_ido_with_session(session_token, ido_name, properties="*", filter_clause=None, record_cap=10):
    """Query an IDO using a Mongoose session token."""
    url = f"{BASE_URL}/load/{ido_name}"
    headers = {
        'Authorization': f'Bearer {session_token}',
        'Accept': 'application/json',
        'X-Infor-MongooseConfig': CONFIG,
    }
    params = {'properties': properties, 'recordCap': record_cap}
    if filter_clause:
        params['filter'] = filter_clause

    print(f"\nQuerying IDO: {ido_name} (session token)")
    resp = requests.get(url, headers=headers, params=params, verify=False, timeout=30)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {resp.text[:1000]}")
    return resp


def probe_server():
    """Probe the server to discover what endpoints and auth methods are available."""
    base = "https://inforosmarine.polarisstage.com:7443/infor/CSI/IDORequestService"
    paths = [
        "/",
        "/ido",
        "/session",
        "/logon",
        "/api",
        "/api/ido",
        "/rest/ido",
        "/ido/load",
    ]
    print("\n--- Server probe ---")
    for path in paths:
        try:
            resp = requests.get(f"{base}{path}", verify=False, timeout=10)
            print(f"  GET {path}: {resp.status_code}  {resp.text[:120]}")
        except Exception as e:
            print(f"  GET {path}: ERROR {e}")


def try_basic_auth():
    """Try Basic auth directly with service credentials against IDO."""
    print("\n--- Basic auth attempts ---")
    url = f"{BASE_URL}/load/SLCos"
    params = {'properties': 'CoNum', 'recordCap': 1}

    for user, pwd, label in [
        (SERVICE_KEY,    SERVICE_SECRET, 'service key/secret'),
        (CLIENT_ID,      CLIENT_SECRET,  'client id/secret'),
    ]:
        headers = {'Accept': 'application/json', 'X-Infor-MongooseConfig': CONFIG}
        resp = requests.get(url, headers=headers, params=params,
                            auth=(user, pwd), verify=False, timeout=30)
        print(f"  Basic({label}): {resp.status_code} — {resp.text[:200]}")


def try_token_as_logon_body(oauth_token):
    """Try posting the token to a logon endpoint to get a session."""
    print("\n--- Token as logon body ---")
    base = "https://inforosmarine.polarisstage.com:7443/infor/CSI/IDORequestService"
    for path in ['/logon', '/session/logon', '/ido/logon']:
        for payload in [
            {'token': oauth_token},
            {'access_token': oauth_token},
            {'BearerToken': oauth_token, 'configuration': CONFIG},
        ]:
            resp = requests.post(f"{base}{path}",
                                 headers={'Accept': 'application/json',
                                          'Content-Type': 'application/json',
                                          'X-Infor-MongooseConfig': CONFIG},
                                 json=payload, verify=False, timeout=10)
            print(f"  POST {path} {list(payload.keys())}: {resp.status_code} — {resp.text[:150]}")


if __name__ == "__main__":
    print("=" * 60)
    print("Syteline IDO API Test (STG)")
    print("=" * 60)

    # Step 1: Get OAuth token
    print("\n--- Step 1: Get OAuth token ---")
    oauth_token = get_token_with_resource()
    if not oauth_token:
        print("Failed to get OAuth token — stopping.")
        exit(1)

    # Step 2: Probe server to see what's available
    probe_server()

    # Step 3: Try Basic auth
    try_basic_auth()

    # Step 4: Try posting token to logon endpoints
    try_token_as_logon_body(oauth_token)

    # Step 5: Exchange for Mongoose session token (existing flow)
    print("\n--- Step 5: Session exchange ---")
    session_token = exchange_for_session(oauth_token)
    if session_token:
        print("\n--- Step 6: Query SLCos with session token ---")
        query_ido_with_session(session_token, "SLCos", properties="CoNum", record_cap=3)
