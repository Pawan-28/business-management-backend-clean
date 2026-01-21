# management/commands/test_sms.py
from django.core.management.base import BaseCommand
from companies.sms_service import send_sms, format_phone_number

class Command(BaseCommand):
    help = 'Test SMS functionality with Twilio'
    
    def add_arguments(self, parser):
        parser.add_argument('number', type=str, help='Phone number to test')
        parser.add_argument('--message', type=str, default='Test SMS from Panda Tech Labs Vehicle Management System', help='Message to send')
        parser.add_argument('--format-only', action='store_true', help='Only format, dont send')
    
    def handle(self, *args, **options):
        number = options['number']
        message = options['message']
        format_only = options['format_only']
        
        # Test formatting
        formatted = format_phone_number(number)
        self.stdout.write(f"📱 Phone Number Test:")
        self.stdout.write(f"   Original:  {number}")
        self.stdout.write(f"   Formatted: {formatted}")
        
        if format_only:
            self.stdout.write(self.style.SUCCESS("✅ Formatting test complete"))
            return
        
        # Test sending
        self.stdout.write(f"\n✉️  Sending SMS Test:")
        self.stdout.write(f"   To:       {formatted}")
        self.stdout.write(f"   Message:  '{message}'")
        self.stdout.write(f"   Length:   {len(message)} characters")
        
        self.stdout.write("\n⏳ Sending...")
        success = send_sms(number, message)
        
        if success:
            self.stdout.write(self.style.SUCCESS('✅ SMS sent successfully!'))
        else:
            self.stdout.write(self.style.ERROR('❌ Failed to send SMS'))