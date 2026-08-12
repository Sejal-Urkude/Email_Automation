import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config.config import config
from utils.mailer import email_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailScheduler:
    def __init__(self):
        self.contact_list = []
        self.webinar_date = datetime.strptime(config.WEBINAR_DATE, '%Y-%m-%d')
        self.sent_emails = set()
        self.scheduler = BackgroundScheduler()
        self.is_running = False

    def load_contacts(self):
        """Load contacts from JSON file"""
        contacts_path = config.DATA_DIR / 'contacts.json'
        
        try:
            if contacts_path.exists():
                with open(contacts_path, 'r') as f:
                    self.contact_list = json.load(f)
                logger.info(f"📋 Loaded {len(self.contact_list)} contacts")
            else:
                logger.warning("⚠️ No contacts file found. Creating sample data...")
                self.contact_list = self.get_sample_contacts()
                self.save_contacts()
                logger.info(f"✅ Created sample contacts file with {len(self.contact_list)} contacts")
        except Exception as e:
            logger.error(f"❌ Failed to load contacts: {e}")
        
        return self.contact_list

    def get_sample_contacts(self):
        """Generate sample contacts for testing"""
        return [
            {
                'id': 1,
                'firstName': 'John',
                'lastName': 'Doe',
                'email': 'test1@example.com',
                'company': 'ABC Corp',
                'registered': False,
                'attended': False,
                'createdAt': datetime.now().isoformat()
            },
            {
                'id': 2,
                'firstName': 'Jane',
                'lastName': 'Smith',
                'email': 'test2@example.com',
                'company': 'XYZ Ltd',
                'registered': False,
                'attended': False,
                'createdAt': datetime.now().isoformat()
            },
            {
                'id': 3,
                'firstName': 'Michael',
                'lastName': 'Johnson',
                'email': 'test3@example.com',
                'company': 'Global Foods',
                'registered': False,
                'attended': False,
                'createdAt': datetime.now().isoformat()
            }
        ]

    def save_contacts(self):
        """Save contacts to JSON file"""
        contacts_path = config.DATA_DIR / 'contacts.json'
        try:
            with open(contacts_path, 'w') as f:
                json.dump(self.contact_list, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Failed to save contacts: {e}")

    def get_days_until_webinar(self):
        """Calculate days until webinar"""
        now = datetime.now()
        diff = self.webinar_date - now
        return diff.days

    def get_hours_until_webinar(self):
        """Calculate hours until webinar"""
        now = datetime.now()
        diff = self.webinar_date - now
        return diff.total_seconds() / 3600

    def should_send_email(self, email_type, contact):
        """Determine if an email should be sent"""
        days_until = self.get_days_until_webinar()
        key = f"{contact['email']}-{email_type}"
        
        if key in self.sent_emails:
            return False

        email_schedule = {
            'email1': (28, 14),   # 4 weeks before
            'email2': (14, 7),    # 2 weeks before
            'email3': (7, 1),     # 1 week before
            'email4': (1, 1),     # 1 day before
            'email5': (0, 0),     # 1 hour before (handled separately)
            'email6': (-1, -1),   # Post-event
            'email7': (-2, -2)    # No-show follow-up
        }

        if email_type in email_schedule:
            min_days, max_days = email_schedule[email_type]
            
            if email_type == 'email5':
                # 1 hour before
                hours_until = self.get_hours_until_webinar()
                return hours_until <= 1 and hours_until > 0 and contact.get('registered', False)
            
            if email_type == 'email6':
                # Post-event thank you
                return days_until < 0 and contact.get('attended', False)
            
            if email_type == 'email7':
                # No-show follow-up
                return days_until < -1 and contact.get('registered', False) and not contact.get('attended', False)
            
            return min_days <= days_until <= max_days

        return False

    def determine_emails_to_send(self):
        """Determine which emails should be sent"""
        self.load_contacts()
        emails_to_send = []
        now = datetime.now()
        current_hour = now.hour
        
        # Only send between 9 AM and 6 PM
        if current_hour < 9 or current_hour > 18:
            return emails_to_send

        days_until = self.get_days_until_webinar()

        for contact in self.contact_list:
            key = contact['email']
            
            # Email 1: Announcement (4 weeks before)
            if self.should_send_email('email1', contact):
                emails_to_send.append({
                    'to': contact['email'],
                    'subject': 'Did You Know a 1% Improvement in Forecast Accuracy Is Worth $3.5 Million?',
                    'template': 'email1_announcement.html',
                    'context': {
                        'firstName': contact['firstName'],
                        'lastName': contact['lastName'],
                        'company': contact['company'],
                        'registered': contact.get('registered', False)
                    },
                    'contact': contact,
                    'email_type': 'email1'
                })
                self.sent_emails.add(f"{contact['email']}-email1")

            # Email 2: Speaker spotlight (2 weeks before)
            if self.should_send_email('email2', contact):
                if contact.get('registered', False):
                    emails_to_send.append({
                        'to': contact['email'],
                        'subject': f"A Preview of What We'll Cover",
                        'template': 'email2b_registered.html',
                        'context': {
                            'firstName': contact['firstName'],
                            'lastName': contact['lastName'],
                            'company': contact['company'],
                            'registered': True
                        },
                        'contact': contact,
                        'email_type': 'email2b'
                    })
                else:
                    emails_to_send.append({
                        'to': contact['email'],
                        'subject': "A 5% Error at Brand Level Becomes 30% at SKU Level",
                        'template': 'email2a_nonregistered.html',
                        'context': {
                            'firstName': contact['firstName'],
                            'lastName': contact['lastName'],
                            'company': contact['company'],
                            'registered': False
                        },
                        'contact': contact,
                        'email_type': 'email2a'
                    })
                self.sent_emails.add(f"{contact['email']}-email2")

            # Email 3: Final push (1 week before)
            if self.should_send_email('email3', contact):
                if contact.get('registered', False):
                    emails_to_send.append({
                        'to': contact['email'],
                        'subject': "One Week to Go — Here's a Question We'll Be Exploring",
                        'template': 'email3b_registered.html',
                        'context': {
                            'firstName': contact['firstName'],
                            'lastName': contact['lastName'],
                            'company': contact['company'],
                            'registered': True
                        },
                        'contact': contact,
                        'email_type': 'email3b'
                    })
                else:
                    emails_to_send.append({
                        'to': contact['email'],
                        'subject': 'Over 60% of Manufacturers Say Bad Forecasts Drive 15%+ Excess Inventory',
                        'template': 'email3a_nonregistered.html',
                        'context': {
                            'firstName': contact['firstName'],
                            'lastName': contact['lastName'],
                            'company': contact['company'],
                            'registered': False
                        },
                        'contact': contact,
                        'email_type': 'email3a'
                    })
                self.sent_emails.add(f"{contact['email']}-email3")

            # Email 4: Day before
            if self.should_send_email('email4', contact):
                if contact.get('registered', False):
                    emails_to_send.append({
                        'to': contact['email'],
                        'subject': f"Webinar Tomorrow - Your Webinar Link",
                        'template': 'email4b_registered.html',
                        'context': {
                            'firstName': contact['firstName'],
                            'lastName': contact['lastName'],
                            'company': contact['company'],
                            'registered': True
                        },
                        'contact': contact,
                        'email_type': 'email4b'
                    })
                else:
                    emails_to_send.append({
                        'to': contact['email'],
                        'subject': 'Tomorrow is the Last Chance to Join',
                        'template': 'email4a_nonregistered.html',
                        'context': {
                            'firstName': contact['firstName'],
                            'lastName': contact['lastName'],
                            'company': contact['company'],
                            'registered': False
                        },
                        'contact': contact,
                        'email_type': 'email4a'
                    })
                self.sent_emails.add(f"{contact['email']}-email4")

            # Email 5: 1 hour before (only for registered)
            if self.should_send_email('email5', contact):
                emails_to_send.append({
                    'to': contact['email'],
                    'subject': f"Starting in 1 Hour — Demand Forecasting in CPG",
                    'template': 'email5_reminder.html',
                    'context': {
                        'firstName': contact['firstName'],
                        'lastName': contact['lastName'],
                        'company': contact['company'],
                        'registered': True
                    },
                    'contact': contact,
                    'email_type': 'email5'
                })
                self.sent_emails.add(f"{contact['email']}-email5")

            # Email 6: Post-event thank you (attendees only)
            if self.should_send_email('email6', contact):
                emails_to_send.append({
                    'to': contact['email'],
                    'subject': 'Thank You — Recording and Next Steps',
                    'template': 'email6_thankyou.html',
                    'context': {
                        'firstName': contact['firstName'],
                        'lastName': contact['lastName'],
                        'company': contact['company'],
                        'registered': True,
                        'attended': True
                    },
                    'contact': contact,
                    'email_type': 'email6'
                })
                self.sent_emails.add(f"{contact['email']}-email6")

            # Email 7: No-show follow-up
            if self.should_send_email('email7', contact):
                emails_to_send.append({
                    'to': contact['email'],
                    'subject': 'You Missed It — But the Recording Is Ready',
                    'template': 'email7_noshow.html',
                    'context': {
                        'firstName': contact['firstName'],
                        'lastName': contact['lastName'],
                        'company': contact['company'],
                        'registered': True,
                        'attended': False
                    },
                    'contact': contact,
                    'email_type': 'email7'
                })
                self.sent_emails.add(f"{contact['email']}-email7")

        return emails_to_send

    def process_emails(self):
        """Process all pending emails"""
        if self.is_running:
            logger.info("⏳ Scheduler already running...")
            return

        self.is_running = True
        logger.info("📧 Checking for scheduled emails...")

        try:
            emails_to_send = self.determine_emails_to_send()
            
            if not emails_to_send:
                logger.info("✅ No emails to send at this time")
                self.is_running = False
                return

            logger.info(f"📧 Found {len(emails_to_send)} emails to send")

            # Send emails in batches
            batch_size = 5
            for i in range(0, len(emails_to_send), batch_size):
                batch = emails_to_send[i:i+batch_size]
                results = email_service.send_bulk_emails(batch)
                
                for result in results:
                    if result['success']:
                        logger.info(f"✅ Sent email to {result['to']}")
                    else:
                        logger.error(f"❌ Failed to send to {result['to']}: {result.get('error', 'Unknown error')}")

            logger.info(f"✅ Completed processing {len(emails_to_send)} emails")
        except Exception as e:
            logger.error(f"❌ Error processing emails: {e}")
        finally:
            self.is_running = False

    def add_contact(self, contact_data):
        """Add a new contact"""
        self.load_contacts()
        new_contact = {
            'id': len(self.contact_list) + 1,
            **contact_data,
            'registered': False,
            'attended': False,
            'createdAt': datetime.now().isoformat()
        }
        self.contact_list.append(new_contact)
        self.save_contacts()
        return new_contact

    def register_contact(self, email, first_name=None, last_name=None, company=None):
        """Register a contact for the webinar"""
        self.load_contacts()
        contact = next((c for c in self.contact_list if c['email'] == email), None)
        
        if contact:
            contact['registered'] = True
            contact['registeredDate'] = datetime.now().isoformat()
        else:
            contact = {
                'id': len(self.contact_list) + 1,
                'firstName': first_name or 'User',
                'lastName': last_name or '',
                'email': email,
                'company': company or '',
                'registered': True,
                'registeredDate': datetime.now().isoformat(),
                'attended': False,
                'createdAt': datetime.now().isoformat()
            }
            self.contact_list.append(contact)
        
        self.save_contacts()
        return contact

    def mark_attended(self, email):
        """Mark a contact as attended"""
        self.load_contacts()
        contact = next((c for c in self.contact_list if c['email'] == email), None)
        
        if contact:
            contact['attended'] = True
            contact['attendedDate'] = datetime.now().isoformat()
            self.save_contacts()
            return contact
        
        return None

    def start(self):
        """Start the scheduler"""
        logger.info("🚀 Email Scheduler Started")
        logger.info(f"📅 Webinar Date: {self.webinar_date.strftime('%Y-%m-%d')}")
        logger.info(f"📊 Days Until Webinar: {self.get_days_until_webinar()} days")
        
        self.load_contacts()
        logger.info(f"👥 Contacts Loaded: {len(self.contact_list)}")

        # Schedule to run every 30 seconds for testing
        # Change to 15 minutes for production
        self.scheduler.add_job(
            self.process_emails,
            trigger=IntervalTrigger(seconds=30),
            id='email_processor',
            replace_existing=True
        )
        
        self.scheduler.start()
        
        # Run once immediately
        self.process_emails()

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        email_service.close()
        logger.info("🛑 Scheduler stopped")

# Create singleton instance
email_scheduler = EmailScheduler()