#!/usr/bin/env python3
"""
lambda_push_quote_pdf.py

AWS Lambda function — triggered via API Gateway.
Fetches a QuoteDocument PDF from Infor EQ, stores it in S3 (audit trail),
generates a pre-signed URL, then POSTs a lead to the Polaris CRM
Campaign Responses API.

Expected event payload (POST body from boss's EQ piece):
{
    "quote_guid":    "09ea026d-623e-4844-9667-b3380157f8bb",
    "quote_number":  "SQAVK000003",
    "first_name":    "Jane",
    "last_name":     "Doe",
    "email":         "jane.doe@example.com",
    "phone":         "5551234567",        // optional, 10 digits no dashes
    "phone_type":    "Mobile",            // Home | Mobile | Business
    "address1":      "123 Main St",       // optional
    "city":          "Indianapolis",      // optional
    "state":         "IN",               // optional, 2-char
    "postal_code":   "46201",            // optional
    "country_code":  "US",              // US or CA
    "dealer_number": "559236",           // no leading zeros per CRM spec
    "note":          "Customer comments" // optional, max 200 chars
}
"""

import base64
import json
import os
import uuid
from datetime import datetime, timezone, timedelta

import boto3
import requests

# ── Configuration — fill in / move to environment variables ──────────────────
EQ_CLIENT_ID      = os.environ.get('EQ_CLIENT_ID',      'QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8')
EQ_CLIENT_SECRET  = os.environ.get('EQ_CLIENT_SECRET',  'CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAnyArDH3ZebqYTKAoMq37_aQ')
EQ_SERVICE_KEY    = os.environ.get('EQ_SERVICE_KEY',    'QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw')
EQ_SERVICE_SECRET = os.environ.get('EQ_SERVICE_SECRET', 'pAze3yNlj8r6dbcTv-Fn8AiGvhIcs2x-yEgJaMiuoraAJdkFB6iLQFKaFQCP_17KZIYoroUoF_CeEoslHWlXug')
EQ_TOKEN_URL      = 'https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2'
EQ_BASE           = 'https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities'

S3_BUCKET         = os.environ.get('S3_BUCKET',         'YOUR_BUCKET_NAME')
S3_PREFIX         = os.environ.get('S3_PREFIX',         'quotes')
S3_URL_EXPIRY     = int(os.environ.get('S3_URL_EXPIRY', 604800))   # 7 days

CRM_API_URL       = os.environ.get('CRM_API_URL',       'https://polarisapim.azure-api.net/api/CRM/campaignmanagement/v1/CampaignResponses')
CRM_SUBSCRIPTION_KEY = os.environ.get('CRM_SUBSCRIPTION_KEY', 'YOUR_SUBSCRIPTION_KEY')
CRM_CAMPAIGN_KEY  = os.environ.get('CRM_CAMPAIGN_KEY',  'YOUR_CAMPAIGN_KEY')
# ─────────────────────────────────────────────────────────────────────────────


def get_eq_token() -> str:
    r = requests.post(EQ_TOKEN_URL, data={
        'grant_type':    'password',
        'client_id':     EQ_CLIENT_ID,
        'client_secret': EQ_CLIENT_SECRET,
        'username':      EQ_SERVICE_KEY,
        'password':      EQ_SERVICE_SECRET,
    }, timeout=30)
    r.raise_for_status()
    return r.json()['access_token']


def fetch_quote(token: str, quote_guid: str) -> dict:
    r = requests.get(
        f'{EQ_BASE}/Quote({quote_guid})',
        headers={'Authorization': f'Bearer {token}'},
        timeout=30
    )
    r.raise_for_status()
    return r.json()


def fetch_quote_document(token: str, quote_guid: str) -> dict:
    r = requests.get(
        f'{EQ_BASE}/QuoteDocument',
        headers={'Authorization': f'Bearer {token}'},
        params={'$filter': f"Quote eq '{quote_guid}'"},
        timeout=30
    )
    r.raise_for_status()
    items = r.json().get('items', [])
    if not items:
        raise ValueError(f'No QuoteDocument found for Quote GUID {quote_guid}')
    return items[0]


def download_pdf(token: str, doc_id: str) -> bytes:
    r = requests.post(
        f'{EQ_BASE}/QuoteDocument({doc_id})/Download',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={},
        timeout=60
    )
    r.raise_for_status()
    b64 = r.json().get('data', '')
    if not b64:
        raise ValueError(f'Download returned no data for QuoteDocument {doc_id}')
    return base64.b64decode(b64)


