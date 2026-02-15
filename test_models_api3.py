#!/usr/bin/env python3
import requests
import json
import urllib3
urllib3.disable_warnings()

CLIENT_ID = 'QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo'
CLIENT_SECRET = '4O7OIZ64sukP1N6YeGZ6IpzsFTG4T6RFkcTZgq6ZwAetb4VoNOOJ1qMkGQAlvnOqqcgaZDlXKux6YEQNvoZQgg'
SERVICE_KEY = 'QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9xuXKp_iYp49_M7JuB7UaEo0xjWDqTAE1Q15rQhxojw'
SERVICE_SECRET = 'IZq8wArFnHi4rESTZ-3SQT5zMgiCQfre8aLM6KirsVmvBhXmGDZS_4TXvCZlD40AjpXX6igL7y8A3svCHV-glg'

payload = {'grant_type': 'password', 'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'username': SERVICE_KEY, 'password': SERVICE_SECRET}
token_resp = requests.post('https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2', data=payload, verify=False)
token = token_resp.json()['access_token']

headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
data_resp = requests.get('https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/DataImport/QA2FNBZCKUAUH7QB_PRD/v1/OptionLists/bb38d84e-6493-40c7-b282-9cb9c0df26ae/values', headers=headers, timeout=30, verify=False)
data = data_resp.json()

print(json.dumps(data, indent=2)[:2000])
