# # companies/management/commands/test_expiry_alerts.py
# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from datetime import timedelta
# from companies.models import Vehicle
# from companies.notifications import check_all_document_expiry
# import logging

# logger = logging.getLogger(__name__)

# class Command(BaseCommand):
#     help = 'Test document expiry alerts for vehicles'
    
#     def add_arguments(self, parser):
#         parser.add_argument(
#             '--vehicle-id',
#             type=int,
#             help='Test for specific vehicle ID'
#         )
#         parser.add_argument(
#             '--days',
#             type=int,
#             default=0,
#             help='Simulate days before expiry (0=today, 3=3 days, 7=7 days)'
#         )
    
#     def handle(self, *args, **options):
#         vehicle_id = options.get('vehicle_id')
#         days_before = options.get('days')
        
#         self.stdout.write(self.style.SUCCESS(
#             f"🚀 Testing expiry alerts (days={days_before})"
#         ))
        
#         if vehicle_id:
#             # Test specific vehicle
#             try:
#                 vehicle = Vehicle.objects.get(id=vehicle_id)
#                 self.test_single_vehicle(vehicle, days_before)
#             except Vehicle.DoesNotExist:
#                 self.stdout.write(self.style.ERROR(f"Vehicle {vehicle_id} not found"))
#         else:
#             # Test all vehicles
#             check_all_document_expiry()
    
#     def test_single_vehicle(self, vehicle, days_before):
#         """Test alerts for a single vehicle"""
#         from companies.notifications import send_alert
        
#         self.stdout.write(self.style.SUCCESS(f"\nTesting Vehicle: {vehicle.vehicle_number}"))
        
#         # Test insurance alert
#         if vehicle.vehicle_insurance_expiry:
#             self.stdout.write(f"Insurance Expiry: {vehicle.vehicle_insurance_expiry}")
            
#             # Simulate sending alert
#             send_alert(vehicle, days_before, "insurance")
        
#         # Test pollution cert alert
#         if vehicle.pollution_cert_expiry:
#             self.stdout.write(f"Pollution Cert Expiry: {vehicle.pollution_cert_expiry}")
#             send_alert(vehicle, days_before, "pollution")
        
#         # Test state permits
#         if vehicle.state_permits:
#             for permit in vehicle.state_permits:
#                 self.stdout.write(f"Permit {permit.get('state')}: {permit.get('expiry_date')}")
#                 send_alert(vehicle, days_before, "permit")
        
#         self.stdout.write(self.style.SUCCESS("✅ Test completed"))