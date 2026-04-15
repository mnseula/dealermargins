#!/usr/bin/env python3
"""
Fetch and store Liquifire image URL for a single CPQ boat.
Usage: python3 backfill_one_boat_image.py <SO_NUMBER> <HIN>
Example: python3 backfill_one_boat_image.py SO00936163 ETWS1404B626
"""

import sys
import requests
import urllib3
import mysql.connector

urllib3.disable_warnings()

import load_cpq_data
import build_liquifire_url as blf

MYSQL_CONFIG = {
    'host':     'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port':     3306,
    'user':     'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
}

EQ_BASE = ('https://mingle-ionapi.inforcloudsuite.com'
           '/QA2FNBZCKUAUH7QB_PRD/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities')

def get_token():
    resp = requests.post(load_cpq_data.TOKEN_ENDPOINT_PRD, data={
        'grant_type':    'password',
        'client_id':     load_cpq_data.CLIENT_ID_PRD,
        'client_secret': load_cpq_data.CLIENT_SECRET_PRD,
        'username':      load_cpq_data.SERVICE_KEY_PRD,
        'password':      load_cpq_data.SERVICE_SECRET_PRD,
    }, verify=False, timeout=30)
    resp.raise_for_status()
    return resp.json()['access_token']


def fetch_image_url(so_number, headers):
    r = requests.get(f"{EQ_BASE}/Order",
                     params={'$filter': f"ExternalId eq '{so_number}'", '$top': 1},
                     headers=headers, verify=False, timeout=30)
    r.raise_for_status()
    items = r.json().get('items', [])
    if not items:
        print(f"  Order not found in PRD: {so_number}")
        return None

    order_id = items[0]['Id']
    print(f"  Order GUID: {order_id}")

    r2 = requests.get(f"{EQ_BASE}/OrderLine",
                      params={'$filter': f"Order eq '{order_id}'", '$top': 50},
                      headers=headers, verify=False, timeout=30)
    r2.raise_for_status()

    for line in r2.json().get('items', []):
        url = line.get('LastConfigurationImageLink')
        if url:
            if 'liquifire.com' not in url:
                print(f"  CPQ returned non-Liquifire URL ({url[:60]}...) — will build from config instead")
                return None
            url = url.replace('view[side]', 'view[orthographic]')
            return url

    print(f"  No LastConfigurationImageLink found on any order line")
    return None


def update_snm(hin, image_url):
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    updated = 0
    for db in ('warrantyparts', 'warrantyparts_test'):
        cursor.execute(
            f"UPDATE {db}.SerialNumberMaster SET LiquifireImageUrl = %s WHERE Boat_SerialNo = %s",
            (image_url, hin)
        )
        rows = cursor.rowcount
        conn.commit()
        print(f"  {db}: updated {rows} row(s)")
        updated += rows
    cursor.close()
    conn.close()
    return updated


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 backfill_one_boat_image.py <SO_NUMBER> <HIN>")
        print("Example: python3 backfill_one_boat_image.py SO00936163 ETWS1404B626")
        sys.exit(1)

    so_number = sys.argv[1]
    hin       = sys.argv[2]

    print(f"Backfilling image URL for {hin} / {so_number}")

    print("Authenticating with CPQ PRD...")
    token   = get_token()
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    print("  Token OK")

    print(f"Fetching image URL from CPQ PRD...")
    image_url = fetch_image_url(so_number, headers)

    if not image_url:
        print("Falling back to Liquifire URL builder from CPQ config...")
        trn_token = blf.get_trn_token()
        matrices  = blf.load_matrices(trn_token)
        conn      = mysql.connector.connect(**MYSQL_CONFIG)
        cur       = conn.cursor()
        cur.execute("USE warrantyparts")
        config, model, series = blf.get_boat_config(cur, hin)
        cur.close()
        conn.close()
        if not model:
            print(f"  No model found in BoatOptions26 for {hin} — nothing updated.")
            sys.exit(1)
        image_url, size = blf.build_and_test_url(hin, config, model, series, matrices)
        if not image_url:
            print(f"  Could not build a rendering Liquifire URL for {hin} — nothing updated.")
            sys.exit(1)
        print(f"  Built URL OK ({size:,} bytes)")

    print(f"  Image URL: {image_url[:80]}...")

    print(f"Updating SerialNumberMaster for {hin}...")
    total = update_snm(hin, image_url)

    if total:
        print(f"\nDone — {total} row(s) updated.")
    else:
        print(f"\nWarning: {hin} not found in SerialNumberMaster in either database.")


if __name__ == '__main__':
    main()
