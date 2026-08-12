import smtplib
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from config.config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.template_env = Environment(
            loader=FileSystemLoader(config.TEMPLATES_DIR)
        )
        self.initialized = False
        self.server = None

    def initialize(self):
        """Initialize email service"""
        if self.initialized:
            return
        
        try:
            self.server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
            self.server.starttls()
            self.server.login(config.SMTP_USER, config.SMTP_PASS)
            self.initialized = True
            logger.info("✅ Email service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize email service: {e}")
            raise

    def render_template(self, template_name, context):
        """Render HTML template with context"""
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"❌ Failed to render template {template_name}: {e}")
            raise

    def send_email(self, to, subject, template, context, attachments=None):
        """Send a single email"""
        if not self.initialized:
            self.initialize()

        try:
            # Prepare context with default values
            default_context = {
                'year': datetime.now().year,
                'webinarDate': config.WEBINAR_DATE,
                'webinarTime': config.WEBINAR_TIME,
                'webinarTimezone': config.WEBINAR_TIMEZONE,
                'webinarDuration': config.WEBINAR_DURATION,
                'registerLink': config.REGISTER_LINK,
                'joinLink': config.JOIN_LINK,
                'recordingLink': config.RECORDING_LINK,
                'bookingLink': config.BOOKING_LINK
            }
            context.update(default_context)

            # Render HTML
            html_content = self.render_template(template, context)

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f'"{config.FROM_NAME}" <{config.FROM_EMAIL}>'
            msg['To'] = to

            # Attach HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            self.server.send_message(msg)
            
            # Log email
            self.log_email(to, subject, template)
            
            logger.info(f"✅ Email sent to {to}")
            return {
                'success': True,
                'to': to,
                'template': template,
                'subject': subject
            }

        except Exception as e:
            logger.error(f"❌ Failed to send email to {to}: {e}")
            return {
                'success': False,
                'to': to,
                'error': str(e)
            }

    def send_bulk_emails(self, emails):
        """Send multiple emails with rate limiting"""
        results = []
        for i, email_data in enumerate(emails):
            result = self.send_email(
                to=email_data['to'],
                subject=email_data['subject'],
                template=email_data['template'],
                context=email_data.get('context', {})
            )
            results.append(result)
            
            # Rate limiting - wait 1 second between emails
            if i < len(emails) - 1:
                import time
                time.sleep(1)
        
        return results

    def log_email(self, to, subject, template):
        """Log email to file"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'to': to,
            'subject': subject,
            'template': template,
            'status': 'sent'
        }

        log_path = config.LOGS_DIR / 'email-log.json'
        
        try:
            logs = []
            if log_path.exists():
                with open(log_path, 'r') as f:
                    logs = json.load(f)
            
            logs.append(log_entry)
            
            with open(log_path, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to log email: {e}")

    def test_connection(self):
        """Test SMTP connection"""
        try:
            if not self.initialized:
                self.initialize()
            return True
        except Exception as e:
            logger.error(f"❌ SMTP connection test failed: {e}")
            return False

    def close(self):
        """Close SMTP connection"""
        if self.server:
            self.server.quit()
            self.initialized = False

# Create singleton instance
email_service = EmailService()