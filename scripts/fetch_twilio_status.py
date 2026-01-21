#!/usr/bin/env python3
import os, sys
from pathlib import Path

# Ensure project root is on sys.path
# The Django project package `backend` lives under the top-level backend/ directory
# so add that directory to sys.path (parent of this scripts/ folder)
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
from twilio.rest import Client

if len(sys.argv) < 2:
    print('Usage: python fetch_twilio_status.py <MESSAGE_SID>')
    sys.exit(1)

sid = sys.argv[1]
print(f'Fetching Twilio message SID: {sid}')

try:
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    msg = client.messages(sid).fetch()
    print('\n=== Message Status ===')
    print('sid:', getattr(msg, 'sid', None))
    print('status:', getattr(msg, 'status', None))
    print('error_code:', getattr(msg, 'error_code', None))
    print('error_message:', getattr(msg, 'error_message', None))
    print('to:', getattr(msg, 'to', None))
    print('from:', getattr(msg, 'from_', None))
    print('date_sent:', getattr(msg, 'date_sent', None))
    print('body:', getattr(msg, 'body', None))
except Exception as e:
    print('Error fetching message:', e)
    sys.exit(2)
