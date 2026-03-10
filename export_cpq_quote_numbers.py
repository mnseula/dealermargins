#!/usr/bin/env python3
"""
Export CPQ Order Number → CPQ Quote Number mapping to CSV.

Fetches all Orders from CPQ EQ (PRD), follows OrderedFromQuote GUID to
the source Quote entity, and outputs a two-column CSV:
    CPQ_Order_Number, CPQ_Quote_Number

Usage:
    python3 export_cpq_quote_numbers.py [output.csv]
    (default output file: cpq_order_quote_numbers.csv)
"""
import csv
import sys
import time
import requests
import urllib3

urllib3.disable_warnings()

# ── Auth (PRD) ─────────────────────────────────────────────────────────────────
CLIENT_ID     = 'QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo'
CLIENT_SECRET = '4O7OIZ64sukP1N6YeGZ6IpzsFTG4T6RFkcTZgq6ZwAetb4VoNOOJ1qMkGQAlvnOqqcgaZDlXKux6YEQNvoZQgg'
SERVICE_KEY   = 'QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9xuXKp_iYp49_M7JuB7UaEo0xjWDqTAE1Q15rQhxojw'
SERVICE_SECR  = 'IZq8wArFnHi4rESTZ-3SQT5zMgiCQfre8aLM6KirsVmvBhXmGDZS_4TXvCZlD40AjpXX6igL7y8A3svCHV-glg'
TOKEN_URL     = 'https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2'

BASE          = 'https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD'
EQ_BASE       = f'{BASE}/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities'

PAGE_SIZE     = 100   # orders per page
QUOTE_CACHE   = {}    # GUID → QuoteNumberString (avoid duplicate lookups)


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


def fetch_all_orders(session):
    """Paginate through all Order entities, return list of dicts."""
    orders = []
    skip = 0
    while True:
        resp = session.get(f'{EQ_BASE}/Order', params={
            '$filter':  "OrderNumberString gt ''",
            '$top':     PAGE_SIZE,
            '$skip':    skip,
        }, verify=False, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        page = data.get('items', data.get('value', []))
        if not page:
            break
        orders.extend(page)
        total = data.get('totalItems', '?')
        print(f'  Fetched {len(orders)}/{total} orders...', end='\r')
        if len(page) < PAGE_SIZE:
            break
        skip += PAGE_SIZE
        time.sleep(0.1)   # be polite to the API
    print()
    return orders


def get_quote_number(session, quote_guid):
    """Fetch QuoteNumberString for a given Quote GUID. Returns '' if not found."""
    if quote_guid in QUOTE_CACHE:
        return QUOTE_CACHE[quote_guid]

    resp = session.get(f'{EQ_BASE}/Quote', params={
        '$filter': f"ID eq '{quote_guid}'",
        '$top':    1,
    }, verify=False, timeout=30)

    quote_number = ''
    if resp.status_code == 200:
        records = resp.json().get('items', resp.json().get('value', []))
        if records:
            quote_number = records[0].get('QuoteNumberString', '')

    QUOTE_CACHE[quote_guid] = quote_number
    return quote_number


def main():
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'cpq_order_quote_numbers.csv'

    print('Authenticating with CPQ PRD...')
    token = get_token()
    print('Token OK')

    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json',
    })

    print('\nFetching all CPQ Orders...')
    orders = fetch_all_orders(session)
    print(f'Total orders fetched: {len(orders)}')

    rows = []
    missing_quote = 0

    print('\nResolving Quote Numbers...')
    for i, order in enumerate(orders, 1):
        cpq_order_num = order.get('OrderNumberString', '')
        quote_guid    = order.get('OrderedFromQuote', '')

        if not cpq_order_num:
            continue

        cpq_quote_num = ''
        if quote_guid:
            cpq_quote_num = get_quote_number(session, quote_guid)
            if not cpq_quote_num:
                missing_quote += 1
        else:
            missing_quote += 1

        rows.append({
            'CPQ_Order_Number': cpq_order_num,
            'CPQ_Quote_Number': cpq_quote_num,
        })

        if i % 25 == 0 or i == len(orders):
            print(f'  Processed {i}/{len(orders)} orders...', end='\r')

    print()

    # Write CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['CPQ_Order_Number', 'CPQ_Quote_Number'])
        writer.writeheader()
        writer.writerows(rows)

    print(f'\nDone.')
    print(f'  Rows written:       {len(rows)}')
    print(f'  Orders with quote:  {len(rows) - missing_quote}')
    print(f'  Orders without:     {missing_quote}')
    print(f'  Output file:        {output_file}')


if __name__ == '__main__':
    main()
