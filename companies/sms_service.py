# companies/sms_service.py
from twilio.rest import Client
from django.conf import settings
import logging
import re

logger = logging.getLogger(__name__)


def format_phone_number(number):
    """Format a phone number into E.164 for India (best-effort).

    Examples:
      9711168942 -> +919711168942
      919711168942 -> +919711168942
      09711168942 -> +919711168942
    """
    if not number:
        return None

    s = str(number).strip()

    # If already starts with + and looks valid, return as-is
    if s.startswith('+'):
        return s

    # remove non-digits
    cleaned = re.sub(r"\D", "", s)
    if not cleaned:
        return None

    # 10-digit local -> assume India
    if len(cleaned) == 10:
        return f"+91{cleaned}"

    # already has country code without +
    if len(cleaned) == 12 and cleaned.startswith('91'):
        return f"+{cleaned}"

    # leading 0 (011...) -> drop 0 and add +91
    if len(cleaned) == 11 and cleaned.startswith('0'):
        return f"+91{cleaned[1:]}"

    # fallback: prefix +
    return f"+{cleaned}"


def send_sms(to_number, message_body):
    """Sends an SMS using Twilio. Returns True on success."""
    formatted = format_phone_number(to_number)
    if not formatted:
        logger.error(f"❌ Invalid phone number: {to_number}")
        return False

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        logger.info(f"📱 Sending SMS to {to_number} -> {formatted}")
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=formatted
        )

        sid = getattr(message, 'sid', None)
        status = getattr(message, 'status', None)
        error_code = getattr(message, 'error_code', None)
        error_message = getattr(message, 'error_message', None)

        logger.info(f"✅ SMS queued/created. to={formatted} sid={sid} status={status} error_code={error_code} error_message={error_message}")
        # also print to stdout for immediate visibility when running management commands
        print(f"SMS -> to={formatted} sid={sid} status={status} error_code={error_code} error_message={error_message}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to send SMS to {formatted}: {e}")
        return False