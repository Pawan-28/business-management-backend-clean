# companies/notifications.py
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
from .utils import send_sms_alert

logger = logging.getLogger(__name__)

def send_alert(vehicle, days, document_type="document", expiry_date=None):
    """
    Send alert for document expiry
    days can be positive (future), zero (today), or negative (past)
    """
    
    # Create appropriate message based on document type
    doc_names = {
        "insurance": "Vehicle Insurance",
        "pollution": "Pollution Certificate", 
        "permit": "State Permit",
        "road_tax": "Road Tax",
        "national_permit": "National Permit",
        "fc": "Fitness Certificate",
        "transit_insurance": "Transit Insurance"
    }
    
    doc_name = doc_names.get(document_type, "Document")
    
    # Prepare message based on days
    if days > 0:
        time_msg = f"in {days} days"
        urgency = "REMINDER"
        emoji = "⏰"
    elif days == 0:
        time_msg = "TODAY"
        urgency = "URGENT"
        emoji = "⚠️"
    else:
        time_msg = f"{abs(days)} days AGO"
        urgency = "EXPIRED"
        emoji = "❌"
    
    # Email subject
    if days < 0:
        subject = f"❌ EXPIRED: {doc_name} - {vehicle.vehicle_number}"
    elif days == 0:
        subject = f"⚠️ URGENT: {doc_name} Expires Today - {vehicle.vehicle_number}"
    else:
        subject = f"⏰ REMINDER: {doc_name} Expiry - {vehicle.vehicle_number}"
    
    # Detailed message
    message = f"""
    {emoji} {urgency}: {doc_name} {time_msg.upper()} {emoji}
    
    📋 Vehicle Details:
    • Name: {vehicle.vehicle_name}
    • Number: {vehicle.vehicle_number}
    • Code: {vehicle.vehicle_code}
    
    📄 Document: {doc_name}
    📅 Expiry Date: {expiry_date if expiry_date else 'N/A'}
    ⏰ Status: {'EXPIRED' if days < 0 else 'Expires ' + time_msg}
    
    💰 Penalty Risk: {'HIGH - Already expired!' if days < 0 else 'Medium - Renew soon' if days <= 3 else 'Low'}
    
    🔔 Reminder Settings:
    • 7-day reminder: {'✅ ON' if vehicle.enable_7day_reminder else '❌ OFF'}
    • 3-day reminder: {'✅ ON' if vehicle.enable_3day_reminder else '❌ OFF'}
    • Day-of reminder: {'✅ ON' if vehicle.enable_expiry_day_reminder else '❌ OFF'}
    
    ⚠️ Please renew immediately to avoid penalties and legal issues.
    
    ---
    📧 This is an automated alert from Vehicle Management System.
    """
    
    # SMS message (shorter)
    if days < 0:
        sms_message = f"❌ EXPIRED: {vehicle.vehicle_number} - {doc_name} expired {abs(days)} days ago. Renew urgently!"
    elif days == 0:
        sms_message = f"⚠️ URGENT: {vehicle.vehicle_number} - {doc_name} expires TODAY!"
    else:
        sms_message = f"⏰ REMINDER: {vehicle.vehicle_number} - {doc_name} expires in {days} days"
    
    # Log the alert
    logger.info(f"Sending {urgency} alert for {vehicle.vehicle_number} - {doc_name} (days: {days})")
    print(f"\n{emoji} SENDING {urgency} ALERT")
    print(f"Vehicle: {vehicle.vehicle_number}")
    print(f"Document: {doc_name}")
    print(f"Days: {days} ({time_msg})")
    print(f"Expiry Date: {expiry_date}")
    
    # 📧 Send EMAIL
    email_sent = False
    if vehicle.notification_emails and vehicle.notification_emails.strip():
        try:
            emails = [e.strip() for e in vehicle.notification_emails.split(';') if e.strip()]
            if emails:
                send_mail(
                    subject=subject,
                    message=message.strip(),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=emails,
                    fail_silently=False
                )
                email_sent = True
                print(f"✅ Email sent to: {', '.join(emails)}")
        except Exception as e:
            logger.error(f"Failed to send email for {vehicle.vehicle_number}: {str(e)}")
            print(f"❌ Email failed: {str(e)}")
    
    # 📱 Send SMS
    sms_sent = False
    if vehicle.notification_phone_numbers and vehicle.notification_phone_numbers.strip():
        try:
            phones = [p.strip() for p in vehicle.notification_phone_numbers.split(';') if p.strip()]
            for phone in phones:
                if send_sms_alert(phone, sms_message):
                    sms_sent = True
                    print(f"✅ SMS sent to: {phone}")
                else:
                    print(f"❌ SMS failed for: {phone}")
        except Exception as e:
            logger.error(f"Failed to send SMS for {vehicle.vehicle_number}: {str(e)}")
            print(f"❌ SMS failed: {str(e)}")
    
    print(f"{'='*50}")
    return email_sent or sms_sent