def upload_to_s3(pdf_bytes: bytes, quote_number: str, filename: str) -> tuple[str, str]:
    """Upload to S3, return (s3_key, presigned_url)."""
    s3 = boto3.client('s3')
    key = f'{S3_PREFIX}/{quote_number}/{filename}'
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=pdf_bytes,
        ContentType='application/pdf',
    )
    presigned_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': key},
        ExpiresIn=S3_URL_EXPIRY
    )
    return key, presigned_url


def post_to_crm(event: dict, quote: dict, quote_number: str, presigned_url: str) -> dict:
    """Build and POST the CRM Campaign Response payload."""
    now = datetime.now(timezone.utc).isoformat()
    boat_model  = quote.get('C_BoatModel', '')
    total_price = quote.get('TotalPrice', 0.0)

    payload = {
        "CampaignResponses": {
            "CampaignResponse": {
                "MessageData": {
                    "LeadType":     "Consumer",
                    "CampaignKey":  CRM_CAMPAIGN_KEY,
                    "CultureCode":  "en-US",
                    "Customer": {
                        "FirstName":               event.get('first_name', ''),
                        "LastName":                event.get('last_name', ''),
                        "EmailSubscriptionStatus": "Opt In",
                        "Email":                   event.get('email', ''),
                        "PostalAddress": {
                            "AddressLine1": event.get('address1', ''),
                            "CityName":     event.get('city', ''),
                            "StateOrProvince": event.get('state', ''),
                            "PostalCode":   event.get('postal_code', ''),
                            "CountryCode":  event.get('country_code', 'US'),
                        },
                        "PurchaseTimeFrame": "Less than 3 months",
                        "PhoneNumber": {
                            "Type":  event.get('phone_type', 'Mobile'),
                            "Value": event.get('phone', ''),
                        }
                    },
                    "Opportunity": {
                        "DealerNumber":        event.get('dealer_number', ''),
                        "ActivityResponseDate": now,
                        "BuildAndQuoteURL":    presigned_url,
                        "BuildNumber":         quote_number,
                        "Note":                event.get('note', '')[:200],
                        "Products": {
                            "Product": [
                                {
                                    "ProductNumber": boat_model,
                                    "Quantity":      "1",
                                    "Price":         round(total_price, 2),
                                }
                            ]
                        }
                    }
                }
            }
        }
    }

    r = requests.post(
        CRM_API_URL,
        headers={
            'Ocp-Apim-Subscription-Key': CRM_SUBSCRIPTION_KEY,
            'Accept':                    'application/json',
            'Content-Type':              'application/json',
            'X-Polaris-CreationDateTime': now,
            'X-Polaris-CultureCode':     'en-US',
            'X-Polaris-BODID':           str(uuid.uuid4()),
        },
        json=payload,
        timeout=30
    )

    return {'status_code': r.status_code, 'body': r.text}


def handler(event, context):
    """Lambda entry point."""
    # API Gateway passes body as a string
    if isinstance(event.get('body'), str):
        event = {**event, **json.loads(event['body'])}

    required = ('quote_guid', 'quote_number', 'first_name', 'last_name')
    missing = [f for f in required if not event.get(f)]
    if missing:
        return {'statusCode': 400, 'body': json.dumps({'error': f'Missing required fields: {missing}'})}

    quote_guid   = event['quote_guid']
    quote_number = event['quote_number']

    try:
        token = get_eq_token()

        quote = fetch_quote(token, quote_guid)
        doc   = fetch_quote_document(token, quote_guid)

        pdf_bytes = download_pdf(token, doc['Id'])

        s3_key, presigned_url = upload_to_s3(pdf_bytes, quote_number, doc['FileName'])

        crm_response = post_to_crm(event, quote, quote_number, presigned_url)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'quote_number':  quote_number,
                'pdf_filename':  doc['FileName'],
                'pdf_size':      len(pdf_bytes),
                's3_key':        s3_key,
                'crm_status':    crm_response['status_code'],
                'crm_response':  crm_response['body'],
            })
        }

    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


# ── Local CLI for testing outside Lambda ─────────────────────────────────────
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--quote-guid',    required=True)
    parser.add_argument('--quote-number',  required=True)
    parser.add_argument('--first-name',    required=True)
    parser.add_argument('--last-name',     required=True)
    parser.add_argument('--email',         default='')
    parser.add_argument('--phone',         default='')
    parser.add_argument('--dealer-number', default='')
    parser.add_argument('--note',          default='')
    args = parser.parse_args()

    result = handler({
        'quote_guid':    args.quote_guid,
        'quote_number':  args.quote_number,
        'first_name':    args.first_name,
        'last_name':     args.last_name,
        'email':         args.email,
        'phone':         args.phone,
        'dealer_number': args.dealer_number,
        'note':          args.note,
    }, None)
    print(json.dumps(json.loads(result['body']), indent=2))
