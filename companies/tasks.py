# # tasks.py (if using Celery)
# from celery import shared_task
# from companies.notifications import check_all_document_expiry

# @shared_task
# def check_document_expiry_task():
#     """Daily task to check document expiry"""
#     return check_all_document_expiry()

# # Celery beat schedule
# # CELERY_BEAT_SCHEDULE = {
# #     'check-document-expiry-daily': {
# #         'task': 'companies.tasks.check_document_expiry_task',
# #         'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
# #     },
# # }


# # companies/tasks.py
# # from background_task import background
# from background_task.models import Task
# from django.utils import timezone
# from datetime import timedelta
# import logging
# from .notifications import check_all_document_expiry, send_daily_expiry_report

# logger = logging.getLogger(__name__)

# @background(schedule=60*60*24)  # Run daily (24 hours)
# def daily_expiry_check_task():
#     """
#     Background task to check document expiry daily
#     """
#     logger.info("Starting background expiry check task")
    
#     try:
#         # Check and send alerts
#         total_alerts = check_all_document_expiry()
#         logger.info(f"Background task: Sent {total_alerts} alerts")
        
#         # Send daily report at 9 AM
#         now = timezone.now()
#         if now.hour == 9:  # Only at 9 AM
#             send_daily_expiry_report()
#             logger.info("Background task: Daily report sent")
            
#     except Exception as e:
#         logger.error(f"Background task failed: {str(e)}")
    
#     # Schedule next run
#     daily_expiry_check_task(schedule=60*60*24)  # Schedule next day

# @background(schedule=60)  # Run every minute (for testing)
# def test_expiry_check_task():
#     """
#     Test task - runs every minute
#     """
#     logger.info("Test task running...")
#     check_all_document_expiry()

# def setup_daily_tasks():
#     """
#     Setup initial scheduled tasks
#     Call this from apps.py or management command
#     """
#     # Clear existing tasks
#     Task.objects.filter(task_name='companies.tasks.daily_expiry_check_task').delete()
    
#     # Schedule daily task at 9 AM
#     from datetime import datetime, time
#     # import pytz
    
#     # Calculate next 9 AM
#     now = timezone.now()
#     today_9am = timezone.make_aware(
#         datetime.combine(now.date(), time(9, 0))
#     )
    
#     if now > today_9am:
#         today_9am += timedelta(days=1)
    
#     schedule_time = today_9am
    
#     # Schedule the task
#     daily_expiry_check_task(schedule=schedule_time)
#     logger.info(f"Scheduled daily expiry check at {schedule_time}")
    
#     return True