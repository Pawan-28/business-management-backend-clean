# run_auto_schedule.py
import schedule
import time
import os
import sys
from datetime import datetime
import subprocess

def run_check():
    """Run the expiry check command"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Running check...")
    
    # Change to project directory
    os.chdir(r"P:\business-management-system\backend")
    
    # Run the command
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'check_daily_expiry', '--report'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Check completed")
            print(result.stdout[-500:])  # Print last 500 chars
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error in check")
            print(result.stderr)
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Exception: {e}")

def main():
    print("=" * 60)
    print("🚀 VEHICLE DOCUMENT AUTO-CHECK SCHEDULER")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Scheduled: Daily at 09:00")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    # Schedule daily at 9 AM
    schedule.every().day.at("09:00").do(run_check)
    
    # For testing: Run every 5 minutes
    schedule.every(5).minutes.do(run_check)
    
    # Run immediately once
    run_check()
    
    # Keep checking schedule
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 System stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")