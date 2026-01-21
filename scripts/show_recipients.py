import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
from companies.models import Vehicle
from companies.management.commands.check_document_expiry import Command

code = 'VEH-1-00001'
try:
    vehicle = Vehicle.objects.get(vehicle_code=code)
except Vehicle.DoesNotExist:
    print('Vehicle not found:', code)
    raise SystemExit(1)

cmd = Command()
recipients = cmd.get_alert_numbers(vehicle)
print('Recipients for', code, ':')
for r in recipients:
    print(' ', r)
