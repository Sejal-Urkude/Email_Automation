from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import json
import logging
from pathlib import Path
from config.config import config
from utils.mailer import email_service
from utils.scheduler import email_scheduler

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='public')
CORS(app)

# Ensure directories exist
config.ensure_directories()

# ==================== API ROUTES ====================

@app.route('/')
@app.route('/dashboard')
def index():
    """Serve the dashboard"""
    return send_from_directory('public', 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    is_email_connected = email_service.test_connection()
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'contacts': len(email_scheduler.contact_list),
        'webinarDate': config.WEBINAR_DATE,
        'daysUntil': email_scheduler.get_days_until_webinar(),
        'emailService': 'connected' if is_email_connected else 'disconnected',
        'version': '1.0.0'
    })

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts"""
    try:
        email_scheduler.load_contacts()
        return jsonify({
            'success': True,
            'data': email_scheduler.contact_list,
            'total': len(email_scheduler.contact_list)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contacts', methods=['POST'])
def add_contact():
    """Add a new contact"""
    try:
        data = request.json
        first_name = data.get('firstName')
        last_name = data.get('lastName', '')
        email = data.get('email')
        company = data.get('company', '')
        
        if not first_name or not email:
            return jsonify({
                'success': False,
                'error': 'firstName and email are required'
            }), 400
        
        contact = email_scheduler.add_contact({
            'firstName': first_name,
            'lastName': last_name,
            'email': email,
            'company': company
        })
        
        return jsonify({'success': True, 'data': contact})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


    

@app.route('/api/register', methods=['POST'])
def register_contact():
    """Register a contact for the webinar"""
    try:
        data = request.json
        email = data.get('email')
        first_name = data.get('firstName', 'User')
        last_name = data.get('lastName', '')
        company = data.get('company', '')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'email is required'
            }), 400
        
        contact = email_scheduler.register_contact(email, first_name, last_name, company)
        
        return jsonify({
            'success': True,
            'message': 'Registration successful!',
            'data': contact
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/attended', methods=['POST'])
def mark_attended():
    """Mark a contact as attended"""
    try:
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'email is required'
            }), 400
        
        contact = email_scheduler.mark_attended(email)
        
        if not contact:
            return jsonify({
                'success': False,
                'error': 'Contact not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Attendance marked successfully!',
            'data': contact
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/process-emails', methods=['POST'])
def process_emails():
    """Manually trigger email processing"""
    try:
        email_scheduler.process_emails()
        return jsonify({
            'success': True,
            'message': 'Email processing triggered successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    try:
        log_path = config.LOGS_DIR / "email-log.json"

        logs = []

        if log_path.exists():
            with open(log_path, "r") as f:
                logs = json.load(f)

        return jsonify({
            "success": True,
            "data": logs
        })

    except Exception as e:
        import traceback
        traceback.print_exc()   # <-- IMPORTANT
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/clear-logs', methods=['POST'])
def clear_logs():
    """Clear email logs"""
    try:
        log_path = config.LOGS_DIR / 'email-log.json'
        with open(log_path, 'w') as f:
            json.dump([], f)
        return jsonify({'success': True, 'message': 'Logs cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-email', methods=['POST'])
def test_email():
    """Send a test email"""
    try:
        data = request.json
        email = data.get('email')
        template = data.get('template', 'email1_announcement.html')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'email is required'
            }), 400
        
        result = email_service.send_email(
            to=email,
            subject='Test Email from VASPP Automation System',
            template=template,
            context={
                'firstName': 'Test',
                'lastName': 'User',
                'company': 'Test Corp'
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Test email sent successfully!',
            'data': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route("/api/stats")
def get_stats():

    email_scheduler.load_contacts()

    contacts = email_scheduler.contact_list

    total_contacts = len(contacts)

    registered = len([
        c for c in contacts
        if c.get("registered")
    ])

    attended = len([
        c for c in contacts
        if c.get("attended")
    ])

    # Read email logs
    try:
        with open(config.LOGS_DIR / "email-log.json", "r") as f:
            logs = json.load(f)
    except:
        logs = []

    emails_sent = len(logs)

    registration_rate = 0
    attendance_rate = 0

    if total_contacts > 0:
        registration_rate = round(
            registered * 100 / total_contacts,
            1
        )

    if registered > 0:
        attendance_rate = round(
            attended * 100 / registered,
            1
        )

    return jsonify({
        "success": True,
        "data": {
            "contacts": total_contacts,
            "registered": registered,
            "attended": attended,
            "emailsSent": emails_sent,
            "registrationRate": registration_rate,
            "attendanceRate": attendance_rate
        }
    })

from datetime import datetime, timedelta

@app.route("/api/next-email")
def next_email():

    webinar_date = datetime.strptime(config.WEBINAR_DATE, "%Y-%m-%d")

    days_until = (webinar_date.date() - datetime.now().date()).days

    if days_until > 28:
        email_name = "Email 1 – Announcement"
        send_date = webinar_date - timedelta(days=28)

    elif days_until > 21:
        email_name = "Email 2 – Registration Reminder"
        send_date = webinar_date - timedelta(days=21)

    elif days_until > 14:
        email_name = "Email 3 – Webinar Reminder"
        send_date = webinar_date - timedelta(days=14)

    elif days_until > 7:
        email_name = "Email 4 – Final Reminder"
        send_date = webinar_date - timedelta(days=7)

    elif days_until > 1:
        email_name = "Email 5 – Tomorrow Reminder"
        send_date = webinar_date - timedelta(days=1)

    elif days_until == 0:
        email_name = "Email 6 – Thank You"
        send_date = webinar_date

    else:
        return jsonify({
            "success": True,
            "data": {
                "email": "Campaign Finished",
                "target": None
            }
        })

    return jsonify({
        "success": True,
        "data": {
            "email": email_name,
            "target": send_date.isoformat()
        }
    })
@app.route("/api/timeline")
def campaign_timeline():

    webinar = datetime.strptime(config.WEBINAR_DATE,"%Y-%m-%d")

    today=datetime.now()
    email_scheduler.load_contacts()
    contacts = email_scheduler.contact_list

    emails = [

    {
        "title": "Email 1",
        "subtitle": "Announcement",
        "days": 28,
        "recipients": [
            c for c in contacts
            if not c.get("registered")
        ]
    },

    {
        "title": "Email 2",
        "subtitle": "Registration Reminder",
        "days": 21,
        "recipients": [
            c for c in contacts
            if c.get("registered")
            and not c.get("attended")
        ]
    },

    {
        "title": "Email 3",
        "subtitle": "Webinar Reminder",
        "days": 14,
        "recipients": [
            c for c in contacts
            if c.get("registered")
            and not c.get("attended")
        ]
    },

    {
        "title": "Email 4",
        "subtitle": "Final Reminder",
        "days": 7,
        "recipients": [
            c for c in contacts
            if c.get("registered")
            and not c.get("attended")
        ]
    },

    {
        "title": "Email 5",
        "subtitle": "Last Reminder",
        "days": 1,
        "recipients": [
            c for c in contacts
            if c.get("registered")
            and not c.get("attended")
        ]
    },

    {
        "title": "Webinar",
        "subtitle": "Live Session",
        "days": 0,
        "recipients": contacts
    }

]

    data = []

    for item in emails:

        email_date = webinar - timedelta(days=item["days"])
    
        left = max(0, (email_date - today).days)
    
        names = []
    
        for c in item["recipients"]:
            names.append(
                f'{c["firstName"]} {c.get("lastName","")}'.strip()
            )
    
        preview = names[:2]
    
        remaining = names[2:]
    
        data.append({
    "title": item["title"],
    "subtitle": item["subtitle"],
    "date": email_date.strftime("%d %b %Y"),
    "daysLeft": left,
    "recipientCount": len(names),
    "previewRecipients": preview,
    "remainingRecipients": remaining
})

    return jsonify({

        "success":True,

        "data":data

    })
# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ==================== START SERVER ====================

if __name__ == '__main__':
    try:
        # Initialize email service
        email_service.initialize()
        
        # Start scheduler
        email_scheduler.start()
        
        # Run Flask app
        logger.info("=" * 60)
        logger.info("🚀 Webinar Email Automation System (Python)")
        logger.info("=" * 60)
        logger.info(f"📡 Server: http://localhost:{config.PORT}")
        logger.info(f"📊 Dashboard: http://localhost:{config.PORT}/dashboard")
        logger.info(f"🔄 Health: http://localhost:{config.PORT}/health")
        logger.info("=" * 60)
        logger.info("✅ System is ready!")
        logger.info("=" * 60)
        
        app.run(host='0.0.0.0', port=config.PORT, debug=True, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down...")
        email_scheduler.stop()
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")