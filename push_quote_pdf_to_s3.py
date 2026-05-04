#!/usr/bin/env python3
"""
push_quote_pdf_to_s3.py

Fetches a QuoteDocument PDF from Infor EQ (TRN), uploads it to S3,
and writes the resulting S3 URL to a file drop for the CRM.

Usage:
    python3 push_quote_pdf_to_s3.py --quote-guid <guid> --quote-number <number>

Example:
    python3 push_quote_pdf_to_s3.py \
        --quote-guid 09ea026d-623e-4844-9667-b3380157f8bb \
        --quote-number SQAVK000003
"""

import argparse
import base64
import sys
import os
from datetime import datetime, timezone

import boto3
import requests

sys.path.insert(0, os.path.dirname(__file__))
from load_cpq_data import get_token

# ── Configuration (fill in before use) ───────────────────────────────────────
S3_BUCKET      = 'YOUR_BUCKET_NAME'          # e.g. 'bennington-crm-leads'
S3_PREFIX      = 'quotes'                    # folder inside the bucket
CRM_DROP_FILE  = '/path/to/crm_drop.csv'     # file drop path for CRM

EQ_BASE = (
    'https://mingle-ionapi.inforcloudsuite.com'
    '/QA2FNBZCKUAUH7QB_TRN'
    '/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities'
)
# ─────────────────────────────────────────────────────────────────────────────


def fetch_quote_document(token: str, quote_guid: str) -> dict:
    """Return the first QuoteDocument record for the given Quote GUID."""
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.get(
        f'{EQ_BASE}/QuoteDocument',
        headers=headers,
        params={'$filter': f"Quote eq '{quote_guid}'"},
        timeout=30
    )
    r.raise_for_status()
    items = r.json().get('items', [])
    if not items:
        raise ValueError(f'No QuoteDocument found for Quote GUID {quote_guid}')
    return items[0]


def download_pdf(token: str, doc_id: str) -> bytes:
    """Download PDF bytes for a QuoteDocument by its Id."""
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    r = requests.post(
        f'{EQ_BASE}/QuoteDocument({doc_id})/Download',
        headers=headers,
        json={},
        timeout=60
    )
    r.raise_for_status()
    b64 = r.json().get('data', '')
    if not b64:
        raise ValueError(f'Download returned no data for QuoteDocument {doc_id}')
    return base64.b64decode(b64)


def upload_to_s3(pdf_bytes: bytes, quote_number: str, filename: str) -> str:
    """Upload PDF bytes to S3 and return the public URL."""
    s3 = boto3.client('s3')
    key = f'{S3_PREFIX}/{quote_number}/{filename}'
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=pdf_bytes,
        ContentType='application/pdf',
    )
    url = f'https://{S3_BUCKET}.s3.amazonaws.com/{key}'
    return url


def write_crm_drop(quote_number: str, quote_guid: str, s3_url: str,
                   doc: dict) -> None:
    """Append a row to the CRM file drop CSV."""
    created = doc.get('CreateDate', '')
    description = doc.get('Description', '')
    filename = doc.get('FileName', '')
    timestamp = datetime.now(timezone.utc).isoformat()

    write_header = not os.path.exists(CRM_DROP_FILE)
    with open(CRM_DROP_FILE, 'a') as f:
        if write_header:
            f.write('quote_number,quote_guid,description,filename,s3_url,eq_create_date,pushed_at\n')
        f.write(f'{quote_number},{quote_guid},{description},{filename},{s3_url},{created},{timestamp}\n')


def main():
    parser = argparse.ArgumentParser(description='Push EQ quote PDF to S3 and notify CRM')
    parser.add_argument('--quote-guid',   required=True, help='EQ Quote GUID')
    parser.add_argument('--quote-number', required=True, help='EQ Quote number (e.g. SQAVK000003)')
    args = parser.parse_args()

    print(f'Quote GUID:   {args.quote_guid}')
    print(f'Quote number: {args.quote_number}')

    print('\n[1/4] Authenticating with EQ...')
    token = get_token('TRN')

    print('[2/4] Fetching QuoteDocument record...')
    doc = fetch_quote_document(token, args.quote_guid)
    print(f'      Id:       {doc["Id"]}')
    print(f'      FileName: {doc["FileName"]}')
    print(f'      FileSize: {doc["FileSize"]:,} bytes')

    print('[3/4] Downloading PDF...')
    pdf_bytes = download_pdf(token, doc['Id'])
    print(f'      Downloaded {len(pdf_bytes):,} bytes')

    print('[4/4] Uploading to S3...')
    s3_url = upload_to_s3(pdf_bytes, args.quote_number, doc['FileName'])
    print(f'      S3 URL: {s3_url}')

    write_crm_drop(args.quote_number, args.quote_guid, s3_url, doc)
    print(f'\nDone. URL written to {CRM_DROP_FILE}')


if __name__ == '__main__':
    main()
