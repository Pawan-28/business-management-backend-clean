# management/commands/check_document_expiry.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from companies.models import Vehicle, Company
from companies.sms_service import send_sms, format_phone_number
from datetime import timedelta
import logging
import re

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Checks for vehicle documents expiring soon and sends SMS alerts to all companies.'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='Check for specific company only',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Check without actually sending SMS',
        )
    
    def handle(self, *args, **options):
        today = timezone.now().date()
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🚧 DRY RUN MODE - No SMS will be sent"))
        
        # Get all verified active companies
        companies = Company.objects.filter(is_verified=True, is_active=True)
        
        if options['company_id']:
            companies = companies.filter(company_id=options['company_id'])
            self.stdout.write(f"🔍 Checking for company ID: {options['company_id']}")
        
        total_alerts_sent = 0
        total_companies = companies.count()
        
        self.stdout.write(f"📊 Processing {total_companies} companies...")
        
        for company in companies:
            alerts_sent = self.process_company_vehicles(company, today, dry_run)
            total_alerts_sent += alerts_sent
        
        # Summary
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"✅ Dry run completed. Would send {total_alerts_sent} alerts across {total_companies} companies."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'✅ Daily expiry check completed. Sent {total_alerts_sent} alerts across {total_companies} companies.'
            ))
    
    def process_company_vehicles(self, company, today, dry_run=False):
        """Process vehicles for a specific company"""
        alert_days = [7, 3, 0]  # 0 = expiry day
        alerts_sent = 0
        
        for days_before in alert_days:
            target_date = today + timedelta(days=days_before)
            
            # Find vehicles with documents expiring on target date
            expiring_vehicles = Vehicle.objects.filter(
                company=company,
                is_active=True
            ).filter(
                vehicle_insurance_expiry=target_date
            ) | Vehicle.objects.filter(
                company=company,
                is_active=True
            ).filter(
                pollution_cert_expiry=target_date
            ) | Vehicle.objects.filter(
                company=company,
                is_active=True
            ).filter(
                fc_expiry_date=target_date
            ) | Vehicle.objects.filter(
                company=company,
                is_active=True
            ).filter(
                transit_insurance_expiry=target_date
            )
            
            for vehicle in expiring_vehicles.distinct():
                if self.send_vehicle_alert(vehicle, days_before, target_date, dry_run):
                    alerts_sent += 1
        
        if alerts_sent > 0:
            self.stdout.write(f"  📨 {company.company_name}: Sent {alerts_sent} alerts")
        
        return alerts_sent
    
    def send_vehicle_alert(self, vehicle, days_before, target_date, dry_run=False):
        """Send alert for a specific vehicle"""
        # Check which documents are expiring
        alert_type = []
        
        if vehicle.vehicle_insurance_expiry == target_date:
            alert_type.append("Vehicle Insurance")
        if vehicle.pollution_cert_expiry == target_date:
            alert_type.append("Pollution Certificate")
        if vehicle.fc_expiry_date == target_date:
            alert_type.append("Fitness Certificate (FC)")
        if vehicle.transit_insurance_expiry == target_date:
            alert_type.append("Transit Insurance")
        
        if not alert_type:
            return False
        
        # Check if reminders are enabled for this vehicle
        if days_before == 7 and not vehicle.enable_7day_reminder:
            return False
        if days_before == 3 and not vehicle.enable_3day_reminder:
            return False
        if days_before == 0 and not vehicle.enable_expiry_day_reminder:
            return False
        
        # Get phone numbers
        phone_numbers = self.get_alert_numbers(vehicle)
        
        if not phone_numbers:
            logger.warning(f"No phone numbers found for vehicle {vehicle.vehicle_code}")
            return False
        
        # Create message
        days_text = "TODAY" if days_before == 0 else f"in {days_before} day(s)"
        
        message = (
            f"🚨 {vehicle.company.company_name} - VEHICLE ALERT\n"
            f"Vehicle: {vehicle.vehicle_name} ({vehicle.vehicle_number})\n"
            f"Code: {vehicle.vehicle_code}\n"
            f"Alert: {', '.join(alert_type)} expires {days_text}\n"
            f"Expiry Date: {target_date}\n"
            f"Please renew promptly to avoid penalties.\n"
            f"--\n"
            f"Panda Tech Labs - Auto Alert System"
        )
        
        if dry_run:
            logger.info(f"📋 [DRY RUN] Would send to {len(phone_numbers)} numbers: {phone_numbers}")
            logger.info(f"📋 [DRY RUN] Message: {message}")
            return True
        
        # Actually send SMS
        success_count = 0
        for number in phone_numbers:
            if send_sms(number, message):
                success_count += 1
                logger.info(f"✅ SMS sent to {number} for {vehicle.vehicle_code}")
            else:
                logger.error(f"❌ Failed to send SMS to {number} for {vehicle.vehicle_code}")
        
        return success_count > 0
    
    def get_alert_numbers(self, vehicle):
        """Extract and format phone numbers for alerts"""
        numbers = []
        
        # Get numbers from vehicle notification settings
        if vehicle.notification_phone_numbers:
            raw_numbers = [
                n.strip() 
                for n in vehicle.notification_phone_numbers.split(';') 
                if n.strip()
            ]
            
            for num in raw_numbers:
                formatted = format_phone_number(num)
                if formatted and formatted not in numbers:
                    numbers.append(formatted)
        
        # Add company mobile number
        if vehicle.company and vehicle.company.mobile:
            company_number = format_phone_number(vehicle.company.mobile)
            if company_number and company_number not in numbers:
                numbers.append(company_number)
        
        # Add company owner/contact number if available
        if hasattr(vehicle.company, 'alternate_mobile') and vehicle.company.alternate_mobile:
            alt_number = format_phone_number(vehicle.company.alternate_mobile)
            if alt_number and alt_number not in numbers:
                numbers.append(alt_number)
        
        return numbers