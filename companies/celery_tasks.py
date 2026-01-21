# companies/celery_tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
from .notifications import check_all_document_expiry, send_daily_expiry_report

logger = get_task_logger(__name__)

@shared_task
def daily_expiry_check():
    """
    Daily task to check document expiry at 9 AM
    """
    logger.info("Starting Celery daily expiry check")
    
    try:
        # Check and send alerts
        total_alerts = check_all_document_expiry()
        logger.info(f"Celery task: Sent {total_alerts} alerts")
        
        # Send daily report
        send_daily_expiry_report()
        logger.info("Celery task: Daily report sent")
        
        return f"Success: {total_alerts} alerts sent"
        
    except Exception as e:
        logger.error(f"Celery task failed: {str(e)}")
        return f"Error: {str(e)}"

@shared_task
def hourly_expiry_check():
    """
    Hourly check (for testing)
    """
    logger.info("Starting hourly expiry check")
    total_alerts = check_all_document_expiry()
    return f"Hourly check: {total_alerts} alerts"

@shared_task
def test_expiry_check():
    """
    Test task - runs immediately
    """
    logger.info("Test task running...")
    return check_all_document_expiry()