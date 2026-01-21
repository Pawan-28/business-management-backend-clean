import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from companies.models import Company

TARGET = '9711168942'

qs = Company.objects.filter(alternate_mobile__contains=TARGET)
if not qs.exists():
    print('No companies found with alternate_mobile containing', TARGET)
else:
    for c in qs:
        print(f'Updating Company {c.company_id} {c.company_name}: alternate_mobile {c.alternate_mobile} -> ""')
        c.alternate_mobile = ''
        c.save()
    print('Update complete.')
