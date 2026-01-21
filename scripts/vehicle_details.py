import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
from companies.models import Vehicle

code = 'VEH-1-00001'
try:
    v = Vehicle.objects.get(vehicle_code=code)
except Vehicle.DoesNotExist:
    print('Vehicle not found:', code)
    raise SystemExit(1)

print('Vehicle:', v.vehicle_code, v.vehicle_name, v.vehicle_number)
print('Company:', v.company.company_id, v.company.company_name)
print('Notification numbers:', v.notification_phone_numbers)
print('Company mobile:', v.company.mobile, 'alternate:', getattr(v.company, 'alternate_mobile', None))
print('FC expiry:', v.fc_expiry_date)
print('Transit insurance expiry:', v.transit_insurance_expiry)
print('Vehicle insurance expiry:', v.vehicle_insurance_expiry)
print('Pollution cert expiry:', v.pollution_cert_expiry)
print('Reminders enabled - 7day:', v.enable_7day_reminder, '3day:', v.enable_3day_reminder, 'expiry_day:', v.enable_expiry_day_reminder)
