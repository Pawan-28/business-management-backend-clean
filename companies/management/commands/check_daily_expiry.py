# # companies/management/commands/check_daily_expiry.py
# from django.core.management.base import BaseCommand
# from companies.notifications import check_all_document_expiry, send_daily_expiry_report
# import logging

# logger = logging.getLogger(__name__)

# class Command(BaseCommand):
#     help = 'Daily check for document expiry - Run this via cron job'
    
#     def add_arguments(self, parser):
#         parser.add_argument(
#             '--report',
#             action='store_true',
#             help='Send daily summary report email'
#         )
#         parser.add_argument(
#             '--only-report',
#             action='store_true',
#             help='Only send report without individual alerts'
#         )
    
#     def handle(self, *args, **options):
#         self.stdout.write(self.style.SUCCESS(
#             "=" * 60
#         ))
#         self.stdout.write(self.style.SUCCESS(
#             "🚀 DAILY VEHICLE DOCUMENT EXPIRY CHECK"
#         ))
#         self.stdout.write(self.style.SUCCESS(
#             "=" * 60
#         ))
        
#         send_report = options.get('report')
#         only_report = options.get('only_report')
        
#         # Log start
#         logger.info("Starting daily document expiry check")
        
#         if not only_report:
#             # Check and send alerts
#             total_alerts = check_all_document_expiry()
#             self.stdout.write(self.style.SUCCESS(
#                 f"✅ Alerts sent: {total_alerts}"
#             ))
#         else:
#             self.stdout.write(self.style.WARNING(
#                 "📊 Sending report only (no individual alerts)"
#             ))
        
#         if send_report or only_report:
#             # Send daily summary report
#             try:
#                 send_daily_expiry_report()
#                 self.stdout.write(self.style.SUCCESS(
#                     "📧 Daily report email sent"
#                 ))
#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(
#                     f"❌ Failed to send report: {str(e)}"
#                 ))
        
#         self.stdout.write(self.style.SUCCESS(
#             "=" * 60
#         ))
#         self.stdout.write(self.style.SUCCESS(
#             "✅ Daily check completed successfully"
#         ))
#         self.stdout.write(self.style.SUCCESS(
#             "=" * 60
#         ))
        
#         logger.info("Daily document expiry check completed")