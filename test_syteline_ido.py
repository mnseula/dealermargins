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


def try_ido_logon(oauth_token):
    """
    /ido/logon is alive (returns 401, not 500).
    Try it with Bearer token in Authorization header + config in body,
    and also with direct service credentials in the body.
    On success it should return a Mongoose session token.
    """
    print("\n--- /ido/logon attempts ---")
    url = "https://inforosmarine.polarisstage.com:7443/infor/CSI/IDORequestService/ido/logon"

    attempts = [
        # Bearer token in header, config in body
        {
            'label': 'Bearer header + config body',
            'headers': {
                'Authorization': f'Bearer {oauth_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Infor-MongooseConfig': CONFIG,
            },
            'body': {'configuration': CONFIG},
        },
        # Bearer token in header, no body
        {
            'label': 'Bearer header, no body',
            'headers': {
                'Authorization': f'Bearer {oauth_token}',
                'Accept': 'application/json',
                'X-Infor-MongooseConfig': CONFIG,
            },
            'body': None,
        },
        # Service key/secret as Mongoose credentials in body
        {
            'label': 'service credentials in body',
            'headers': {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Infor-MongooseConfig': CONFIG,
            },
            'body': {
                'configuration': CONFIG,
                'userName': SERVICE_KEY,
                'password': SERVICE_SECRET,
            },
        },
        # Bearer + service credentials in body
        {
            'label': 'Bearer header + service credentials in body',
            'headers': {
                'Authorization': f'Bearer {oauth_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-Infor-MongooseConfig': CONFIG,
            },
            'body': {
                'configuration': CONFIG,
                'userName': SERVICE_KEY,
                'password': SERVICE_SECRET,
            },
        },
    ]

    for attempt in attempts:
        kwargs = dict(headers=attempt['headers'], verify=False, timeout=30)
        if attempt['body'] is not None:
            kwargs['json'] = attempt['body']
        resp = requests.post(url, **kwargs)
        print(f"  [{attempt['label']}]: {resp.status_code} — {resp.text[:300]}")
        if resp.status_code == 200:
            data = resp.json()
            token = (data.get('SessionToken') or data.get('sessionToken')
                     or data.get('token') or data.get('access_token'))
            if token:
                print(f"    *** Got session token: {token[:60]}...")
                return token
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("Syteline IDO API Test (STG)")
    print("=" * 60)

    # Step 1: CPQ-style token — no scope, no resource (CPQ gets a JWT this way)
    print("\n--- Step 1: CPQ-style token (no scope/resource) ---")
    resp = requests.post(
        TOKEN_ENDPOINT,
        data={
            'grant_type':    'password',
            'client_id':     CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'username':      SERVICE_KEY,
            'password':      SERVICE_SECRET,
        },
        verify=False, timeout=30
    )
    print(f"  Status: {resp.status_code}")
    cpq_style_token = None
    if resp.status_code == 200:
        cpq_style_token = resp.json().get('access_token', '')
        is_jwt = cpq_style_token.startswith('eyJ')
        print(f"  Token ({len(cpq_style_token)} chars, {'JWT ✓' if is_jwt else 'opaque'}): {cpq_style_token[:80]}...")
        print("\n  Testing CPQ-style token directly against IDO...")
        query_ido(cpq_style_token, "SLCos", properties="CoNum", record_cap=1)
    else:
        print(f"  Error: {resp.text[:200]}")

    # Step 2: Fallback — token with resource param
    print("\n--- Step 2: Token with resource param (fallback) ---")
    oauth_token = get_token_with_resource()
    if not oauth_token:
        print("Failed to get OAuth token — stopping.")
        exit(1)

    # Step 2: Probe server to see what's available
    probe_server()

    # Step 3: Try Basic auth
    try_basic_auth()

    # Step 4: Check OIDC discovery — find valid scopes/grant types
    print("\n--- Step 4: OIDC discovery ---")
    discovery_url = "https://inforosmarine.polarisstage.com/InforIntSTS/.well-known/openid-configuration"
    resp = requests.get(discovery_url, verify=False, timeout=30)
    print(f"  Status: {resp.status_code}")
    if resp.status_code == 200:
        import json
        data = resp.json()
        print(f"  grant_types_supported:  {data.get('grant_types_supported')}")
        print(f"  scopes_supported:       {data.get('scopes_supported')}")
        print(f"  token_endpoint:         {data.get('token_endpoint')}")
        print(f"  introspection_endpoint: {data.get('introspection_endpoint')}")
    else:
        print(f"  Response: {resp.text[:300]}")

    # Step 5: Try scopes discovered from OIDC - especially infor-ionapi-all
    print("\n--- Step 5: Discovered scopes (looking for valid IDO token) ---")
    for scope in ['infor-ionapi-all', 'Infor-Mingle', 'Default_Scope', 'openid infor-ionapi-all', 'openid Infor-Mingle']:
        resp = requests.post(
            TOKEN_ENDPOINT,
            data={
                'grant_type': 'password',
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'username': SERVICE_KEY,
                'password': SERVICE_SECRET,
                'scope': scope,
            },
            verify=False, timeout=15
        )
        token = resp.json().get('access_token', '') if resp.status_code == 200 else ''
        is_jwt = token.startswith('eyJ') if token else False
        print(f"  scope={scope!r}: {resp.status_code}  {'JWT ✓' if is_jwt else ('opaque' if token else resp.json().get('error',''))}")
        if token:
            print(f"    Token: {token[:60]}...")
            print(f"    Testing against IDO...")
            r = query_ido(token, "SLCos", properties="CoNum", record_cap=1)
            if '"Success": true' in r.text:
                print("    *** SUCCESS! ***")
                break

    # Step 6: Introspect the token to see what it contains
    print("\n--- Step 6: Token introspection ---")
    introspect_url = "https://inforosmarine.polarisstage.com/InforIntSTS/connect/introspect"
    test_token = get_token_with_resource() or get_token()
    if test_token:
        import json
        resp = requests.post(
            introspect_url,
            data={'token': test_token},
            auth=(CLIENT_ID, CLIENT_SECRET),
            verify=False, timeout=30
        )
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"  active: {data.get('active')}")
            print(f"  sub: {data.get('sub')}")
            print(f"  scope: {data.get('scope')}")
            print(f"  client_id: {data.get('client_id')}")
            print(f"  aud: {data.get('aud')}")
            print(f"  Full response: {json.dumps(data, indent=2)}")

    # Step 7: Try different endpoint patterns for IDO
    session_token = try_ido_logon(oauth_token)
    if session_token:
        print("\n--- Step 7: Query SLCos with session token ---")
        query_ido_with_session(session_token, "SLCos", properties="CoNum", record_cap=3)

    # Step 8: If you have a Syteline app username/password, set them here and try logon
    SL_USERNAME = ""   # e.g. "svc_api" or "POLARIS\\svc_api"
    SL_PASSWORD = ""
    if SL_USERNAME and SL_PASSWORD:
        print("\n--- Step 8: Syteline app user logon ---")
        url = "https://inforosmarine.polarisstage.com:7443/infor/CSI/IDORequestService/ido/logon"
        resp = requests.post(url,
                             headers={'Accept': 'application/json', 'Content-Type': 'application/json',
                                      'X-Infor-MongooseConfig': CONFIG},
                             json={'configuration': CONFIG, 'userName': SL_USERNAME, 'password': SL_PASSWORD},
                             verify=False, timeout=30)
        print(f"  Status: {resp.status_code}  Response: {resp.text[:400]}")