def check_all_document_expiry():
    """
    Check all documents for all vehicles and send alerts
    Now includes expired documents too!
    """
    from .models import Vehicle
    from django.utils import timezone
    
    today = timezone.now().date()
    print(f"\n📅 Running document expiry check for {today}")
    print("=" * 60)
    
    total_alerts = 0
    
    for vehicle in Vehicle.objects.filter(is_active=True):
        print(f"\nChecking Vehicle: {vehicle.vehicle_number}")
        print("-" * 40)
        
        # Check each document type
        documents_to_check = [
            ('insurance', vehicle.vehicle_insurance_expiry),
            ('pollution', vehicle.pollution_cert_expiry),
            ('national_permit', vehicle.national_permit_expiry),
            ('fc', vehicle.fc_expiry_date),
            ('transit_insurance', vehicle.transit_insurance_expiry),
        ]
        
        for doc_type, expiry_date in documents_to_check:
            if expiry_date:
                days_left = (expiry_date - today).days
                print(f"{doc_type.upper()}: {expiry_date} (Days: {days_left})")
                
                # Send alerts for:
                # 1. Standard reminders (7, 3, 0 days before)
                # 2. Expired documents (negative days)
                # 3. Near expiry (1-2 days)
                
                if days_left in [7, 3, 0, -1, -2, -3, -7]:
                    # Check if reminder is enabled for future dates
                    if days_left >= 0:
                        if (days_left == 7 and vehicle.enable_7day_reminder) or \
                           (days_left == 3 and vehicle.enable_3day_reminder) or \
                           (days_left == 0 and vehicle.enable_expiry_day_reminder):
                            
                            if send_alert(vehicle, days_left, doc_type, str(expiry_date)):
                                total_alerts += 1
                    # For expired documents (always send alert)
                    else:
                        if send_alert(vehicle, days_left, doc_type, str(expiry_date)):
                            total_alerts += 1
        
        # Check state permits (JSON field)
        if vehicle.state_permits:
            for permit in vehicle.state_permits:
                if 'expiry_date' in permit:
                    try:
                        expiry_date = timezone.datetime.strptime(permit['expiry_date'], '%Y-%m-%d').date()
                        days_left = (expiry_date - today).days
                        state = permit.get('state', 'Unknown')
                        print(f"PERMIT {state}: {expiry_date} (Days: {days_left})")
                        
                        if days_left in [7, 3, 0, -1, -2, -3, -7]:
                            if days_left >= 0:
                                if (days_left == 7 and vehicle.enable_7day_reminder) or \
                                   (days_left == 3 and vehicle.enable_3day_reminder) or \
                                   (days_left == 0 and vehicle.enable_expiry_day_reminder):
                                    
                                    if send_alert(vehicle, days_left, "permit", str(expiry_date)):
                                        total_alerts += 1
                            else:
                                if send_alert(vehicle, days_left, "permit", str(expiry_date)):
                                    total_alerts += 1
                    except ValueError:
                        continue
        
        # Check road tax (JSON field)
        if vehicle.road_tax:
            for tax in vehicle.road_tax:
                if 'expiry_date' in tax:
                    try:
                        expiry_date = timezone.datetime.strptime(tax['expiry_date'], '%Y-%m-%d').date()
                        days_left = (expiry_date - today).days
                        state = tax.get('state', 'Unknown')
                        print(f"ROAD TAX {state}: {expiry_date} (Days: {days_left})")
                        
                        if days_left in [7, 3, 0, -1, -2, -3, -7]:
                            if days_left >= 0:
                                if (days_left == 7 and vehicle.enable_7day_reminder) or \
                                   (days_left == 3 and vehicle.enable_3day_reminder) or \
                                   (days_left == 0 and vehicle.enable_expiry_day_reminder):
                                    
                                    if send_alert(vehicle, days_left, "road_tax", str(expiry_date)):
                                        total_alerts += 1
                            else:
                                if send_alert(vehicle, days_left, "road_tax", str(expiry_date)):
                                    total_alerts += 1
                    except ValueError:
                        continue
    
    print(f"\n{'='*60}")
    print(f"✅ Check completed. Total alerts sent: {total_alerts}")
    print(f"{'='*60}\n")
    
    return total_alerts

