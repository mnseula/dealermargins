#!/usr/bin/env python3
"""
Test CPQ Order → OrderLine → BoatPerformanceData template chain.

Usage:
    python3 test_order_api.py <ExternalId>
    python3 test_order_api.py 50093718527
"""
import sys
import json
import requests
import urllib3

urllib3.disable_warnings()

# ── Auth (PRD) ────────────────────────────────────────────────────────────────
CLIENT_ID     = 'QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo'
CLIENT_SECRET = '4O7OIZ64sukP1N6YeGZ6IpzsFTG4T6RFkcTZgq6ZwAetb4VoNOOJ1qMkGQAlvnOqqcgaZDlXKux6YEQNvoZQgg'
SERVICE_KEY   = 'QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9xuXKp_iYp49_M7JuB7UaEo0xjWDqTAE1Q15rQhxojw'
SERVICE_SECR  = 'IZq8wArFnHi4rESTZ-3SQT5zMgiCQfre8aLM6KirsVmvBhXmGDZS_4TXvCZlD40AjpXX6igL7y8A3svCHV-glg'
TOKEN_URL     = 'https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2'

BASE          = 'https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD'

EXTERNAL_ID   = sys.argv[1] if len(sys.argv) > 1 else '50093718527'

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_token():
    resp = requests.post(TOKEN_URL, data={
        'grant_type':    'password',
        'client_id':     CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'username':      SERVICE_KEY,
        'password':      SERVICE_SECR,
    }, verify=False, timeout=30)
    resp.raise_for_status()
    return resp.json()['access_token']


def get(session, url, params=None):
    print(f"\n  GET {url}")
    if params:
        print(f"  params: {params}")
    resp = session.get(url, params=params, timeout=30, verify=False)
    print(f"  → {resp.status_code}")
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, resp.text


def try_entity(session, service, entity, params):
    """Try an entity endpoint and return (status, data) or None if 404/403."""
    url = f"{BASE}/{service}/RuntimeApi/EnterpriseQuoting/Entities/{entity}"
    status, data = get(session, url, params)
    return status, data


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"Getting token...")
    token = get_token()
    print("Token OK")

    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
    })

    # ── STEP 1: Find Order by ExternalId ─────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"STEP 1: Query Order where ExternalId = {EXTERNAL_ID}")
    print(f"{'='*60}")

    order_id = None
    order_data = None

    # Try service prefixes and filter variants
    for service in ['CPQEQ', 'CVPO']:
        for entity in ['Order', 'Order$']:
            for filter_val in [
                f"ExternalId eq '{EXTERNAL_ID}'",
                f"ExternalId eq {EXTERNAL_ID}",
                f"ExternalId eq {EXTERNAL_ID}$",
            ]:
                status, data = try_entity(session, service, entity, {
                    '$filter': filter_val,
                    '$top': 5,
                })
                if status == 200 and isinstance(data, dict):
                    results = data.get('value') or data.get('result') or data.get('items') or []
                    if results:
                        print(f"\n✅ Found Order! service={service}, entity={entity}, filter={filter_val!r}")
                        print(json.dumps(results[0], indent=2))
                        order_id = results[0].get('ID') or results[0].get('Id') or results[0].get('id')
                        order_data = results[0]
                        break
                    else:
                        print(f"  → 200 but empty. Keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
                        print(f"  → Full response: {json.dumps(data, indent=2)[:300]}")
                elif status not in (404, 403, 401):
                    print(f"  → Unexpected: {str(data)[:200]}")
            if order_id:
                break
        if order_id:
            break

    if not order_id:
        print("\n❌ Could not find Order. Check ExternalId and service prefix.")
        print("Dumping last 200 chars of final response for debugging.")
        return

    # ── STEP 2: Get OrderLines for that Order ─────────────────────────────────
    print(f"\n{'='*60}")
    print(f"STEP 2: Query OrderLine where OrderId = {order_id}")
    print(f"{'='*60}")

    service_used = 'CPQEQ'  # use whatever worked above
    line_id = None

    for filter_val in [
        f"OrderId eq '{order_id}'",
        f"OrderId eq {order_id}",
        f"C_OrderId eq '{order_id}'",
        f"Order_ID eq '{order_id}'",
    ]:
        status, data = try_entity(session, service_used, 'OrderLine', {
            '$filter': filter_val,
            '$top': 20,
        })
        if status == 200 and isinstance(data, dict):
            results = data.get('value') or data.get('result') or data.get('items') or []
            if results:
                print(f"\n✅ Found {len(results)} OrderLine(s)!")
                for line in results:
                    print(json.dumps(line, indent=2))
                # Find the boat line — typically has a model number or type indicator
                boat_line = next(
                    (l for l in results if any(
                        str(l.get(k, '')).startswith('25') or str(l.get(k, '')).startswith('24')
                        for k in ['ItemNo', 'ProductId', 'C_ModelNo', 'Description']
                    )),
                    results[0]
                )
                line_id = (boat_line.get('ID') or boat_line.get('Id') or
                           boat_line.get('LineId') or boat_line.get('LineNumber'))
                print(f"\nUsing line: {json.dumps(boat_line, indent=2)}")
                print(f"Line ID: {line_id}")
                break
            else:
                print(f"  → 200 but empty results. Keys: {list(data.keys())}")
                print(f"  → Sample: {json.dumps(data, indent=2)[:300]}")

    if not line_id:
        print("\n❌ Could not find OrderLine.")
        return

    # ── STEP 3: Query BoatPerformanceData template ────────────────────────────
    print(f"\n{'='*60}")
    print(f"STEP 3: Query BoatPerformanceData template")
    print(f"  OrderId={order_id}  LineId={line_id}")
    print(f"{'='*60}")

    # Common template/report endpoint patterns in Infor CPQ
    template_urls = [
        f"{BASE}/{service_used}/RuntimeApi/EnterpriseQuoting/Entities/OrderLine('{line_id}')/Templates/BoatPerformanceData",
        f"{BASE}/{service_used}/RuntimeApi/EnterpriseQuoting/Entities/OrderLine('{line_id}')/Templates/BoatPerforamanceData",
        f"{BASE}/{service_used}/RuntimeApi/EnterpriseQuoting/Templates/BoatPerformanceData?orderId={order_id}&lineId={line_id}",
        f"{BASE}/{service_used}/RuntimeApi/EnterpriseQuoting/Entities/Order('{order_id}')/OrderLines('{line_id}')/Templates/BoatPerformanceData",
    ]

    for url in template_urls:
        print(f"\n  GET {url}")
        resp = session.get(url, timeout=30, verify=False)
        print(f"  → {resp.status_code}")
        if resp.status_code == 200:
            try:
                print(f"✅ SUCCESS!\n{json.dumps(resp.json(), indent=2)}")
            except Exception:
                print(f"✅ SUCCESS (non-JSON):\n{resp.text[:500]}")
            break
        else:
            print(f"  {resp.text[:200]}")


if __name__ == '__main__':
    main()
