
const emailService = require('./mailer');
const scheduler = require('./scheduler');

async function testEmail() {
  console.log('=' .repeat(60));
  console.log('📧 Testing Email System');
  console.log('=' .repeat(60));
  
  const connected = await emailService.testConnection();
  
  if (!connected) {
    console.log('❌ SMTP connection failed. Check your .env file.');
    process.exit(1);
  }
  
  console.log('✅ SMTP connection successful!');
  console.log('');
  
  await scheduler.loadContacts();
  console.log(`👥 Found ${scheduler.contactList.length} contacts`);
  
  if (scheduler.contactList.length > 0) {
    const testContact = scheduler.contactList[0];
    console.log(`📧 Sending test email to ${testContact.email}...`);
    
    try {
      const result = await emailService.sendEmail({
        to: testContact.email,
        subject: 'Test Email from VASPP Automation System',
        template: 'email1-announcement',
        context: {
          firstName: testContact.firstName,
          lastName: testContact.lastName,
          company: testContact.company || 'Test Company'
        }
      });
      
      if (result.success) {
        console.log(`✅ Test email sent to ${testContact.email}`);
        console.log(`📧 Message ID: ${result.messageId}`);
      }
    } catch (error) {
      console.error(`❌ Failed to send test email: ${error.message}`);
    }
  }
  
  console.log('');
  console.log('=' .repeat(60));
  console.log('✅ Test complete!');
  console.log('=' .repeat(60));
}

testEmail();