def send_daily_expiry_report():
    """
    Send daily report of all expiring/expired documents
    """
    from .models import Vehicle
    from django.utils import timezone
    from django.core.mail import send_mail
    from django.conf import settings
    
    today = timezone.now().date()
    
    expired_docs = []
    expiring_today = []
    expiring_7days = []
    
    for vehicle in Vehicle.objects.filter(is_active=True):
        # Check all documents
        docs = [
            ('Insurance', vehicle.vehicle_insurance_expiry),
            ('Pollution', vehicle.pollution_cert_expiry),
            ('National Permit', vehicle.national_permit_expiry),
        ]
        
        for doc_name, expiry_date in docs:
            if expiry_date:
                days = (expiry_date - today).days
                
                if days < 0:
                    expired_docs.append({
                        'vehicle': vehicle.vehicle_number,
                        'document': doc_name,
                        'expiry_date': expiry_date,
                        'days_overdue': abs(days)
                    })
                elif days == 0:
                    expiring_today.append({
                        'vehicle': vehicle.vehicle_number,
                        'document': doc_name,
                        'expiry_date': expiry_date
                    })
                elif days <= 7:
                    expiring_7days.append({
                        'vehicle': vehicle.vehicle_number,
                        'document': doc_name,
                        'expiry_date': expiry_date,
                        'days_left': days
                    })
    
    # Create report message
    message = f"📊 Daily Expiry Report - {today}\n\n"
    
    if expired_docs:
        message += "❌ EXPIRED DOCUMENTS:\n"
        for doc in expired_docs:
            message += f"• {doc['vehicle']} - {doc['document']} (Expired {doc['days_overdue']} days ago)\n"
        message += "\n"
    
    if expiring_today:
        message += "⚠️ EXPIRING TODAY:\n"
        for doc in expiring_today:
            message += f"• {doc['vehicle']} - {doc['document']}\n"
        message += "\n"
    
    if expiring_7days:
        message += "⏰ EXPIRING IN NEXT 7 DAYS:\n"
        for doc in expiring_7days:
            message += f"• {doc['vehicle']} - {doc['document']} ({doc['days_left']} days left)\n"
    
    if not (expired_docs or expiring_today or expiring_7days):
        message += "✅ All documents are up to date!\n"
    
    message += f"\n---\nReport generated at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Send to admin
    send_mail(
        subject=f"Daily Vehicle Document Report - {today}",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else ['admin@example.com'],
        fail_silently=False
    )
    
    print(f"📧 Daily report sent!")
    return True