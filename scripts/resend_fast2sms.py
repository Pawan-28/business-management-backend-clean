#!/usr/bin/env python3
import os, sys
from pathlib import Path

# Make project importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
try:
    django.setup()
except Exception as e:
    print('Failed to setup Django:', e)
    sys.exit(1)

from django.conf import settings
import requests

if len(sys.argv) < 3:
    print('Usage: python resend_fast2sms.py <MOBILE_WITHOUT_COUNTRY> <MESSAGE_TEXT>')
    sys.exit(1)

mobile = sys.argv[1]
message = sys.argv[2]

api_key = getattr(settings, 'FAST2SMS_API_KEY', None)
if not api_key:
    print('No FAST2SMS_API_KEY found in settings. Aborting.')
    sys.exit(1)

# New Fast2SMS DLT-style endpoint & JSON body (as per updated docs)
url = 'https://www.fast2sms.com/dev/bulkV2'

# Build JSON body using DLT-style fields shown by user
payload = {
    "route": "dlt",
    "sender_id": "",        # optional: your registered sender ID
    "message": message,
    "variables_values": "", # optional if using templates
    "schedule_time": None,
    "flash": 0,
    "numbers": f"91{mobile}"
}

headers = {
    'authorization': api_key,
    'Content-Type': 'application/json'
}

print(f"Sending Fast2SMS (DLT format) to 91{mobile}...\nMessage: {message}\nAPI Key present: {'Yes' if api_key else 'No'}")

try:
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    print('Status code:', resp.status_code)
    # Try to print JSON (most modern Fast2SMS endpoints return JSON)
    try:
        print('Response JSON:', resp.json())
    except Exception:
        print('Response text:', resp.text)
    # Provide hint if provider says old API
    if resp.status_code == 400 and 'old api' in (resp.text or '').lower():
        print('\nFast2SMS indicates old API usage — check docs.fast2sms.com for the correct endpoint and required fields (sender_id, template registration for DLT).')
except Exception as e:
    print('Request failed:', e)
    sys.exit(2)

# If Fast2SMS DLT failed or indicated invalid sender, try legacy endpoint (form-data)
print('\nTrying legacy Fast2SMS endpoint (form-data) as fallback...')
legacy_url = 'https://www.fast2sms.com/dev/bulk'
legacy_payload = {
    'route': 'v3',
    'message': message,
    'numbers': f'91{mobile}',
    'sender_id': ''
}
try:
    resp2 = requests.post(legacy_url, data=legacy_payload, headers={'authorization': api_key}, timeout=30)
    print('Legacy endpoint status:', resp2.status_code)
    try:
        print('Legacy response JSON:', resp2.json())
    except Exception:
        print('Legacy response text:', resp2.text)
except Exception as e:
    print('Legacy endpoint request failed:', e)

# Try TextLocal if configured
textlocal_api = getattr(settings, 'TEXTLOCAL_API_KEY', None)
textlocal_sender = getattr(settings, 'TEXTLOCAL_SENDER_ID', None)
if textlocal_api:
    print('\nTrying TextLocal as secondary provider...')
    tl_url = 'https://api.textlocal.in/send/'
    tl_params = {
        'apikey': textlocal_api,
        'numbers': f'91{mobile}',
        'message': message,
        'sender': textlocal_sender or 'TXTLCL'
    }
    try:
        resp3 = requests.post(tl_url, data=tl_params, timeout=30)
        print('TextLocal status:', resp3.status_code)
        try:
            print('TextLocal response JSON:', resp3.json())
        except Exception:
            print('TextLocal response text:', resp3.text)
    except Exception as e:
        print('TextLocal request failed:', e)
else:
    print('\nTextLocal API key not configured in settings; skipping TextLocal.')
