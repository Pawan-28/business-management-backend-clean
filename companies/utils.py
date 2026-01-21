import requests
from django.conf import settings

def send_fast2sms_otp(mobile, otp):
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "route": "4",  # OTP route
        "variables_values": str(otp),
        "numbers": f"91{mobile}"  # India country code
    }
    headers = {
        "authorization": settings.FAST2SMS_API_KEY,
        "Content-Type": "application/json"
    }
    
    print(f"📱 Sending OTP to: 91{mobile}")
    print(f"🔢 OTP: {otp}")
    print(f"🔑 API Key present: {'Yes' if settings.FAST2SMS_API_KEY else 'No'}")
    print(f"🔑 API Key length: {len(settings.FAST2SMS_API_KEY) if settings.FAST2SMS_API_KEY else 0}")
    print(f"📦 Payload: {payload}")
    print(f"📋 Headers: {headers}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"📡 Response Status Code: {response.status_code}")
        print(f"📡 Response Text: {response.text}")
        
        response_json = response.json()
        print(f"📊 Response JSON: {response_json}")
        
        # Check Fast2SMS specific response
        if response_json.get('return'):
            print(f"✅ Fast2SMS Response: {response_json}")
            if response_json.get('message'):
                print(f"📝 Message: {response_json['message']}")
            if response_json.get('request_id'):
                print(f"🆔 Request ID: {response_json['request_id']}")
        else:
            print(f"❌ Fast2SMS Error: {response_json}")
            
        return response_json
        
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        return {"error": str(e)}



# companies/utils.py
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_sms_alert(phone_number, message):
    """
    Send SMS alert using third-party SMS service
    Replace with your actual SMS provider integration
    """
    try:
        # Remove any spaces or special characters
        phone_number = phone_number.strip()
        
        # Example using Twilio (you need to install: pip install twilio)
        if hasattr(settings, 'USE_TWILIO') and settings.USE_TWILIO:
            from twilio.rest import Client
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            message = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            logger.info(f"SMS sent to {phone_number}: {message.sid}")
            return True
            
        # Example using TextLocal (Indian provider)
        elif hasattr(settings, 'USE_TEXTLOCAL') and settings.USE_TEXTLOCAL:
            url = "https://api.textlocal.in/send/"
            
            params = {
                'apikey': settings.TEXTLOCAL_API_KEY,
                'numbers': phone_number,
                'sender': settings.TEXTLOCAL_SENDER_ID,
                'message': message
            }
            
            response = requests.post(url, data=params)
            logger.info(f"TextLocal SMS response: {response.json()}")
            return response.status_code == 200
            
        # For testing - print to console
        else:
            print(f"\n📱 SMS ALERT (TEST MODE)")
            print(f"To: {phone_number}")
            print(f"Message: {message}")
            print("-" * 50)
            
            # Also log to file
            logger.info(f"SMS Alert (Test Mode) - To: {phone_number}, Message: {message}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
        return False



from twilio.rest import Client
from django.conf import settings
import random

def send_twilio_otp(mobile):
    otp = str(random.randint(100000, 999999))

    client = Client(
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN
    )

    message = client.messages.create(
        body=f"Your OTP is {otp}",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=f"+91{mobile}"   # India number
    )

    print("✅ Twilio OTP Sent")
    print("📱 To:", mobile)
    print("🔢 OTP:", otp)
    print("🆔 Message SID:", message.sid)

    return otp

