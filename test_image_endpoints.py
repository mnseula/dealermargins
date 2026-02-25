#!/usr/bin/env python3
import requests
import json
import urllib3
urllib3.disable_warnings()

CLIENT_ID = 'QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo'
CLIENT_SECRET = '4O7OIZ64sukP1N6YeGZ6IpzsFTG4T6RFkcTZgq6ZwAetb4VoNOOJ1qMkGQAlvnOqqcgaZDlXKux6YEQNvoZQgg'
SERVICE_KEY = 'QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9xuXKp_iYp49_M7JuB7UaEo0xjWDqTAE1Q15rQhxojw'
SERVICE_SECRET = 'IZq8wArFnHi4rESTZ-3SQT5zMgiCQfre8aLM6KirsVmvBhXmGDZS_4TXvCZlD40AjpXX6igL7y8A3svCHV-glg'

# Get Token
payload = {'grant_type': 'password', 'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'username': SERVICE_KEY, 'password': SERVICE_SECRET}
token_resp = requests.post('https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2', data=payload, verify=False)
token = token_resp.json()['access_token']

headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

# Target info from previous inspect
image_name = "HighRes2025 25LTFB.png"
value_id = "b24a266c-b5a7-4b0d-9d95-cf7f040e7a39"

# Common ION API Media Patterns
test_urls = [
    f"https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/RuntimeApi/v1/Media/{image_name}",
    f"https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/RuntimeApi/v1/Assets/{image_name}",
    f"https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/DataImport/QA2FNBZCKUAUH7QB_PRD/v1/OptionLists/bb38d84e-6493-40c7-b282-9cb9c0df26ae/values/{value_id}/image",
]

for url in test_urls:
    print(f"Testing URL: {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=10, verify=False)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"✅ Found! Content-Type: {resp.headers.get('Content-Type')}")
            # If it's small, print a bit, if it's image, just confirm
            if 'image' in resp.headers.get('Content-Type', ''):
                print("Confirmed Image Content")
        else:
            print(f"Failed: {resp.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 40)
