import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from companies.models import Company, Vehicle

pattern = '9711168942'

print('Searching for numbers containing:', pattern)

companies = Company.objects.filter(mobile__contains=pattern)
print('\nCompanies with mobile containing pattern:')
for c in companies:
    print(f"company_id={c.company_id}, company_name={c.company_name}, mobile={c.mobile}, alternate_mobile={c.alternate_mobile}")

vehicles = Vehicle.objects.filter(notification_phone_numbers__contains=pattern)
print('\nVehicles with notification_phone_numbers containing pattern:')
for v in vehicles:
    print(f"vehicle_code={v.vehicle_code}, notification_phone_numbers={v.notification_phone_numbers}")

# Also search for numbers starting variants
from django.db.models import Q
q = Q(mobile__contains=pattern) | Q(alternate_mobile__contains=pattern) | Q(notification_phone_numbers__contains=pattern)

print('\nAny matches across companies and vehicles:')
for c in Company.objects.filter(Q(mobile__contains=pattern) | Q(alternate_mobile__contains=pattern)):
    print('Company:', c.company_id, c.company_name, c.mobile, c.alternate_mobile)
for v in Vehicle.objects.filter(Q(notification_phone_numbers__contains=pattern)):
    print('Vehicle:', v.vehicle_code, v.notification_phone_numbers)
