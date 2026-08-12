#!/usr/bin/env python
"""
Test script for the email automation system
"""
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from config.config import config
from utils.mailer import email_service
from utils.scheduler import email_scheduler

def test_email_system():
    """Test the email system"""
    print("=" * 60)
    print("📧 Testing Email System")
    print("=" * 60)
    
    # Test SMTP connection
    print("🔌 Testing SMTP connection...")
    connected = email_service.test_connection()
    
    if not connected:
        print(" SMTP connection failed. Check your .env file.")
        print("   Make sure SMTP_USER and SMTP_PASS are correct.")
        return False
    
    print(" SMTP connection successful!")
    print("")
    
    # Load contacts
    print(" Loading contacts...")
    email_scheduler.load_contacts()
    print(f"👥 Found {len(email_scheduler.contact_list)} contacts")
    
    # Send test email
    if email_scheduler.contact_list:
        test_contact = email_scheduler.contact_list[0]
        print("")
        print(f"📧 Sending test email to {test_contact['email']}...")
        
        try:
            result = email_service.send_email(
                to=test_contact['email'],
                subject='Test Email from VASPP Automation System',
                template='email1_announcement.html',
                context={
                    'firstName': test_contact['firstName'],
                    'lastName': test_contact['lastName'],
                    'company': test_contact.get('company', 'Test Company')
                }
            )
            
            if result['success']:
                print(f"Test email sent to {test_contact['email']}")
            else:
                print(f" Failed to send test email: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f" Failed to send test email: {e}")
    else:
        print("⚠️ No contacts found. Add contacts first.")
    
    print("")
    print("=" * 60)
    print(" Test complete!")
    print("=" * 60)
    return True

def test_templates():
    """Test all email templates"""
    print("=" * 60)
    print("📧 Testing Email Templates")
    print("=" * 60)
    
    templates = [
        'email1_announcement.html',
        'email2a_nonregistered.html',
        'email2b_registered.html',
        'email3a_nonregistered.html',
        'email3b_registered.html',
        'email4a_nonregistered.html',
        'email4b_registered.html',
        'email5_reminder.html',
        'email6_thankyou.html',
        'email7_noshow.html'
    ]
    
    context = {
        'firstName': 'Test',
        'lastName': 'User',
        'company': 'Test Corp',
        'year': 2026,
        'webinarDate': config.WEBINAR_DATE,
        'webinarTime': config.WEBINAR_TIME,
        'webinarTimezone': config.WEBINAR_TIMEZONE,
        'webinarDuration': config.WEBINAR_DURATION,
        'registerLink': config.REGISTER_LINK,
        'joinLink': config.JOIN_LINK,
        'recordingLink': config.RECORDING_LINK,
        'bookingLink': config.BOOKING_LINK
    }
    
    for template in templates:
        try:
            html = email_service.render_template(template, context)
            print(f" {template} rendered successfully")
        except Exception as e:
            print(f" Failed to render {template}: {e}")
    
    print("=" * 60)
    print(" Template test complete!")
    print("=" * 60)

def test_api():
    """Test API endpoints"""
    print("=" * 60)
    print("📧 Testing API")
    print("=" * 60)
    
    import requests
    
    base_url = f"http://localhost:{config.PORT}"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f" Health endpoint failed: {response.status_code}")
        
        # Test contacts endpoint
        response = requests.get(f"{base_url}/api/contacts")
        if response.status_code == 200:
            print("✅ Contacts endpoint working")
            data = response.json()
            print(f"   Total contacts: {data.get('total', 0)}")
        else:
            print(f" Contacts endpoint failed: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("Could not connect to server. Make sure it's running.")
        print("   Run: python server.py")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'email':
            test_email_system()
        elif command == 'templates':
            test_templates()
        elif command == 'api':
            test_api()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: email, templates, api")
    else:
        # Run all tests
        test_email_system()
        print("")
        test_templates()
        print("")
        test_api()